from django.shortcuts import render

from django.views.decorators.csrf import csrf_protect
from django.db import transaction
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic.edit import FormView
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

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
