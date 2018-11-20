"""
Middleware classes
"""
from django.utils.deprecation import MiddlewareMixin

class MultipleProxyMiddleware(MiddlewareMixin):  # pylint: disable=too-few-public-methods
    """
    Middleware to rewrite proxy headers for deployments
    with multiple proxies
    """

    def process_request(self, request):
        """
        Rewrites the proxy headers so that forwarded server is
        used if available.
        """
        if 'HTTP_X_FORWARDED_SERVER' in request.META:
            request.META['HTTP_X_FORWARDED_HOST'] = request.META['HTTP_X_FORWARDED_SERVER']
