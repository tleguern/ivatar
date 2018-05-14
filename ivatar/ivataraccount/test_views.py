from django.test import TestCase
from django.test import Client
from django.urls import reverse

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'ivatar.settings'
django.setup()

from ivatar import settings
from ivatar.ivataraccount.forms import MAX_NUM_UNCONFIRMED_EMAILS_DEFAULT

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from ivatar.utils import random_string
from ivatar.ivataraccount.models import Photo

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

    # CreateView
    def test_new_user(self):
        """
        Create a new user
        """
        response = self.client.get(reverse('new_account'))
        self.assertEqual(response.status_code, 200, 'no 200 ok?')
        # Empty database / eliminate existing users
        User.objects.all().delete()
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

    # CreateView
    def test_new_user_twice(self):
        """
        Try to create a user that already exists
        """
        response = self.client.get(reverse('new_account'))
        self.assertEqual(response.status_code, 200, 'no 200 ok?')
        # Due to setUp(), we already have this user!
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
        self.assertEqual(response.context[0]['user'].username, '')
        self.assertContains(response,
            'A user with that username already exists.', 1, 200, 
            'can we create a user a second time???')

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
                'new_password1': self.password,
                'new_password2': self.password,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200, 'cannot change password?')
        self.assertEqual(str(list(response.context[0]['messages'])[0]),
            'password changed successfully - please login again', 'password change not successful?')

        self.assertIsNotNone(authenticate(
            username=self.username,
            password=self.password,
        ), 'cannot authenticate with new password!?')
                  
        self.login()
        response = self.client.get(reverse('profile'))
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

    def test_confirm_email_w_invalid_auth_key(self):
        '''
        Test confirmation with invalid auth key
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
        url = reverse('confirm_email', args=['x'])
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200,
            'Not able to request confirmation - without verification key?')
        self.assertEqual(str(list(response.context[0]['messages'])[0]),
            'Verification key incorrect', 'Confirm w/o verification key does not produce error message?')

    def test_confirm_email_w_inexisting_auth_key(self):
        '''
        Test confirmation with inexisting auth key
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
        url = reverse('confirm_email', args=['x'*64])
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200,
            'Not able to request confirmation - without verification key?')
        self.assertEqual(str(list(response.context[0]['messages'])[0]),
            'Verification key does not exist',
            'Confirm w/o inexisting key does not produce error message?')


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

    def test_remove_not_existing_confirmed_email(self):
        '''
        Try removing confirmed mail that doesn't exist
        '''
        self.login()
        url = reverse('remove_confirmed_email', args=[1234])
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200,
            'removing email does not redirect to profile?')
        self.assertEqual(str(list(response.context[0]['messages'])[0]),
            'Address does not exist',
            'Removing not existing (confirmed) address, should produce an\
                error message!')

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
        self.assertIsInstance(self.user.photo_set.first(), Photo, 'why is there no Photo (instance)?')

    def test_raw_image(self):
        '''
        test raw image view (as seen in profile <img src=
        '''

        # Ensure we have a photo
        self.test_gravatar_photo_import()
        response = self.client.get(reverse('raw_image', args=[self.user.photo_set.first().id]))
        self.assertEqual(response.status_code, 200, 'cannot fetch photo?')
        # Probably not the best way to access the content type
        self.assertEqual(response._headers['content-type'][1], 'image/jpg', 'Content type wrong!?')

        self.assertEqual(response.content, self.user.photo_set.first().data,
            'raw_image should return the same content as if we read it directly from the DB')

    def test_delete_photo(self):
        '''
        test deleting the photo
        '''

        # Ensure we have a photo
        self.test_gravatar_photo_import()

        url = reverse('delete_photo', args=[self.user.photo_set.first().id])
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200, 'deleting photo doesnt work?')
        self.assertEqual(str(list(response.context[0]['messages'])[0]),
            'Photo deleted successfully', 'Photo deletion did not work?')

    def test_too_many_unconfirmed_email(self):
        '''
        Request too many unconfirmed email addresses, make sure we
        cannot add more
        '''
        self.login()
        # Avoid sending out mails
        settings.EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

        max_num_unconfirmed = getattr(settings, 'MAX_NUM_UNCONFIRMED_EMAILS', MAX_NUM_UNCONFIRMED_EMAILS_DEFAULT)                                                     

        for i in range(max_num_unconfirmed+1):
            response = self.client.post(
                reverse('add_email'), {
                    'email': '%i.%s' %(i, self.email),
                },
            )  # Create test addresses + 1 too much
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200, 'why does profile page not work!?')
        # Take care, since we do did not fetch any pages after adding mail
        # addresses, the messages still sit there waiting to be fetched!!
        # Therefore the message index we need to use is max_num_unconfirmed!
        self.assertEqual(str(list(response.context[0]['messages'])[max_num_unconfirmed]),
                'Address not added', 'Too many unconfirmed address, should return a "not added" messsage!')


    def test_add_mail_address_twice(self):
        '''
        Request the same mail address two times, should not lead to
        having the same address twice
        '''
        self.login()
        # Avoid sending out mails
        settings.EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

        for i in range(2):
            response = self.client.post(
                reverse('add_email'), {
                    'email': self.email,
                },
            )  # Request adding test address twice
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200, 'why does profile page not work!?')
        # Take care, since we do did not fetch any pages after adding mail
        # addresses, the messages still sit there waiting to be fetched!!
        self.assertEqual(str(list(response.context[0]['messages'])[1]),
                'Address not added', 'Adding address twice must lead to "Address not added" message!')

    def test_add_already_confirmed_email(self):
        '''
        Request adding mail address that is already confirmed (by someone)
        '''
        # Create test mail and confirm it, reuse test code
        # Should set EMAIL_BACKEND, so no need to do it here
        self.test_confirm_email()

        response = self.client.post(
            reverse('add_email'), {
                'email': self.email,
            },
        )  # Request adding test address a second time
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200, 'why does profile page not\
                work!?')
        self.assertEqual(str(list(response.context[0]['messages'])[0]),
                'Address not added', 'Adding already added address must lead to\
                        "Address not added" message!')

    def test_remove_unconfirmed_non_existing_email(self):
        '''
        Remove unconfirmed email that doesn't exist
        '''
        self.login()
        url = reverse('remove_unconfirmed_email', args=[1234])
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200, 'unable to remove non existing address?')
        self.assertEqual(str(list(response.context[0]['messages'])[0]),
                'Address does not exist', 'Removing address that does not\
                        exist, should return error message!')

    def test_upload_img(self):
        '''
        Test uploading image
        '''
        self.login()
        url = reverse('upload_photo')
        # rb => Read binary
        with open(os.path.join(settings.STATIC_ROOT, 'img', 'deadbeef.png'), 'rb') as photo:
            response = self.client.post(url, {
                'photo': photo,
                'not_porn': True,
                'can_distribute': True,
            }, follow=True)
        self.assertEqual(self.user.photo_set.count(), 1,
            'there must be exactly one photo now!')

    def test_automatic_photo_assign_to_confirmed_mail(self):
        self.test_upload_img()
        self.test_confirm_email()
        self.assertEqual(self.user.confirmedemail_set.first().photo, self.user.photo_set.first())

    def test_assign_photo_to_email(self):
        self.test_confirm_email()
        self.test_upload_img()
        self.assertIsNone(self.user.confirmedemail_set.first().photo)
        url = reverse('assign_photo_email', args=[self.user.confirmedemail_set.first().id])
        response = self.client.post(url, {
            'photo_id': self.user.photo_set.first().id,
        }, follow=True)
        self.assertEqual(response.status_code, 200, 'cannot assign photo?')
        self.assertEqual(self.user.confirmedemail_set.first().photo, self.user.photo_set.first())

    def test_assign_invalid_photo_id_to_email(self):
        self.test_confirm_email()
        self.test_upload_img()
        self.assertIsNone(self.user.confirmedemail_set.first().photo)
        url = reverse('assign_photo_email', args=[self.user.confirmedemail_set.first().id])
        response = self.client.post(url, {
            'photo_id': 1234,
        }, follow=True)
        self.assertEqual(response.status_code, 200,
            'cannot post assign photo request?')
        self.assertEqual(str(list(response.context[0]['messages'])[0]),
            'Photo does not exist',
            'Assign non existing photo, does not return error message?')

    def test_post_to_assign_photo_without_photo_id(self):
        self.test_confirm_email()
        self.test_upload_img()
        self.assertIsNone(self.user.confirmedemail_set.first().photo)
        url = reverse('assign_photo_email', args=[self.user.confirmedemail_set.first().id])
        response = self.client.post(url, {}, follow=True)
        self.assertEqual(response.status_code, 200,
            'cannot post assign photo request?')
        self.assertEqual(str(list(response.context[0]['messages'])[0]),
            'Invalid request [photo_id] missing',
            'Assign non existing photo, does not return error message?')

    def test_assign_photo_to_inexisting_mail(self):
        self.test_upload_img()
        url = reverse('assign_photo_email', args=[1234])
        response = self.client.post(url, {
            'photo_id': self.user.photo_set.first().id,
        }, follow=True)
        self.assertEqual(response.status_code, 200,
            'cannot post assign photo request?')
        self.assertEqual(str(list(response.context[0]['messages'])[0]),
            'Invalid request',
            'Assign non existing photo, does not return error message?')
