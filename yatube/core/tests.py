from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class ViewTestClass(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='test_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_auth_error_page_404(self):
        response = self.authorized_client.get("/fake_page/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, "core/404.html")

    def test_guest_error_page_404(self):
        response = self.client.get("/fake_page/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, "core/404.html")
