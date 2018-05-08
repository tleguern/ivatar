from django.shortcuts import render

from django.views.decorators.csrf import csrf_protect
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

from . forms import AddEmailForm
from . models import UnconfirmedEmail, ConfirmedEmail, Photo

import io

from ipware import get_client_ip

from . gravatar import get_photo as get_gravatar_photo

class CreateView(SuccessMessageMixin, FormView):
    template_name = 'new.html'
    form_class = UserCreationForm
    success_message = _('created successfully')
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        form.save()
        user = authenticate(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password1'])
        if user is not None:
            login(self.request, user)
            return HttpResponseRedirect(reverse_lazy('profile'))
        else:
            return HttpResponseRedirect(reverse_lazy('login'))

        return super().form_valid(form)

class PasswordSetView(SuccessMessageMixin, FormView):
    template_name = 'password_change.html'
    form_class = SetPasswordForm
    success_message = _('password changed successfully')
    success_url = reverse_lazy('profile')

    def get_form_kwargs(self):
        kwargs = super(PasswordSetView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        super().form_valid(form)
        return HttpResponseRedirect(reverse_lazy('login'))

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

class ConfirmEmailView(SuccessMessageMixin, TemplateView):
    template_name = 'email_confirmed.html'

    def get(self, *args, **kwargs):
        if 'verification_key' not in kwargs:
            messages.error(self.request, _('Verification key missing'))
            return HttpResponseRedirect(reverse_lazy('profile'))

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

        # TODO: Check for a reansonable expiration time in unconfirmed email

        # check to see whether this email is already confirmed
        if ConfirmedEmail.objects.filter(email=unconfirmed.email).exists():
            messages.warning(self.request, _('Address already confirmed'))
            # FUCK return HttpResponseRedirect(reverse_lazy('profile'))

        # FUCK - remove this try/except
        try:
            (confirmed_id, external_photos) = ConfirmedEmail.objects.create_confirmed_email(
                unconfirmed.user, unconfirmed.email, not self.request.user.is_anonymous)
        except:
            confirmed_id = ConfirmedEmail.objects.filter(user=self.request.user,email=unconfirmed.email).first().id
            external_photos = get_gravatar_photo(unconfirmed.email)

        # FUCK unconfirmed.delete()

        # if there's a single image in this user's profile, assign it to the new email
        confirmed = ConfirmedEmail.objects.get(id=confirmed_id)
        if confirmed.user.photo_set.count() == 1   :
            confirmed.set_photo(confirmed.user.photos.get())
        kwargs['photos'] = [ external_photos ]
        kwargs['email_id'] = confirmed_id
        return super(ConfirmEmailView, self).get(*args, **kwargs)


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


class AssignPhotoEmailView(SuccessMessageMixin, View):
    def post(self, *args, **kwargs):
        photo = None
        if not 'photo_id' in kwargs:
            mesages.error(self.request, _('Invalid request'))
            return HttpResponseRedirect(reverse_lazy('profile'))
        try:
            photo = Photo.objects.get(
                id=kwargs['photo_id'], user=request.user)
        except Photo.DoesNotExist:
            message.error(self.request, _('Photo does not exist'))
            return HttpResponseRedirect(reverse_lazy('profile'))


class ImportPhotoView(SuccessMessageMixin, View):
    def post(self, *args, **kwargs):
        if not 'email_id' in kwargs:
            messages.error(self.request, _('Address not given'))
            return HttpResponseRedirect(reverse_lazy('profile'))

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
                messages.error(self.request, _('Image import not successful'))
        else:
            messages.warning(self.request, _('Nothing importable'))
        return HttpResponseRedirect(reverse_lazy('profile'))

class RawImageView(DetailView):
    model = Photo
    def get(self, *args, **kwargs):
        photo = self.model.objects.get(pk=kwargs['pk'])
        return HttpResponse(
            io.BytesIO(photo.data),
            content_type='image/%s' % photo.format)
