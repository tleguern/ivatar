'''
View classes for ivatar/ivataraccount/
'''
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.views.generic.edit import FormView
from django.views.generic.base import View, TemplateView
from django.views.generic.detail import DetailView
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse_lazy, reverse

from openid import oidutil
from openid.consumer import consumer

from .forms import AddEmailForm, UploadPhotoForm, AddOpenIDForm
from .models import UnconfirmedEmail, ConfirmedEmail, Photo
from .models import UnconfirmedOpenId, ConfirmedOpenId, DjangoOpenIDStore

from ivatar.settings import MAX_NUM_PHOTOS, MAX_PHOTO_SIZE, SITE_URL

import io

from ipware import get_client_ip

from django_openid_auth.models import UserOpenID


def openid_logging(message, level=0):
    '''
    Helper method for openid logging
    '''
    # Normal messages are not that important
    # No need for coverage here
    if level > 0:  # pragma: no cover
        print(message)


class CreateView(SuccessMessageMixin, FormView):
    '''
    View class for creating a new user
    '''
    template_name = 'new.html'
    form_class = UserCreationForm

    def form_valid(self, form):
        form.save()
        user = authenticate(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password1'])
        if user is not None:
            login(self.request, user)
            return HttpResponseRedirect(reverse_lazy('profile'))
        else:
            return HttpResponseRedirect(
                reverse_lazy('login'))  # pragma: no cover


@method_decorator(login_required, name='dispatch')
class PasswordSetView(SuccessMessageMixin, FormView):
    '''
    View class for changing the password
    '''
    template_name = 'password_change.html'
    form_class = SetPasswordForm
    success_message = _('password changed successfully - please login again')
    success_url = reverse_lazy('profile')

    def get_form_kwargs(self):
        kwargs = super(PasswordSetView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        super().form_valid(form)
        return HttpResponseRedirect(reverse_lazy('login'))


@method_decorator(login_required, name='dispatch')
class AddEmailView(SuccessMessageMixin, FormView):
    '''
    View class for adding email addresses
    '''
    template_name = 'add_email.html'
    form_class = AddEmailForm
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        if not form.save(self.request):
            messages.error(self.request, _('Address not added'))
        else:
            messages.success(self.request, _('Address added successfully'))
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class RemoveUnconfirmedEmailView(SuccessMessageMixin, View):
    '''
    View class for removing a unconfirmed email address
    '''

    def post(self, request, *args, **kwargs):
        try:
            email = UnconfirmedEmail.objects.get(
                user=request.user, id=kwargs['email_id'])
            email.delete()
            messages.success(request, _('Address removed'))
        except UnconfirmedEmail.DoesNotExist:
            messages.error(request, _('Address does not exist'))
        return HttpResponseRedirect(reverse_lazy('profile'))


@method_decorator(login_required, name='dispatch')
class ConfirmEmailView(SuccessMessageMixin, TemplateView):
    '''
    View class for confirming an unconfirmed email address
    '''
    template_name = 'email_confirmed.html'

    def get(self, request, *args, **kwargs):
        # be tolerant of extra crap added by mail clients
        key = kwargs['verification_key'].replace(' ', '')

        if len(key) != 64:
            messages.error(request, _('Verification key incorrect'))
            return HttpResponseRedirect(reverse_lazy('profile'))

        try:
            unconfirmed = UnconfirmedEmail.objects.get(verification_key=key)
        except UnconfirmedEmail.DoesNotExist:
            messages.error(request, _('Verification key does not exist'))
            return HttpResponseRedirect(reverse_lazy('profile'))

        # TODO: Check for a reasonable expiration time in unconfirmed email

        (confirmed_id,
         external_photos) = ConfirmedEmail.objects.create_confirmed_email(
             unconfirmed.user, unconfirmed.email,
             not request.user.is_anonymous)

        unconfirmed.delete()

        # if there's a single image in this user's profile,
        # assign it to the new email
        confirmed = ConfirmedEmail.objects.get(id=confirmed_id)
        if confirmed.user.photo_set.count() == 1:
            confirmed.set_photo(confirmed.user.photo_set.first())
        kwargs['photos'] = external_photos
        kwargs['email_id'] = confirmed_id
        return super().get(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class RemoveConfirmedEmailView(SuccessMessageMixin, View):
    '''
    View class for removing a confirmed email address
    '''

    def post(self, request, *args, **kwargs):
        try:
            email = ConfirmedEmail.objects.get(
                user=request.user, id=kwargs['email_id'])
            email.delete()
            messages.success(request, _('Address removed'))
        except ConfirmedEmail.DoesNotExist:
            messages.error(request, _('Address does not exist'))
        return HttpResponseRedirect(reverse_lazy('profile'))


@method_decorator(login_required, name='dispatch')
class AssignPhotoEmailView(SuccessMessageMixin, TemplateView):
    '''
    View class for assigning a photo to an email address
    '''
    model = Photo
    template_name = 'assign_photo_email.html'

    def post(self, request, *args, **kwargs):
        photo = None
        if 'photo_id' not in request.POST:
            messages.error(request,
                           _('Invalid request [photo_id] missing'))
            return HttpResponseRedirect(reverse_lazy('profile'))

        try:
            photo = self.model.objects.get(
                id=request.POST['photo_id'], user=request.user)
        except self.model.DoesNotExist:
            messages.error(request, _('Photo does not exist'))
            return HttpResponseRedirect(reverse_lazy('profile'))

        try:
            email = ConfirmedEmail.objects.get(
                user=request.user, id=kwargs['email_id'])
        except ConfirmedEmail.DoesNotExist:
            messages.error(request, _('Invalid request'))
            return HttpResponseRedirect(reverse_lazy('profile'))

        email.photo = photo
        email.save()

        messages.success(request, _('Successfully changed photo'))
        return HttpResponseRedirect(reverse_lazy('profile'))

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['email'] = ConfirmedEmail.objects.get(pk=kwargs['email_id'])
        return data


@method_decorator(login_required, name='dispatch')
class AssignPhotoOpenIDView(SuccessMessageMixin, TemplateView):
    '''
    View class for assigning a photo to an openid address
    '''
    model = Photo
    template_name = 'assign_photo_openid.html'

    def post(self, request, *args, **kwargs):
        photo = None
        if 'photo_id' not in request.POST:
            messages.error(request,
                           _('Invalid request [photo_id] missing'))
            return HttpResponseRedirect(reverse_lazy('profile'))

        try:
            photo = self.model.objects.get(
                id=request.POST['photo_id'], user=request.user)
        except self.model.DoesNotExist:
            messages.error(request, _('Photo does not exist'))
            return HttpResponseRedirect(reverse_lazy('profile'))

        try:
            openid = ConfirmedOpenId.objects.get(
                user=request.user, id=kwargs['openid_id'])
        except ConfirmedOpenId.DoesNotExist:
            messages.error(request, _('Invalid request'))
            return HttpResponseRedirect(reverse_lazy('profile'))

        openid.photo = photo
        openid.save()

        messages.success(request, _('Successfully changed photo'))
        return HttpResponseRedirect(reverse_lazy('profile'))

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['openid'] = ConfirmedOpenId.objects.get(pk=kwargs['openid_id'])
        return data


@method_decorator(login_required, name='dispatch')
class ImportPhotoView(SuccessMessageMixin, View):
    '''
    View class to import a photo from another service
    Currently only Gravatar is supported
    '''

    def post(self, request, *args, **kwargs):
        try:
            email = ConfirmedEmail.objects.get(
                id=kwargs['email_id'], user=request.user)
        except Exception as e:
            messages.error(
                request,
                _('Address does not exist'))
            return HttpResponseRedirect(reverse_lazy('profile'))

        if 'photo_Gravatar' in request.POST:
            photo = Photo()
            photo.user = request.user
            photo.ip_address = get_client_ip(request)
            if photo.import_image('Gravatar', email.email):
                messages.success(request,
                                 _('Image successfully imported'))
            else:
                # Honestly, I'm not sure how to test this...
                messages.error(
                    request,
                    _('Image import not successful'))  # pragma: no cover
        else:
            messages.warning(request, _('Nothing importable'))
        return HttpResponseRedirect(reverse_lazy('profile'))


@method_decorator(login_required, name='dispatch')
class RawImageView(DetailView):
    '''
    View to return (binary) raw image data, for use in <img/>-tags
    '''
    model = Photo

    def get(self, request, *args, **kwargs):
        photo = self.model.objects.get(pk=kwargs['pk'])
        return HttpResponse(
            io.BytesIO(photo.data), content_type='image/%s' % photo.format)


@method_decorator(login_required, name='dispatch')
class DeletePhotoView(SuccessMessageMixin, View):
    '''
    View class for deleting a photo
    '''
    model = Photo

    def get(self, request, *args, **kwargs):
        try:
            photo = self.model.objects.get(
                pk=kwargs['pk'], user=request.user)
            photo.delete()
        except Exception as e:
            messages.error(
                request,
                _('No such image or no permission to delete it'))
            return HttpResponseRedirect(reverse_lazy('profile'))
        messages.success(request, _('Photo deleted successfully'))
        return HttpResponseRedirect(reverse_lazy('profile'))


@method_decorator(login_required, name='dispatch')
class UploadPhotoView(SuccessMessageMixin, FormView):
    '''
    View class responsible for photo upload
    '''
    model = Photo
    template_name = 'upload_photo.html'
    form_class = UploadPhotoForm
    success_message = _('Successfully uploaded')
    success_url = reverse_lazy('profile')

    def post(self, request, *args, **kwargs):
        num_photos = request.user.photo_set.count()
        if num_photos >= MAX_NUM_PHOTOS:
            messages.error(
                request,
                _('Maximum number of photos (%i) reached' % MAX_NUM_PHOTOS))
            return HttpResponseRedirect(reverse_lazy('profile'))
        return super().post(request, *args, **kwargs)

    def form_valid(self, form, *args, **kwargs):
        photo_data = self.request.FILES['photo']
        if photo_data.size > MAX_PHOTO_SIZE:
            messages.error(self.request, _('Image too big'))
            return HttpResponseRedirect(reverse_lazy('profile'))

        photo = form.save(self.request, photo_data)

        if not photo:
            messages.error(self.request, _('Invalid Format'))
            return HttpResponseRedirect(reverse_lazy('profile'))

        return super().form_valid(form, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class AddOpenIDView(SuccessMessageMixin, FormView):
    '''
    View class for adding OpenID
    '''
    template_name = 'add_openid.html'
    form_class = AddOpenIDForm
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        openid_id = form.save(self.request.user)
        if not openid_id:
            messages.error(self.request, _('ID not added'))
        else:
            messages.success(self.request, _('ID added successfully'))
            return HttpResponseRedirect(
                reverse_lazy('openid_redirection', args=[openid_id]))

        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class RemoveUnconfirmedOpenIDView(View):
    '''
    View class for removing a unconfirmed OpenID
    '''
    model = UnconfirmedOpenId

    def post(self, request, *args, **kwargs):
        try:
            openid = self.model.objects.get(
                user=request.user, id=kwargs['openid_id'])
            openid.delete()
            messages.success(request, _('ID removed'))
        except self.model.DoesNotExist:  # pragma: no cover
            messages.error(request, _('ID does not exist'))
        return HttpResponseRedirect(reverse_lazy('profile'))


@method_decorator(login_required, name='dispatch')
class RemoveConfirmedOpenIDView(View):
    '''
    View class for removing a confirmed OpenID
    '''
    model = ConfirmedOpenId

    def post(self, request, *args, **kwargs):
        try:
            openid = self.model.objects.get(
                user=request.user, id=kwargs['openid_id'])
            openid.delete()
            messages.success(request, _('ID removed'))
        except self.model.DoesNotExist:
            messages.error(request, _('ID does not exist'))
        return HttpResponseRedirect(reverse_lazy('profile'))


@method_decorator(login_required, name='dispatch')
class RedirectOpenIDView(View):
    model = UnconfirmedOpenId

    def get(self, request, *args, **kwargs):
        try:
            unconfirmed = self.model.objects.get(
                user=request.user, id=kwargs['openid_id'])
        except self.model.DoesNotExist:  # pragma: no cover
            messages.error(request, _('ID does not exist'))
            return HttpResponseRedirect(reverse_lazy('profile'))

        user_url = unconfirmed.openid
        session = {'id': request.session.session_key}

        oidutil.log = openid_logging
        openid_consumer = consumer.Consumer(session, DjangoOpenIDStore())

        try:
            auth_request = openid_consumer.begin(user_url)
        except consumer.DiscoveryFailure as e:
            messages.error(request, _('OpenID discovery failed: %s' % e))
            return HttpResponseRedirect(reverse_lazy('profile'))
        except UnicodeDecodeError as e:  # pragma: no cover
            msg = _('OpenID discovery failed (userid=%s) for %s: %s' %
                    (request.user.id, user_url.encode('utf-8'), e))
            print(msg)
            messages.error(request, msg)

        if auth_request is None:  # pragma: no cover
            messages.error(request, _('OpenID discovery failed'))
            return HttpResponseRedirect(reverse_lazy('profile'))

        realm = request.build_absolute_uri('/')[:-1].strip('/')  # pragma: no cover
        return_url = realm + reverse(  # pragma: no cover
            'confirm_openid', args=[kwargs['openid_id']])
        return HttpResponseRedirect(  # pragma: no cover
            auth_request.redirectURL(realm, return_url))


@method_decorator(login_required, name='dispatch')
class ConfirmOpenIDView(View):  # pragma: no cover
    model = UnconfirmedOpenId
    model_confirmed = ConfirmedOpenId

    def do_request(self, data, *args, **kwargs):
        session = {'id': self.request.session.session_key}
        current_url = SITE_URL + self.request.path
        openid_consumer = consumer.Consumer(session, DjangoOpenIDStore())
        info = openid_consumer.complete(data, current_url)
        if info.status == consumer.FAILURE:
            messages.error(
                self.request,
                _('Confirmation failed: "') + str(info.message) + '"')
            return HttpResponseRedirect(reverse_lazy('profile'))
        elif info.status == consumer.CANCEL:
            messages.error(self.request, _('Cancelled by user'))
            return HttpResponseRedirect(reverse_lazy('profile'))
        elif info.status != consumer.SUCCESS:
            messages.error(self.request, _('Unknown verification error'))
            return HttpResponseRedirect(reverse_lazy('profile'))

        try:
            unconfirmed = self.model.objects.get(
                user=self.request.user, id=kwargs['openid_id'])
        except self.model.DoesNotExist:
            messages.error(self.request, _('ID does not exist'))
            return HttpResponseRedirect(reverse_lazy('profile'))

        # TODO: Check for a reasonable expiration time
        confirmed = self.model_confirmed()
        confirmed.user = unconfirmed.user
        confirmed.ip_address = get_client_ip(self.request)
        confirmed.openid = unconfirmed.openid
        confirmed.save()

        unconfirmed.delete()

        # If there is a single image in this user's profile
        # assign it to the new id
        if self.request.user.photo_set.count() == 1:
            confirmed.set_photo(self.request.user.photo_set.first())

        # Also allow user to login using this OPenID (if not already taken)
        if not UserOpenID.objects.filter(claimed_id=confirmed.openid).exists():
            user_openid = UserOpenID()
            user_openid.user = self.request.user
            user_openid.claimed_id = confirmed.openid
            user_openid.display_id = confirmed.openid
            user_openid.save()
        return HttpResponseRedirect(reverse_lazy('profile'))

    def get(self, request, *args, **kwargs):
        return self.do_request(request.GET, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.do_request(request.POST, *args, **kwargs)
