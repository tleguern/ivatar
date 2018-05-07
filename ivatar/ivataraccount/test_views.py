from django.test import TestCase
from django.test import Client
from django.urls import reverse

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'ivatar.settings'
django.setup()

from ivatar.utils import random_string

class Tester(TestCase):
    client = Client()
    username = random_string()
    password = random_string()
    
    def test_new_user(self):
        """
        Create a new user
        """
        response = self.client.get(reverse('new_account'))
        self.assertEqual(response.status_code, 200, 'no 200 ok?')
        url = reverse('new_account')
        response = self.client.post(url, {
            'username': self.username,
            'password1': self.password,
            'password2': self.password,
        })
        print(response)
