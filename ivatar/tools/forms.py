'''
Classes for our ivatar.tools.forms
'''
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError


class CheckDomainForm(forms.Form):
    '''
    Form handling domain check
    '''
    can_distribute = forms.TextInput(
        attrs={
            'label': _('Domain'),
            'required': True,
            'error_messages': {
                'required':
                _('Cannot check without a domain name.')
            }
        }
    )


class CheckForm(forms.Form):
    '''
    Form handling check
    '''
    mail = forms.EmailField(
        label=_('E-Mail'),
        required=False,
        error_messages={
            'required':
            _('Cannot check without a domain name.')
        })

    openid = forms.CharField(
        label=_('OpenID'),
        required=False,
        error_messages={
            'required':
            _('Cannot check without an openid name.')
        })

    size = forms.IntegerField(
        label=_('Size'),
        initial=80,
        min_value=10,
        max_value=160,
        required=True,
    )

    default_url = forms.URLField(
        label=_('Default URL'),
        required=False,
    )

    def clean(self):
        self.cleaned_data = super().clean()
        mail = self.cleaned_data.get('mail')
        openid = self.cleaned_data.get('openid')
        if not mail and not openid:
            raise ValidationError(_('Either OpenID or mail must be specified'))
        return self.cleaned_data
