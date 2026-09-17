from decimal import Decimal
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.accounts.roles import Roles
from apps.commissions.models import CommissionRecord
from apps.leads.models import Lead
from apps.projects.models import Project


class CommissionsViewsAPITests(APITestCase):
    def setUp(self):
        self.bd_group, _ = Group.objects.get_or_create(name=Roles.BUSINESS_DEVELOPER)
        self.eng_group, _ = Group.objects.get_or_create(name=Roles.ENGINEER)
        self.admin_group, _ = Group.objects.get_or_create(name=Roles.SUPER_ADMIN)

        self.bd_user = User.objects.create_user(
            email="bd@example.com",
            password="password123",
        )
        self.bd_user.groups.add(self.bd_group)

        self.engineer_user = User.objects.create_user(
            email="eng@example.com",
            password="password123",
        )
        self.engineer_user.groups.add(self.eng_group)

        self.super_admin = User.objects.create_superuser(
            email="admin@example.com",
            password="password123",
        )
        self.super_admin.groups.add(self.admin_group)

        self.lead = Lead.objects.create(
            project_name="CRM Project",
            client_name="Sales Corp",
            client_email="crm@example.com",
            client_contact="12345",
            platform_used="Direct",
            created_by=self.bd_user,
        )
        self.project = Project.objects.create(
            lead=self.lead,
            title="CRM Solution",
            sale_amount=Decimal("20000.00"),
            created_by=self.bd_user,
        )

        self.record = CommissionRecord.objects.create(
            project=self.project,
            user=self.bd_user,
            role_name=Roles.BUSINESS_DEVELOPER,
            sale_amount=Decimal("20000.00"),
            commission_percentage=Decimal("5.00"),
            commission_amount=Decimal("1000.00"),
        )

        self.api_url = reverse("commissions:my-commissions")
        self.page_url = reverse("commissions:my-commissions-page")

    def test_my_commissions_unauthenticated(self):
        response = self.client.get(self.api_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_engineer_blocked_from_commissions_api(self):
        self.client.force_authenticate(user=self.engineer_user)
        response = self.client.get(self.api_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_bd_sees_own_commissions(self):
        self.client.force_authenticate(user=self.bd_user)
        response = self.client.get(self.api_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"] if "results" in response.data else response.data), 1)

    def test_super_admin_all_commissions_query(self):
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(self.api_url, {"all": "1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        count = len(response.data["results"] if "results" in response.data else response.data)
        self.assertEqual(count, 1)

    def test_my_commissions_page_access(self):
        # Engineer blocked
        self.client.force_login(self.engineer_user)
        response = self.client.get(self.page_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # BD allowed
        self.client.force_login(self.bd_user)
        response = self.client.get(self.page_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, "commissions/my_commissions.html")

        # Super admin allowed
        self.client.force_login(self.super_admin)
        response = self.client.get(self.page_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
