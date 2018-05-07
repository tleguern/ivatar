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
        response = self.client.post(
            url, {
                'username': self.username,
                'password1': self.password,
                'password2': self.password,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200, 'unable to create user?')
        self.assertEqual(response.context[0]['user'].username, self.username)

    def test_set_password(self):
        """
        Change the user password
        """
        response = self.client.get(reverse('password_set'))
        self.assertEqual(response.status_code, 200, 'no 200 ok?')
        url = reverse('password_set')
        self.password = random_string()
        response = self.client.post(
            url, {
                'password1': self.password,
                'password2': self.password,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200, 'cannot change password?')
        self.assertEqual(response.context[0]['user'].is_anonymous, True)
