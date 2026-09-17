from decimal import Decimal
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.accounts.roles import Roles
from apps.leads.models import Lead
from apps.projects.models import Project


class ProjectsViewsAPITests(APITestCase):
    def setUp(self):
        self.bd_group, _ = Group.objects.get_or_create(name=Roles.BUSINESS_DEVELOPER)
        self.tm_group, _ = Group.objects.get_or_create(name=Roles.TECHNICAL_MANAGER)
        self.eng_group, _ = Group.objects.get_or_create(name=Roles.ENGINEER)

        self.bd_user = User.objects.create_user(email="bd@projview.com", password="pw")
        self.bd_user.groups.add(self.bd_group)

        self.tm_user = User.objects.create_user(email="tm@projview.com", password="pw")
        self.tm_user.groups.add(self.tm_group)

        self.eng_user = User.objects.create_user(email="eng@projview.com", password="pw")
        self.eng_user.groups.add(self.eng_group)

        self.lead = Lead.objects.create(
            project_name="Fleet Tracking",
            client_name="Fleet Co",
            client_email="fleet@example.com",
            client_contact="333-444",
            platform_used="Upwork",
            created_by=self.bd_user,
        )

        self.project = Project.objects.create(
            lead=self.lead,
            title="Fleet Tracking App",
            sale_amount=Decimal("25000.00"),
            created_by=self.bd_user,
        )

        self.list_url = reverse("projects:project-list")
        self.detail_url = reverse("projects:project-detail", kwargs={"pk": self.project.pk})
        self.assign_url = reverse("projects:project-assign-manager", kwargs={"pk": self.project.pk})
        self.page_list_url = reverse("projects:project-page-list")
        self.page_detail_url = reverse("projects:project-page-detail", kwargs={"pk": self.project.pk})

    def test_project_list_unauthenticated(self):
        response = self.client.get(self.list_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_project_list_authenticated(self):
        self.client.force_authenticate(user=self.bd_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"] if "results" in response.data else response.data
        self.assertEqual(len(results), 1)

    def test_project_detail_authenticated(self):
        self.client.force_authenticate(user=self.bd_user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Fleet Tracking App")

    def test_project_assign_manager_permissions(self):
        # Engineer cannot assign manager
        self.client.force_authenticate(user=self.eng_user)
        response = self.client.post(self.assign_url, {"manager_id": self.tm_user.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # BD can assign manager
        self.client.force_authenticate(user=self.bd_user)
        response = self.client.post(self.assign_url, {"manager_id": self.tm_user.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertTrue(self.project.project_managers.filter(manager=self.tm_user).exists())

    def test_project_assign_invalid_manager_raises_bad_request(self):
        self.client.force_authenticate(user=self.bd_user)
        # Try assigning engineer as TM
        response = self.client.post(self.assign_url, {"manager_id": self.eng_user.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_project_pages(self):
        self.client.force_login(self.bd_user)
        res_list = self.client.get(self.page_list_url)
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(res_list, "projects/project_list.html")

        res_detail = self.client.get(self.page_detail_url)
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(res_detail, "projects/project_detail.html")
