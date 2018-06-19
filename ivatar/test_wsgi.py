'''
Unit tests for WSGI
'''
import unittest

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'ivatar.settings'
django.setup()


class TestCase(unittest.TestCase):
    '''
    Simple testcase to see if WSGI loads correctly
    '''
    def test_run_wsgi(self):
        '''
        Run wsgi import
        '''
        import ivatar.wsgi
        self.assertEqual(ivatar.wsgi.application.__class__,
                         django.core.handlers.wsgi.WSGIHandler)
