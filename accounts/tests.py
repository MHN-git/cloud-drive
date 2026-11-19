from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from quota.models import Quota


User = get_user_model()


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "accounts-tests",
        }
    }
)
class AccountAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.signup_url = "/api/v1/auth/signup/"
        self.token_url = "/api/v1/auth/token/"

    def test_register_user_successfully(self):
        payload = {
            "username": "testuser",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        }

        response = self.client.post(
            self.signup_url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="testuser").exists())

        user = User.objects.get(username="testuser")

        self.assertTrue(user.check_password("StrongPass123!"))
        self.assertTrue(Quota.objects.filter(owner=user).exists())

    def test_register_with_duplicate_username(self):
        User.objects.create_user(
            username="testuser",
            password="StrongPass123!",
        )

        payload = {
            "username": "testuser",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        }

        response = self.client.post(
            self.signup_url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_with_different_passwords(self):
        payload = {
            "username": "testuser",
            "password1": "StrongPass123!",
            "password2": "DifferentPass123!",
        }

        response = self.client.post(
            self.signup_url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="testuser").exists())

    def test_login_successfully(self):
        User.objects.create_user(
            username="testuser",
            password="StrongPass123!",
        )

        payload = {
            "username": "testuser",
            "password": "StrongPass123!",
        }

        response = self.client.post(
            self.token_url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_with_invalid_password(self):
        User.objects.create_user(
            username="testuser",
            password="StrongPass123!",
        )

        payload = {
            "username": "testuser",
            "password": "WrongPassword123!",
        }

        response = self.client.post(
            self.token_url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
