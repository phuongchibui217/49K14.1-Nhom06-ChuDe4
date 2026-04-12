from django.contrib.auth import SESSION_KEY
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse


class LogoutViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='logout_staff',
            password='LogoutPass@123',
            is_staff=True,
        )

    def test_logout_redirects_home_and_clears_auth_session(self):
        client = Client()
        self.assertTrue(client.login(username='logout_staff', password='LogoutPass@123'))

        response = client.get(reverse('accounts:logout'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('pages:home'))
        self.assertNotIn(SESSION_KEY, client.session)
