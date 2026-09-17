from django.contrib.auth.models import AnonymousUser, Group
from django.test import RequestFactory, TestCase
from django.urls import reverse
from rest_framework.test import APIRequestFactory

from apps.accounts.models import User
from apps.accounts.roles import Roles
from apps.core.permissions import HasAnyRole, IsSuperAdmin
from apps.core.views import dashboard_page


class DummyRolePermission(HasAnyRole):
    allowed_roles = [Roles.TECHNICAL_MANAGER]


class CoreViewsAndPermissionsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.api_factory = APIRequestFactory()

        self.admin_group, _ = Group.objects.get_or_create(name=Roles.SUPER_ADMIN)
        self.bd_group, _ = Group.objects.get_or_create(name=Roles.BUSINESS_DEVELOPER)
        self.tm_group, _ = Group.objects.get_or_create(name=Roles.TECHNICAL_MANAGER)
        self.eng_group, _ = Group.objects.get_or_create(name=Roles.ENGINEER)

        self.super_admin = User.objects.create_superuser(
            email="admin@core.com",
            password="password",
        )
        self.super_admin.groups.add(self.admin_group)

        self.bd_user = User.objects.create_user(
            email="bd@core.com",
            password="password",
        )
        self.bd_user.groups.add(self.bd_group)

        self.tm_user = User.objects.create_user(
            email="tm@core.com",
            password="password",
        )
        self.tm_user.groups.add(self.tm_group)

        self.eng_user = User.objects.create_user(
            email="eng@core.com",
            password="password",
        )
        self.eng_user.groups.add(self.eng_group)

    def test_has_any_role_permission_evaluation(self):
        perm = DummyRolePermission()

        # Unauthenticated
        request = self.api_factory.get("/")
        request.user = AnonymousUser()
        self.assertFalse(perm.has_permission(request, None))

        # Super admin always allowed
        request.user = self.super_admin
        self.assertTrue(perm.has_permission(request, None))

        # Allowed role TM allowed
        request.user = self.tm_user
        self.assertTrue(perm.has_permission(request, None))

        # Non-allowed role BD denied
        request.user = self.bd_user
        self.assertFalse(perm.has_permission(request, None))

    def test_is_super_admin_permission_evaluation(self):
        perm = IsSuperAdmin()

        request = self.api_factory.get("/")
        request.user = self.super_admin
        self.assertTrue(perm.has_permission(request, None))

        request.user = self.bd_user
        self.assertFalse(perm.has_permission(request, None))

    def test_dashboard_unauthenticated_redirects(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_bd_user(self):
        self.client.force_login(self.bd_user)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["show_bd_queue"])
        self.assertFalse(response.context["show_engineer_queue"])

    def test_dashboard_tm_user(self):
        self.client.force_login(self.tm_user)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["show_tm_queue"])
        self.assertFalse(response.context["show_bd_queue"])

    def test_dashboard_super_admin_includes_user_counts(self):
        self.client.force_login(self.super_admin)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["user_count"])
        self.assertTrue(response.context["show_bd_queue"])
