'''
View classes for ivatar/tools/
'''
from django.views.generic.edit import FormView
from django.urls import reverse_lazy as reverse
from django.shortcuts import render

from libravatar import libravatar_url, parse_user_identity
from libravatar import SECURE_BASE_URL as LIBRAVATAR_SECURE_BASE_URL
from libravatar import BASE_URL as LIBRAVATAR_BASE_URL
import hashlib

from .forms import CheckDomainForm, CheckForm
from ivatar.settings import SECURE_BASE_URL, BASE_URL


class CheckDomainView(FormView):
    '''
    View class for checking a domain
    '''
    template_name = 'check_domain.html'
    form_class = CheckDomainForm


class CheckView(FormView):
    '''
    View class for checking an e-mail or openid address
    '''
    template_name = 'check.html'
    form_class = CheckForm
    success_url = reverse('tools_check')

    def form_valid(self, form):
        mailurl = None
        openidurl = None
        mailurl_secure = None
        openidurl_secure = None
        mail_hash = None
        mail_hash256 = None
        openid_hash = None
        size = 80

        super().form_valid(form)

        if form.cleaned_data['default_url']:
            default_url = form.cleaned_data['default_url']
        else:
            default_url = None

        if form.cleaned_data['mail']:
            mailurl = libravatar_url(
              email=form.cleaned_data['mail'],
              size=form.cleaned_data['size'],
              default=default_url)
            mailurl = mailurl.replace(LIBRAVATAR_BASE_URL, BASE_URL)
            mailurl_secure = libravatar_url(
              email=form.cleaned_data['mail'],
              size=form.cleaned_data['size'],
              https=True,
              default=default_url)
            mailurl_secure = mailurl_secure.replace(
              LIBRAVATAR_SECURE_BASE_URL,
              SECURE_BASE_URL)
            mail_hash = parse_user_identity(
              email=form.cleaned_data['mail'],
              openid=None)[0]
            hash_obj = hashlib.new('sha256')
            hash_obj.update(form.cleaned_data['mail'].encode('utf-8'))
            mail_hash256 = hash_obj.hexdigest()
            size = form.cleaned_data['size']
        if form.cleaned_data['openid']:
            if form.cleaned_data['openid'][-1] != '/':
                form.cleaned_data['openid'] += '/'
            openidurl = libravatar_url(
              openid=form.cleaned_data['openid'],
              size=form.cleaned_data['size'],
              default=default_url)
            openidurl = openidurl.replace(LIBRAVATAR_BASE_URL, BASE_URL)
            openidurl_secure = libravatar_url(
              openid=form.cleaned_data['openid'],
              size=form.cleaned_data['size'],
              https=True,
              default=default_url)
            openidurl_secure = openidurl_secure.replace(
              LIBRAVATAR_SECURE_BASE_URL,
              SECURE_BASE_URL)
            openid_hash = parse_user_identity(
              openid=form.cleaned_data['openid'],
              email=None)[0]
            size = form.cleaned_data['size']

        return render(self.request, self.template_name, {
            'form': form,
            'mailurl': mailurl,
            'openidurl': openidurl,
            'mailurl_secure': mailurl_secure,
            'openidurl_secure': openidurl_secure,
            'mail_hash': mail_hash,
            'mail_hash256': mail_hash256,
            'openid_hash': openid_hash,
            'size': size,
        })
