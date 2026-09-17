from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.accounts.roles import Roles


class AccountsViewsAPITests(APITestCase):
    def setUp(self):
        self.admin_group, _ = Group.objects.get_or_create(name=Roles.SUPER_ADMIN)
        self.tm_group, _ = Group.objects.get_or_create(name=Roles.TECHNICAL_MANAGER)
        self.bd_group, _ = Group.objects.get_or_create(name=Roles.BUSINESS_DEVELOPER)

        self.super_admin = User.objects.create_superuser(
            email="superadmin@example.com",
            password="adminpassword123",
        )
        self.super_admin.groups.add(self.admin_group)

        self.tm_user = User.objects.create_user(
            email="tm@example.com",
            password="password123",
            first_name="Tech",
            last_name="Lead",
        )
        self.tm_user.groups.add(self.tm_group)

        self.regular_user = User.objects.create_user(
            email="user@example.com",
            password="password123",
        )

        self.list_url = reverse("accounts:user-list")
        self.roles_url = reverse("accounts:user-roles", kwargs={"pk": self.tm_user.pk})
        self.users_page_url = reverse("accounts:user-page-list")

    def test_role_user_list_unauthenticated(self):
        response = self.client.get(self.list_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_role_user_list_by_role_filter(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.list_url, {"role": Roles.TECHNICAL_MANAGER})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        emails = [item["email"] for item in response.data]
        self.assertIn("tm@example.com", emails)
        self.assertNotIn("user@example.com", emails)

    def test_role_user_list_without_filter_regular_user_returns_empty(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_role_user_list_without_filter_super_admin_returns_all(self):
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 3)

    def test_user_role_update_unauthenticated(self):
        response = self.client.post(self.roles_url, {"roles": [Roles.ENGINEER]})
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_user_role_update_non_admin_forbidden(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post(self.roles_url, {"roles": [Roles.ENGINEER]})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_role_update_invalid_role_bad_request(self):
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.post(self.roles_url, {"roles": ["FakeRole"]})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("roles", response.data)

    def test_user_role_update_success_by_super_admin(self):
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.post(
            self.roles_url,
            {"roles": [Roles.BUSINESS_DEVELOPER]},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.tm_user.refresh_from_db()
        self.assertIn(Roles.BUSINESS_DEVELOPER, self.tm_user.role_names)
        self.assertNotIn(Roles.TECHNICAL_MANAGER, self.tm_user.role_names)

    def test_users_page_access_control(self):
        # Unauthenticated redirects to login
        response = self.client.get(self.users_page_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Non-admin gets 403
        self.client.force_login(self.regular_user)
        response = self.client.get(self.users_page_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Super admin gets 200
        self.client.force_login(self.super_admin)
        response = self.client.get(self.users_page_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, "accounts/user_list.html")
