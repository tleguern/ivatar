from django.shortcuts import render

from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db import transaction
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.views.generic.edit import FormView
from django.views.generic.base import View, TemplateView
from django.views.generic.detail import DetailView
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse_lazy, reverse

from . forms import AddEmailForm, UploadPhotoForm
from . models import UnconfirmedEmail, ConfirmedEmail, Photo

from ivatar.settings import MAX_NUM_PHOTOS, MAX_PHOTO_SIZE

import io

from ipware import get_client_ip

from . gravatar import get_photo as get_gravatar_photo

class CreateView(SuccessMessageMixin, FormView):
    '''
    TODO: Docs
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
            return HttpResponseRedirect(reverse_lazy('login'))  # pragma: no cover

@method_decorator(login_required, name='dispatch')
class PasswordSetView(SuccessMessageMixin, FormView):
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
    template_name = 'add_email.html'
    form_class = AddEmailForm
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        if not form.save(self.request.user):
            messages.error(self.request, _('Address not added'))
        else:
            messages.success(self.request, _('Address added successfully'))
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class RemoveUnconfirmedEmailView(SuccessMessageMixin, View):
    def post(self, *args, **kwargs):
        try:
            email = UnconfirmedEmail.objects.get(
                user=self.request.user, id=kwargs['email_id'])
            email.delete()
            messages.success(self.request, _('Address removed'))
        except UnconfirmedEmail.DoesNotExist:
            messages.error(self.request, _('Address does not exist'))
        return HttpResponseRedirect(reverse_lazy('profile'))

@method_decorator(login_required, name='dispatch')
class ConfirmEmailView(SuccessMessageMixin, TemplateView):
    template_name = 'email_confirmed.html'

    def get(self, *args, **kwargs):
        # be tolerant of extra crap added by mail clients
        key = kwargs['verification_key'].replace(' ', '')

        if len(key) != 64:
            messages.error(self.request, _('Verification key incorrect'))
            return HttpResponseRedirect(reverse_lazy('profile'))

        try:
            unconfirmed = UnconfirmedEmail.objects.get(verification_key=key)
        except UnconfirmedEmail.DoesNotExist:
            messages.error(self.request, _('Verification key does not exist'))
            return HttpResponseRedirect(reverse_lazy('profile'))

        # TODO: Check for a reasonable expiration time in unconfirmed email

        (confirmed_id, external_photos) = ConfirmedEmail.objects.create_confirmed_email(
            unconfirmed.user, unconfirmed.email, not self.request.user.is_anonymous)

        unconfirmed.delete()

        # if there's a single image in this user's profile, assign it to the new email
        confirmed = ConfirmedEmail.objects.get(id=confirmed_id)
        if confirmed.user.photo_set.count() == 1   :
            confirmed.set_photo(confirmed.user.photo_set.first())
        kwargs['photos'] = external_photos
        kwargs['email_id'] = confirmed_id
        return super().get(*args, **kwargs)


@method_decorator(login_required, name='dispatch')
class RemoveConfirmedEmailView(SuccessMessageMixin, View):
    def post(self, *args, **kwargs):
        try:
            email = ConfirmedEmail.objects.get(
                user=self.request.user, id=kwargs['email_id'])
            email.delete()
            messages.success(self.request, _('Address removed'))
        except ConfirmedEmail.DoesNotExist:
            messages.error(self.request, _('Address does not exist'))
        return HttpResponseRedirect(reverse_lazy('profile'))


@method_decorator(login_required, name='dispatch')
class AssignPhotoEmailView(SuccessMessageMixin, TemplateView):
    model = Photo
    template_name = 'assign_photo_email.html'

    def post(self, *args, **kwargs):
        photo = None
        if not 'photo_id' in self.request.POST:
            messages.error(self.request, _('Invalid request [photo_id] missing'))
            return HttpResponseRedirect(reverse_lazy('profile'))

        try:
            photo = self.model.objects.get(
                id=self.request.POST['photo_id'],
                user=self.request.user)
        except self.model.DoesNotExist:
            messages.error(self.request, _('Photo does not exist'))
            return HttpResponseRedirect(reverse_lazy('profile'))

        try:
            email = ConfirmedEmail.objects.get(user=self.request.user,
                    id=kwargs['email_id'])
        except ConfirmedEmail.DoesNotExist:
            messages.error(self.request, _('Invalid request'))
            return HttpResponseRedirect(reverse_lazy('profile'))

        email.photo = photo
        email.save()

        messages.success(self.request, _('Successfully changed photo'))
        return HttpResponseRedirect(reverse_lazy('profile'))

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['email'] = ConfirmedEmail.objects.get(pk=kwargs['email_id'])
        return data

@method_decorator(login_required, name='dispatch')
class ImportPhotoView(SuccessMessageMixin, View):
    def post(self, *args, **kwargs):
        try:
            email = ConfirmedEmail.objects.get(id=kwargs['email_id'], user=self.request.user)
        except:
            messages.error(self.request, _('Address does not exist'))
            return HttpResponseRedirect(reverse_lazy('profile'))

        if 'photo_Gravatar' in self.request.POST:
            photo = Photo()
            photo.user = self.request.user
            photo.ip_address = get_client_ip(self.request)
            if photo.import_image('Gravatar', email.email):
                messages.success(self.request, _('Image successfully imported'))
            else:
                # Honestly, I'm not sure how to test this...
                messages.error(self.request, _('Image import not successful'))  # pragma: no cover
        else:
            messages.warning(self.request, _('Nothing importable'))
        return HttpResponseRedirect(reverse_lazy('profile'))

@method_decorator(login_required, name='dispatch')
class RawImageView(DetailView):
    model = Photo
    def get(self, *args, **kwargs):
        photo = self.model.objects.get(pk=kwargs['pk'])
        return HttpResponse(
            io.BytesIO(photo.data),
            content_type='image/%s' % photo.format)

@method_decorator(login_required, name='dispatch')
class DeletePhotoView(SuccessMessageMixin, View):
    model = Photo

    def get(self, *args, **kwargs):
        try:
            photo = self.model.objects.get(pk=kwargs['pk'], user=self.request.user)
            photo.delete()
        except:
            messages.error(self.request, _('No such image or no permission to delete it'))
            return HttpResponseRedirect(reverse_lazy('profile'))
        messages.success(self.request, _('Photo deleted successfully'))
        return HttpResponseRedirect(reverse_lazy('profile'))

@method_decorator(login_required, name='dispatch')
class UploadPhotoView(SuccessMessageMixin, FormView):
    model = Photo
    template_name = 'upload_photo.html'
    form_class = UploadPhotoForm
    success_message = _('Successfully uploaded')
    success_url = reverse_lazy('profile')

    def post(self, *args, **kwargs):
        num_photos = self.request.user.photo_set.count()
        if num_photos >= MAX_NUM_PHOTOS:
            messages.error(self.request, _('Maximum number of photos (%i) reached' % MAX_NUM_PHOTOS))
            return HttpResponseRedirect(reverse_lazy('profile'))
        return super().post(*args, **kwargs)

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
