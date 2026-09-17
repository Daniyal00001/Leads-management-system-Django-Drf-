from decimal import Decimal
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.accounts.models import User
from apps.accounts.roles import Roles
from apps.leads.models import Lead
from apps.projects.models import Project, ProjectManager
from apps.projects.services import assign_project_manager


class ProjectServicesTests(TestCase):
    def setUp(self):
        self.tm_group, _ = Group.objects.get_or_create(name=Roles.TECHNICAL_MANAGER)
        self.bd_group, _ = Group.objects.get_or_create(name=Roles.BUSINESS_DEVELOPER)

        self.bd_user = User.objects.create_user(email="bd@proj.com", password="pw")
        self.bd_user.groups.add(self.bd_group)

        self.tm_user = User.objects.create_user(email="tm@proj.com", password="pw")
        self.tm_user.groups.add(self.tm_group)

        self.non_tm_user = User.objects.create_user(email="nontm@proj.com", password="pw")

        self.lead = Lead.objects.create(
            project_name="Logistics App",
            client_name="Logistics Inc",
            client_email="logistics@inc.com",
            client_contact="123",
            platform_used="Upwork",
            created_by=self.bd_user,
        )

        self.project = Project.objects.create(
            lead=self.lead,
            title="Logistics App",
            sale_amount=Decimal("30000.00"),
            created_by=self.bd_user,
        )

    def test_assign_project_manager_validates_tm_role(self):
        with self.assertRaises(ValidationError):
            assign_project_manager(
                self.project,
                manager=self.non_tm_user,
                assigned_by=self.bd_user,
            )

    def test_assign_project_manager_success_and_prevent_duplicate(self):
        pm = assign_project_manager(
            self.project,
            manager=self.tm_user,
            assigned_by=self.bd_user,
        )
        self.assertEqual(pm.manager, self.tm_user)
        self.assertEqual(pm.project, self.project)

        with self.assertRaises(ValidationError):
            assign_project_manager(
                self.project,
                manager=self.tm_user,
                assigned_by=self.bd_user,
            )
