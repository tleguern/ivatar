'''
views under /
'''
from io import BytesIO
from os import path
from PIL import Image
from django.views.generic.base import TemplateView
from django.http import HttpResponse, HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from ivatar.settings import AVATAR_MAX_SIZE, JPEG_QUALITY
from . ivataraccount.models import ConfirmedEmail, ConfirmedOpenId
from . ivataraccount.models import pil_format


class AvatarImageView(TemplateView):
    '''
    View to return (binary) image, based on OpenID/Email (both by digest)
    '''
    # TODO: Do cache resize images!! Memcached?

    def get(self, request, *args, **kwargs):  # pylint: disable=too-many-branches
        '''
        Override get from parent class
        '''
        model = ConfirmedEmail
        size = 80
        imgformat = 'png'
        obj = None
        default = None

        if 'd' in request.GET:
            default = request.GET['d']

        if 's' in request.GET:
            size = request.GET['s']
        size = int(size)
        if size > int(AVATAR_MAX_SIZE):
            size = int(AVATAR_MAX_SIZE)
        if len(kwargs['digest']) == 32:
            # Fetch by digest from mail
            pass
        elif len(kwargs['digest']) == 64:
            if ConfirmedOpenId.objects.filter(  # pylint: disable=no-member
                    digest=kwargs['digest']).count():
                # Fetch by digest from OpenID
                model = ConfirmedOpenId
        else:  # pragma: no cover
            # We should actually never ever reach this code...
            raise Exception('Digest provided is wrong: %s' % kwargs['digest'])

        try:
            obj = model.objects.get(digest=kwargs['digest'])
        except ObjectDoesNotExist:
            try:
                obj = model.objects.get(digest_sha256=kwargs['digest'])
            except ObjectDoesNotExist:
                pass

        # If that mail/openid doesn't exist, or has no photo linked to it
        if not obj or not obj.photo:
            # Return the default URL, as specified
            if default:
                return HttpResponseRedirect(default)
            # Return our default URl
            else:
                static_img = path.join('static', 'img', 'mm', '%s%s' % (str(size), '.png'))
                if not path.isfile(static_img):
                    # We trust this exists!!!
                    static_img = path.join('static', 'img', 'mm', '512.png')
                # We trust static/ is mapped to /static/
                return HttpResponseRedirect('/' + static_img)
        else:
            imgformat = obj.photo.format
            photodata = Image.open(BytesIO(obj.photo.data))

        photodata.thumbnail((size, size), Image.ANTIALIAS)
        data = BytesIO()
        photodata.save(data, pil_format(imgformat), quality=JPEG_QUALITY)
        data.seek(0)

        return HttpResponse(
            data,
            content_type='image/%s' % imgformat)
