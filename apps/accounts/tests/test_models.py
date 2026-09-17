from django.contrib.auth.models import Group
from django.test import TestCase

from apps.accounts.models import User
from apps.accounts.roles import Roles


class UserModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="developer@example.com",
            password="securepassword123",
            first_name="Jane",
            last_name="Doe",
            phone="1234567890",
        )

    def test_create_user_successful(self):
        self.assertEqual(self.user.email, "developer@example.com")
        self.assertTrue(self.user.check_password("securepassword123"))
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)
        self.assertTrue(self.user.is_active)
        self.assertEqual(self.user.phone, "1234567890")

    def test_create_user_missing_email_raises_error(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="password123")

    def test_create_superuser_successful(self):
        admin = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpassword123",
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertEqual(str(admin), "admin@example.com")

    def test_create_superuser_invalid_flags_raises_error(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="admin2@example.com",
                password="password",
                is_staff=False,
            )
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="admin3@example.com",
                password="password",
                is_superuser=False,
            )

    def test_str_representation(self):
        self.assertEqual(str(self.user), "developer@example.com")

    def test_display_name_with_full_name(self):
        self.assertEqual(self.user.display_name, "Jane Doe")

    def test_display_name_fallback_to_email(self):
        user_no_name = User.objects.create_user(
            email="noname@example.com",
            password="password123",
        )
        self.assertEqual(user_no_name.display_name, "noname@example.com")

    def test_role_names_property(self):
        group_bd, _ = Group.objects.get_or_create(name=Roles.BUSINESS_DEVELOPER)
        group_tm, _ = Group.objects.get_or_create(name=Roles.TECHNICAL_MANAGER)
        self.user.groups.add(group_bd, group_tm)

        self.assertCountEqual(
            self.user.role_names,
            [Roles.BUSINESS_DEVELOPER, Roles.TECHNICAL_MANAGER],
        )
