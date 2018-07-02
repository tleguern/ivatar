'''
View classes for ivatar/tools/
'''
from django.views.generic.edit import FormView
from django.urls import reverse_lazy as reverse
from django.shortcuts import render

from .forms import CheckDomainForm, CheckForm


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
        super().form_valid(form)
        return render(self.request, self.template_name, {'form': form})
