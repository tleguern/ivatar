from django.test import TestCase
from django.test import Client
from django.urls import reverse

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'ivatar.settings'
django.setup()

from ivatar import settings

from django.contrib.auth.models import User

from ivatar.utils import random_string

class Tester(TestCase):
    client = Client()
    user = None
    username = random_string()
    password = random_string()
    email = '%s@%s.%s' % (username, random_string(), random_string(2))

    def login(self):
        '''
        Login as user
        '''
        self.client.login(username=self.username, password=self.password)

    def setUp(self):
        '''
        Prepare for tests.
        - Create user
        '''
        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
        )
    
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
        self.login()
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.context[0]['user'].username, self.username)

    def test_set_password(self):
        """
        Change the user password
        """
        self.login()
        response = self.client.get(reverse('password_set'))
        self.assertEqual(response.status_code, 200, 'no 200 ok?')
        self.password = random_string()
        response = self.client.post(
            reverse('password_set'), {
                'password1': self.password,
                'password2': self.password,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200, 'cannot change password?')
        self.assertEqual(response.context[0]['user'].is_anonymous, False)

    def test_add_email(self):
        """
        Add e-mail address
        """
        self.login()
        response = self.client.get(reverse('add_email'))
        self.assertEqual(response.status_code, 200, 'no 200 ok?')
        # Avoid sending out mails
        settings.EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
        response = self.client.post(
            reverse('add_email'), {
                'email': self.email,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200, 'cannot add email?')
        self.assertEqual(len(response.context[0]['messages']), 1,
                'there must not be more or less than ONE (1) message')
        self.assertEqual(str(list(response.context[0]['messages'])[0]),
                'Address added successfully', 'unable to add mail address?')

    def test_confirm_email(self):
        '''
        Confirm unconfirmed email
        '''
        self.login()
        # Avoid sending out mails
        settings.EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
        response = self.client.post(
            reverse('add_email'), {
                'email': self.email,
            },
            follow=True,
        )
        verification_key = self.user.unconfirmedemail_set.first().verification_key
        url = reverse('confirm_email', args=[verification_key])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, 'unable to confirm mail address?')

        self.assertEqual(self.user.unconfirmedemail_set.count(), 0,
                'there must not be any unconfirmed address, after confirming it')
        self.assertEqual(self.user.confirmedemail_set.count(), 1,
                'there must not be more or less than ONE (1) confirmed address!')

    def test_remove_confirmed_email(self):
        '''
        Remove confirmed email
        '''
        self.login()
        # Avoid sending out mails
        settings.EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
        response = self.client.post(
            reverse('add_email'), {
                'email': self.email,
            },
        )  # Create test address
        verification_key = self.user.unconfirmedemail_set.first().verification_key
        url = reverse('confirm_email', args=[verification_key])
        self.client.get(url)  # Confirm
        url = reverse('remove_confirmed_email', args=[self.user.confirmedemail_set.first().id])
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200, 'unable to remove confirmed address?')
        self.assertEqual(str(list(response.context[0]['messages'])[0]),
                'Address removed', 'Removing confirmed mail does not work?')

    def test_remove_unconfirmed_email(self):
        '''
        Remove unconfirmed email
        '''
        self.login()
        # Avoid sending out mails
        settings.EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
        response = self.client.post(
            reverse('add_email'), {
                'email': self.email,
            },
        )  # Create test address
        url = reverse('remove_unconfirmed_email', args=[self.user.unconfirmedemail_set.first().id])
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200, 'unable to remove unconfirmed address?')
        # Take care, since we do not fetch any page now, the message we need to check is the
        # _second_ (aka [1], since first is [0])
        self.assertEqual(str(list(response.context[0]['messages'])[1]),
                'Address removed', 'Removing unconfirmed mail does not work?')

    def test_gravatar_photo_import(self):
        '''
        import photo from Gravatar (with known mail address)
        '''
        self.login()
        # Avoid sending out mails
        settings.EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
        response = self.client.post(
            reverse('add_email'), {
                'email': 'oliver@linux-kernel.at',  # Whohu, static :-[
            },
        )  # Create test address
        verification_key = self.user.unconfirmedemail_set.first().verification_key
        url = reverse('confirm_email', args=[verification_key])
        self.client.get(url)  # Confirm

        url = reverse('import_photo', args=[self.user.confirmedemail_set.first().id])
        response = self.client.post(url, {
                'photo_Gravatar': 1,
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200, 'unable to import photo from Gravatar?')
        self.assertEqual(str(list(response.context[0]['messages'])[0]),
            'Image successfully imported', 'Importing gravatar photo did not work?')
