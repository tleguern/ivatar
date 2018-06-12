'''
Default: useful variables for the base page templates.
'''

from ivatar.settings import IVATAR_VERSION, SITE_NAME
from ipware import get_client_ip


def basepage(request):
    '''
    Our contextprocessor adds additional context variables
    in order to be used in the templates
    '''
    context = {}
    if 'openid_identifier' in request.GET:
        context['openid_identifier'] = \
            request.GET['openid_identifier']  # pragma: no cover
    client_ip, is_routable = get_client_ip(request)
    context['client_ip'] = client_ip
    context['ivatar_version'] = IVATAR_VERSION
    context['site_name'] = SITE_NAME
    context['site_url'] = request.build_absolute_uri('/')
    return context
