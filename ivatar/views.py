'''
views under /
'''
import io
from django.views.generic.base import TemplateView
from django.http import HttpResponse
from . ivataraccount.models import ConfirmedEmail, ConfirmedOpenId
from django.core.exceptions import ObjectDoesNotExist


class AvatarImageView(TemplateView):
    '''
    View to return (binary) image, based for OpenID/Email (both by digest)
    '''

    def get(self, request, *args, **kwargs):
        '''
        Override get from parent class
        '''
        model = ConfirmedEmail
        if len(kwargs['digest']) == 32:
            # Fetch by digest from mail
            pass
        elif len(kwargs['digest']) == 64:
            if model.objects.filter(digest=kwargs['digest']).count():
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
                # TODO: Use default!?
                raise Exception('Mail/openid ("%s") does not exist"' %
                                kwargs['digest'])
        if not obj.photo:
            # That is hacky, but achieves what we want :-)
            attr = getattr(obj, 'email', obj.openid)
            # TODO: Use default!?
            raise Exception('No photo assigned to "%s"' % attr)

        return HttpResponse(
            io.BytesIO(obj.photo.data),
            content_type='image/%s' % obj.photo.format)
