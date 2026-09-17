from django.contrib.auth.models import AnonymousUser, Group
from django.test import TestCase

from apps.accounts.models import User
from apps.accounts.permissions import (
    has_role,
    is_business_developer,
    is_engineer,
    is_super_admin,
    is_technical_manager,
)
from apps.accounts.roles import Roles


class AccountPermissionServicesTests(TestCase):
    def setUp(self):
        self.bd_group, _ = Group.objects.get_or_create(name=Roles.BUSINESS_DEVELOPER)
        self.tm_group, _ = Group.objects.get_or_create(name=Roles.TECHNICAL_MANAGER)
        self.eng_group, _ = Group.objects.get_or_create(name=Roles.ENGINEER)
        self.admin_group, _ = Group.objects.get_or_create(name=Roles.SUPER_ADMIN)

        self.user = User.objects.create_user(
            email="regular@example.com",
            password="password123",
        )

    def test_has_role_for_unauthenticated_user(self):
        anon = AnonymousUser()
        self.assertFalse(has_role(anon, Roles.BUSINESS_DEVELOPER))

    def test_has_role_false_when_not_in_group(self):
        self.assertFalse(has_role(self.user, Roles.BUSINESS_DEVELOPER))

    def test_has_role_true_when_in_group(self):
        self.user.groups.add(self.bd_group)
        self.assertTrue(has_role(self.user, Roles.BUSINESS_DEVELOPER))

    def test_is_super_admin_for_superuser_and_group(self):
        self.assertFalse(is_super_admin(self.user))

        # Superuser check
        self.user.is_superuser = True
        self.user.save()
        self.assertTrue(is_super_admin(self.user))

        # Group check
        self.user.is_superuser = False
        self.user.save()
        self.user.groups.add(self.admin_group)
        self.assertTrue(is_super_admin(self.user))

    def test_is_business_developer(self):
        self.assertFalse(is_business_developer(self.user))
        self.user.groups.add(self.bd_group)
        self.assertTrue(is_business_developer(self.user))

    def test_is_technical_manager(self):
        self.assertFalse(is_technical_manager(self.user))
        self.user.groups.add(self.tm_group)
        self.assertTrue(is_technical_manager(self.user))

    def test_is_engineer(self):
        self.assertFalse(is_engineer(self.user))
        self.user.groups.add(self.eng_group)
        self.assertTrue(is_engineer(self.user))
