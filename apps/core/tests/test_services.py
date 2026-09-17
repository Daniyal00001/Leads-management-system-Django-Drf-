from django.conf import settings
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings

from apps.accounts.models import User
from apps.accounts.roles import Roles
from apps.core.utils import absolute_url
from apps.core.views import user_role_counts


class CoreServicesTests(TestCase):
    def setUp(self):
        self.admin_group, _ = Group.objects.get_or_create(name=Roles.SUPER_ADMIN)
        self.bd_group, _ = Group.objects.get_or_create(name=Roles.BUSINESS_DEVELOPER)
        self.tm_group, _ = Group.objects.get_or_create(name=Roles.TECHNICAL_MANAGER)
        self.eng_group, _ = Group.objects.get_or_create(name=Roles.ENGINEER)

        self.u1 = User.objects.create_superuser(email="admin@test.com", password="pw")
        self.u1.groups.add(self.admin_group)

        self.u2 = User.objects.create_user(email="bd@test.com", password="pw")
        self.u2.groups.add(self.bd_group)

        self.u3 = User.objects.create_user(email="tm@test.com", password="pw")
        self.u3.groups.add(self.tm_group)

        self.u4 = User.objects.create_user(email="eng@test.com", password="pw")
        self.u4.groups.add(self.eng_group)

    @override_settings(APP_BASE_URL="http://testserver")
    def test_absolute_url_helper(self):
        url = absolute_url("accounts:login")
        self.assertEqual(url, "http://testserver/accounts/login/")

    def test_user_role_counts(self):
        counts = user_role_counts()
        self.assertEqual(counts["total"], 4)
        self.assertEqual(counts["super_admin"], 1)
        self.assertEqual(counts["business_developer"], 1)
        self.assertEqual(counts["technical_manager"], 1)
        self.assertEqual(counts["engineer"], 1)
