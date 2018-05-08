from django import forms
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse
from django.template.loader import render_to_string
from django.core.mail import send_mail

from ivatar import settings
from . models import UnconfirmedEmail, ConfirmedEmail

from ivatar.settings import MAX_LENGTH_EMAIL

class AddEmailForm(forms.Form):
    email = forms.EmailField(
        label=_('Email'),
        max_length=MAX_LENGTH_EMAIL,
        min_length=6, # x@x.xx
    )

    def clean_email(self):
        '''
        Enforce lowercase email
        '''
        # TODO: Domain restriction as in libravatar?
        return self.cleaned_data['email'].lower()

    def save(self, user):
        # Enforce the maximum number of unconfirmed emails a user can have
        num_unconfirmed = user.unconfirmedemail_set.count()

        max_num_unconfirmed_emails = getattr(settings, 'MAX_NUM_UNCONFIRMED_EMAILS', 5)

        if num_unconfirmed >= max_num_unconfirmed_emails:
            return False

        # Check whether or not a confirmation email has been sent by this user already
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

        link = settings.SITE_URL + reverse('confirm_email', kwargs={'verification_key':unconfirmed.verification_key})
        email_subject = _('Confirm your email address on %s') % settings.SITE_NAME
        email_body = render_to_string('email_confirmation.txt', {
            'verification_link': link,
            'site_name': settings.SITE_NAME,
        })
        if settings.DEBUG:
            print('DEBUG: %s' % link)
        send_mail(email_subject, email_body, settings.SERVER_EMAIL,
            [unconfirmed.email])
        return True
