from decimal import Decimal
from django.db import IntegrityError
from django.test import TestCase

from apps.accounts.models import User
from apps.leads.models import Lead
from apps.projects.models import Project, ProjectManager, ProjectStatus


class ProjectModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="projcreator@example.com",
            password="password123",
        )
        self.manager = User.objects.create_user(
            email="projmgr@example.com",
            password="password123",
        )
        self.lead = Lead.objects.create(
            project_name="Crypto Exchange",
            client_name="Crypto Ltd",
            client_email="crypto@example.com",
            client_contact="111-222",
            platform_used="Upwork",
            created_by=self.user,
        )

    def test_project_creation_and_default_title(self):
        project = Project.objects.create(
            lead=self.lead,
            sale_amount=Decimal("45000.00"),
            created_by=self.user,
        )
        self.assertEqual(project.title, "Crypto Exchange")
        self.assertEqual(str(project), "Crypto Exchange")
        self.assertEqual(project.status, ProjectStatus.ACTIVE)

    def test_project_manager_model_and_unique_constraint(self):
        project = Project.objects.create(
            lead=self.lead,
            title="Crypto Platform",
            sale_amount=Decimal("45000.00"),
            created_by=self.user,
        )
        pm = ProjectManager.objects.create(
            project=project,
            manager=self.manager,
            assigned_by=self.user,
        )
        self.assertEqual(str(pm), f"{self.manager} → {project}")

        with self.assertRaises(IntegrityError):
            ProjectManager.objects.create(
                project=project,
                manager=self.manager,
                assigned_by=self.user,
            )
