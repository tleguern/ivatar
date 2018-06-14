'''
Our models for ivatar.ivataraccount
'''

import base64
import hashlib
import time
from io import BytesIO
from os import urandom
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
from urllib.parse import urlsplit, urlunsplit

from PIL import Image
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import models
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from openid.association import Association as OIDAssociation
from openid.store import nonce as oidnonce
from openid.store.interface import OpenIDStore
from ipware import get_client_ip

from ivatar.settings import MAX_LENGTH_EMAIL, logger
from ivatar.settings import MAX_PIXELS, AVATAR_MAX_SIZE, JPEG_QUALITY
from .gravatar import get_photo as get_gravatar_photo


MAX_LENGTH_URL = 255  # MySQL can't handle more than that (LP 1018682)


def file_format(image_type):
    '''
    Helper method returning a 3 character long image type
    '''
    if image_type == 'JPEG':
        return 'jpg'
    elif image_type == 'PNG':
        return 'png'
    elif image_type == 'GIF':
        return 'gif'

def pil_format(image_type):
    '''
    Helper method returning the 'encoder name' for PIL
    '''
    if image_type == 'jpg':
        return 'JPEG'
    elif image_type == 'png':
        return 'PNG'
    elif image_type == 'gif':
        return 'GIF'

    logger.info('Unsupported file format: %s' % image_type)
    return None


class BaseAccountModel(models.Model):
    '''
    Base, abstract model, holding fields we use in all cases
    '''
    user = models.ForeignKey(
        User,
        on_delete=models.deletion.CASCADE,
    )
    ip_address = models.GenericIPAddressField(unpack_ipv4=True, null=True)
    add_date = models.DateTimeField(default=timezone.now)

    class Meta:
        '''
        Class attributes
        '''
        abstract = True


class Photo(BaseAccountModel):
    '''
    Model holding the photos and information about them
    '''
    ip_address = models.GenericIPAddressField(unpack_ipv4=True)
    data = models.BinaryField()
    format = models.CharField(max_length=3)

    class Meta:
        '''
        Class attributes
        '''
        verbose_name = _('photo')
        verbose_name_plural = _('photos')

    def import_image(self, service_name, email_address):
        image_url = False

        if service_name == 'Gravatar':
            gravatar = get_gravatar_photo(email_address)
            if gravatar:
                image_url = gravatar['image_url']

        if not image_url:
            return False  # pragma: no cover
        try:
            image = urlopen(image_url)
        # No idea how to test this
        except HTTPError as e:  # pragma: no cover
            print('%s import failed with an HTTP error: %s' %
                  (service_name, e.code))
            return False
        # No idea how to test this
        except URLError as e:  # pragma: no cover
            print('%s import failed: %s' % (service_name, e.reason))
            return False
        data = image.read()

        try:
            img = Image.open(BytesIO(data))
        # How am I supposed to test this?
        except ValueError:  # pragma: no cover
            return False  # pragma: no cover

        self.format = file_format(img.format)
        if not self.format:
            print('Unable to determine format: %s' % img)  # pragma: no cover
            return False  # pragma: no cover
        self.data = data
        super().save()
        return True

    def save(self, *args, **kwargs):
        '''
        Override save from parent, taking care about the image
        '''
        # Use PIL to read the file format
        try:
            img = Image.open(BytesIO(self.data))
        # Testing? Ideas anyone?
        except Exception as e:  # pylint: disable=unused-variable
            # For debugging only
            print('Exception caught: %s' % e)
            return False
        self.format = file_format(img.format)
        if not self.format:
            print('Format not recognized')
            return False
        return super().save(*args, **kwargs)

    def perform_crop(self, request, dimensions, email, openid):
        if request.user.photo_set.count() == 1:
            # This is the first photo, assign to all confirmed addresses
            for email in request.user.confirmedemail_set.all():
                email.photo = self
                email.save()

            for openid in request.user.confirmedopenid_set.all():
                openid.photo = self
                openid.save()

        if email:
            # Explicitely asked
            email.photo = self
            email.save()

        if openid:
            # Explicitely asked
            openid.photo = self
            openid.save()

        # Do the real work cropping
        img = Image.open(BytesIO(self.data))

        # This should be anyway checked during save...
        a, b = img.size
        if a > MAX_PIXELS or b > MAX_PIXELS:
            messages.error(request, _('Image dimensions are too big(max: %s x %s' % (MAX_PIXELS, MAX_PIXELS)))
            return HttpResponseRedirect(reverse_lazy('profile'))

        w = dimensions['w']
        h = dimensions['h']
        x = dimensions['x']
        y = dimensions['y']

        if w == 0 and h == 0:
            w, h = a, b
            i = min(w, h)
            w, h = i, i
        elif w < 0 or (x + w) > a or h < 0 or (y + h) > b:
            messages.error(request, _('Crop outside of original image bounding box'))
            return HttpResponseRedirect(reverse_lazy('profile'))

        cropped = img.crop((x, y, x + w, y + h))
        # cropped.load()
        # Resize the image only if it's larger than the specified max width.
        cropped_w, cropped_h = cropped.size
        max_w = AVATAR_MAX_SIZE
        if cropped_w > max_w or cropped_h > max_w:
            cropped = cropped.resize((max_w, max_w), Image.ANTIALIAS)

        data = BytesIO()
        cropped.save(data, pil_format(self.format), quality=JPEG_QUALITY)
        data.seek(0)
        # Create new photo?
        # photo = Photo()
        # photo.user = request.user
        # photo.ip_address = get_client_ip(request)
        # photo.data = data.read()
        # photo.save()

        # Overwrite the existing image
        self.data = data.read()
        self.save()

        return HttpResponseRedirect(reverse_lazy('profile'))


class ConfirmedEmailManager(models.Manager):
    '''
    Manager for our confirmed email addresses model
    '''

    def create_confirmed_email(self, user, email_address, is_logged_in):
        '''
        Helper method to create confirmed email address
        '''
        confirmed = ConfirmedEmail()
        confirmed.user = user
        confirmed.ip_address = '0.0.0.0'
        confirmed.email = email_address
        confirmed.save()

        external_photos = []
        if is_logged_in:
            gravatar = get_gravatar_photo(confirmed.email)
            if gravatar:
                external_photos.append(gravatar)

        return (confirmed.pk, external_photos)


class ConfirmedEmail(BaseAccountModel):
    '''
    Model holding our confirmed email addresses, as well as the relation
    to the assigned photo
    '''
    email = models.EmailField(unique=True, max_length=MAX_LENGTH_EMAIL)
    photo = models.ForeignKey(
        Photo,
        related_name='emails',
        blank=True,
        null=True,
        on_delete=models.deletion.CASCADE,
    )
    digest = models.CharField(max_length=64)
    objects = ConfirmedEmailManager()

    class Meta:
        '''
        Class attributes
        '''
        verbose_name = _('confirmed email')
        verbose_name_plural = _('confirmed emails')

    def set_photo(self, photo):
        '''
        Helper method to set photo
        '''
        self.photo = photo
        self.save()

    def save(self, *args, **kwargs):
        '''
        Override save from parent, add digest
        '''
        self.digest = hashlib.md5(
            self.email.strip().lower().encode('utf-8')
        ).hexdigest()
        return super().save(*args, **kwargs)


class UnconfirmedEmail(BaseAccountModel):
    '''
    Model holding unconfirmed email addresses as well as the verification key
    '''
    email = models.EmailField(max_length=MAX_LENGTH_EMAIL)
    verification_key = models.CharField(max_length=64)

    class Meta:
        '''
        Class attributes
        '''
        verbose_name = _('unconfirmed_email')
        verbose_name_plural = _('unconfirmed_emails')

    def save(self, *args, **kwargs):
        hash_object = hashlib.new('sha256')
        hash_object.update(urandom(1024) + self.user.username.encode('utf-8'))
        self.verification_key = hash_object.hexdigest()
        super(UnconfirmedEmail, self).save(*args, **kwargs)


class UnconfirmedOpenId(BaseAccountModel):
    '''
    Model holding unconfirmed OpenIDs
    '''
    openid = models.URLField(unique=False, max_length=MAX_LENGTH_URL)

    class Meta:
        verbose_name = _('unconfirmed OpenID')
        verbose_name_plural = ('unconfirmed_OpenIDs')


class ConfirmedOpenId(BaseAccountModel):
    '''
    Model holding confirmed OpenIDs, as well as the relation to
    the assigned photo
    '''
    openid = models.URLField(unique=True, max_length=MAX_LENGTH_URL)
    photo = models.ForeignKey(
        Photo,
        related_name='openids',
        blank=True,
        null=True,
        on_delete=models.deletion.CASCADE,
    )
    digest = models.CharField(max_length=64)

    class Meta:
        verbose_name = _('confirmed OpenID')
        verbose_name_plural = _('confirmed OpenIDs')

    def set_photo(self, photo):
        self.photo = photo
        self.save()

    def save(self, *args, **kwargs):
        url = urlsplit(self.openid)
        if url.username:  # pragma: no cover
            password = url.password or ''
            netloc = url.username + ':' + password + '@' + url.hostname
        else:
            netloc = url.hostname
        lowercase_url = urlunsplit(
            (url.scheme.lower(), netloc, url.path, url.query, url.fragment)
        )
        self.digest = hashlib.sha256(lowercase_url.encode('utf-8')).hexdigest()
        return super().save(*args, **kwargs)


class OpenIDNonce(models.Model):
    '''
    Model holding OpenID Nonces
    See also: https://github.com/edx/django-openid-auth/
    '''
    server_url = models.CharField(max_length=255)
    timestamp = models.IntegerField()
    salt = models.CharField(max_length=128)


class OpenIDAssociation(models.Model):
    '''
    Model holding the relation/association about OpenIDs
    '''
    server_url = models.TextField(max_length=2047)
    handle = models.CharField(max_length=255)
    secret = models.TextField(max_length=255)  # stored base64 encoded
    issued = models.IntegerField()
    lifetime = models.IntegerField()
    assoc_type = models.TextField(max_length=64)


class DjangoOpenIDStore(OpenIDStore):
    '''
    The Python openid library needs an OpenIDStore subclass to persist data
    related to OpenID authentications. This one uses our Django models.
    '''

    def storeAssociation(self, server_url, association):  # pragma: no cover
        '''
        Helper method to store associations
        TODO: Could be moved to classmethod
        '''
        assoc = OpenIDAssociation(
            server_url=server_url,
            handle=association.handle,
            secret=base64.encodestring(association.secret),
            issued=association.issued,
            lifetime=association.issued,
            assoc_type=association.assoc_type)
        assoc.save()

    def getAssociation(self, server_url, handle=None):  # pragma: no cover
        '''
        Helper method to get associations
        '''
        assocs = []
        if handle is not None:
            assocs = OpenIDAssociation.objects.filter(
                server_url=server_url, handle=handle)
        else:
            assocs = OpenIDAssociation.objects.filter(server_url=server_url)
        if not assocs:
            return None
        associations = []
        for assoc in assocs:
            if type(assoc.secret) is str:
                assoc.secret = assoc.secret.split("b'")[1].split("'")[0]
                assoc.secret = bytes(assoc.secret, 'utf-8')
            association = OIDAssociation(assoc.handle,
                                         base64.decodestring(assoc.secret),
                                         assoc.issued, assoc.lifetime,
                                         assoc.assoc_type)
            expires = 0
            try:
                expires = association.getExpiresIn()
            except Exception as e:
                expires = association.expiresIn
            if expires == 0:
                self.removeAssociation(server_url, assoc.handle)
            else:
                associations.append((association.issued, association))
        if not associations:
            return None
        return associations[-1][1]

    def removeAssociation(self, server_url, handle):  # pragma: no cover
        '''
        Helper method to remove associations
        TODO: Could be moved to classmethod
        '''
        assocs = list(
            OpenIDAssociation.objects.filter(
                server_url=server_url, handle=handle))
        assocs_exist = len(assocs) > 0
        for assoc in assocs:
            assoc.delete()
        return assocs_exist

    def useNonce(self, server_url, timestamp, salt):  # pragma: no cover
        '''
        Helper method to 'use' nonces
        TODO: Could be moved to classmethod
        '''
        # Has nonce expired?
        if abs(timestamp - time.time()) > oidnonce.SKEW:
            return False
        try:
            nonce = OpenIDNonce.objects.get(
                server_url__exact=server_url,
                timestamp__exact=timestamp,
                salt__exact=salt)
        except OpenIDNonce.DoesNotExist:
            nonce = OpenIDNonce.objects.create(
                server_url=server_url, timestamp=timestamp, salt=salt)
            return True
        nonce.delete()
        return False

    def cleanupNonces(self):  # pragma: no cover
        '''
        Helper method to cleanup nonces
        TODO: Could be moved to classmethod
        '''
        timestamp = int(time.time()) - oidnonce.SKEW
        OpenIDNonce.objects.filter(timestamp__lt=timestamp).delete()

    def cleanupAssociations(self):  # pragma: no cover
        '''
        Helper method to cleanup associations
        TODO: Could be moved to classmethod
        '''
        OpenIDAssociation.objects.extra(
            where=['issued + lifetimeint < (%s)' % time.time()]).delete()
