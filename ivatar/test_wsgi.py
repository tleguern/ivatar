import unittest

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'ivatar.settings'
django.setup()


class TestCase(unittest.TestCase):
    def test_run_wsgi(self):
        import ivatar.wsgi
        self.assertEqual(ivatar.wsgi.application.__class__,
                         django.core.handlers.wsgi.WSGIHandler)
