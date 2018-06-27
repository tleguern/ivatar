'''
Default: useful variables for the base page templates.
'''

from ipware import get_client_ip
from ivatar.settings import IVATAR_VERSION, SITE_NAME


def basepage(request):
    '''
    Our contextprocessor adds additional context variables
    in order to be used in the templates
    '''
    context = {}
    if 'openid_identifier' in request.GET:
        context['openid_identifier'] = \
            request.GET['openid_identifier']  # pragma: no cover
    client_ip = get_client_ip(request)[0]
    context['client_ip'] = client_ip
    context['ivatar_version'] = IVATAR_VERSION
    context['site_name'] = SITE_NAME
    context['site_url'] = request.build_absolute_uri('/')[:-1]
    return context
