from django import forms
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse
from django.template.loader import render_to_string
from django.core.mail import send_mail

from urllib.parse import urlsplit, urlunsplit

from ivatar import settings
from . models import UnconfirmedEmail, ConfirmedEmail, Photo
from . models import UnconfirmedOpenId, ConfirmedOpenId

from ivatar.settings import MAX_LENGTH_EMAIL
from ivatar.ivataraccount.models import MAX_LENGTH_URL

from ipware import get_client_ip

MAX_NUM_UNCONFIRMED_EMAILS_DEFAULT = 5


class AddEmailForm(forms.Form):
    '''
    Form to handle adding email addresses
    '''
    email = forms.EmailField(
        label=_('Email'),
        max_length=MAX_LENGTH_EMAIL,
        min_length=6,  # x@x.xx
    )

    def clean_email(self):
        '''
        Enforce lowercase email
        '''
        # TODO: Domain restriction as in libravatar?
        return self.cleaned_data['email'].lower()

    def save(self, user):
        '''
        Save the model, ensuring some safety
        '''
        # Enforce the maximum number of unconfirmed emails a user can have
        num_unconfirmed = user.unconfirmedemail_set.count()

        max_num_unconfirmed_emails = getattr(
            settings,
            'MAX_NUM_UNCONFIRMED_EMAILS',
            MAX_NUM_UNCONFIRMED_EMAILS_DEFAULT)

        if num_unconfirmed >= max_num_unconfirmed_emails:
            return False

        # Check whether or not a confirmation email has been
        # sent by this user already
        if UnconfirmedEmail.objects.filter(
                user=user, email=self.cleaned_data['email']).exists():
            return False

        # Check whether or not the email is already confirmed by someone
        if ConfirmedEmail.objects.filter(
                email=self.cleaned_data['email']).exists():
            return False

        unconfirmed = UnconfirmedEmail()
        unconfirmed.email = self.cleaned_data['email']
        unconfirmed.user = user
        unconfirmed.save()

        link = settings.SITE_URL + \
            reverse(
                'confirm_email',
                kwargs={'verification_key': unconfirmed.verification_key})
        email_subject = _('Confirm your email address on %s') % \
            settings.SITE_NAME
        email_body = render_to_string('email_confirmation.txt', {
            'verification_link': link,
            'site_name': settings.SITE_NAME,
        })
        # if settings.DEBUG:
        #    print('DEBUG: %s' % link)
        send_mail(
            email_subject, email_body, settings.SERVER_EMAIL,
            [unconfirmed.email])
        return True


class UploadPhotoForm(forms.Form):
    '''
    Form handling photo upload
    '''
    photo = forms.FileField(
        label=_('Photo'),
        error_messages={'required': _('You must choose an image to upload.')})
    not_porn = forms.BooleanField(
        label=_('suitable for all ages (i.e. no offensive content)'),
        required=True,
        error_messages={
            'required':
            _('We only host "G-rated" images and so this field must\
              be checked.')
        })
    can_distribute = forms.BooleanField(
        label=_('can be freely copied'),
        required=True,
        error_messages={
            'required':
            _('This field must be checked since we need to be able to\
              distribute photos to third parties.')
        })

    def save(self, request, data):
        '''
        Save the model and assign it to the current user
        '''
        # Link this file to the user's profile
        photo = Photo()
        photo.user = request.user
        photo.ip_address = get_client_ip(request)
        photo.data = data.read()
        photo.save()
        if not photo.id:
            return None
        return photo


class AddOpenIDForm(forms.Form):
    '''
    Form to handle adding OpenID
    '''
    openid = forms.URLField(
        label=_('OpenID'),
        max_length=MAX_LENGTH_URL,
        # However, not 100% sure if single character domains are possible
        # under any tld...
        min_length=11,  # eg. http://a.io
        initial='http://'
    )

    def clean_openid(self):
        '''
        Enforce restrictions
        '''
        # Lowercase hostname port of the URL
        url = urlsplit(self.cleaned_data['openid'])
        data = urlunsplit(
            (url.scheme.lower(), url.netloc.lower(), url.path,
             url.query, url.fragment))

        # TODO: Domain restriction as in libravatar?

        return data

    def save(self, user):
        '''
        Save the model, ensuring some safety
        '''
        if ConfirmedOpenId.objects.filter(
                openid=self.cleaned_data['openid']).exists():
            return False

        if UnconfirmedOpenId.objects.filter(
                openid=self.cleaned_data['openid']).exists():
            return False

        unconfirmed = UnconfirmedOpenId()
        unconfirmed.openid = self.cleaned_data['openid']
        unconfirmed.user = user
        unconfirmed.save()

        return unconfirmed.id
