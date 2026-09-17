from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.accounts.roles import Roles
from apps.commissions.models import CommissionRule
from apps.core.choices import TestType
from apps.leads.choices import PhaseStatus
from apps.leads.models import Lead, Phase, PhaseEngineer


class LeadViewsAPITests(APITestCase):
    def setUp(self):
        self.bd_group, _ = Group.objects.get_or_create(name=Roles.BUSINESS_DEVELOPER)
        self.tm_group, _ = Group.objects.get_or_create(name=Roles.TECHNICAL_MANAGER)
        self.eng_group, _ = Group.objects.get_or_create(name=Roles.ENGINEER)
        self.admin_group, _ = Group.objects.get_or_create(name=Roles.SUPER_ADMIN)

        self.bd_user = User.objects.create_user(email="bd@view.com", password="pw")
        self.bd_user.groups.add(self.bd_group)

        self.other_bd = User.objects.create_user(email="otherbd@view.com", password="pw")
        self.other_bd.groups.add(self.bd_group)

        self.tm_user = User.objects.create_user(email="tm@view.com", password="pw")
        self.tm_user.groups.add(self.tm_group)

        self.eng_user = User.objects.create_user(email="eng@view.com", password="pw")
        self.eng_user.groups.add(self.eng_group)

        CommissionRule.objects.get_or_create(
            role_name=Roles.BUSINESS_DEVELOPER,
            defaults={"commission_percentage": Decimal("5.00"), "is_active": True},
        )
        CommissionRule.objects.get_or_create(
            role_name=Roles.TECHNICAL_MANAGER,
            defaults={"commission_percentage": Decimal("10.00"), "is_active": True},
        )

        self.lead = Lead.objects.create(
            project_name="Inventory Engine",
            client_name="Warehouse Ltd",
            client_email="warehouse@example.com",
            client_contact="12345678",
            platform_used="Upwork",
            created_by=self.bd_user,
        )

        self.phase = Phase.objects.create(
            lead=self.lead,
            order=1,
            type=TestType.TEST_PROJECT,
            start_date=date.today(),
            due_date=date.today() + timedelta(days=5),
            created_by=self.bd_user,
            status=PhaseStatus.PENDING_ACCEPTANCE,
            current_manager=self.tm_user,
        )

    def test_lead_list_api(self):
        url = reverse("leads:lead-list")
        # Unauthenticated
        response = self.client.get(url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        # Authenticated
        self.client.force_authenticate(user=self.bd_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_lead_detail_api(self):
        url = reverse("leads:lead-detail", kwargs={"pk": self.lead.pk})
        self.client.force_authenticate(user=self.bd_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["project_name"], "Inventory Engine")

    def test_lead_create_permissions(self):
        url = reverse("leads:lead-create")
        payload = {
            "project_name": "New App",
            "client_name": "Client",
            "client_email": "client@app.com",
            "client_contact": "123",
            "platform_used": "Direct",
        }

        # Engineer cannot create leads
        self.client.force_authenticate(user=self.eng_user)
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # BD can create lead
        self.client.force_authenticate(user=self.bd_user)
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_phase_create_by_lead_creator(self):
        url = reverse("leads:phase-create", kwargs={"lead_pk": self.lead.pk})
        payload = {
            "type": TestType.TEST_PROJECT,
            "start_date": str(date.today()),
            "due_date": str(date.today() + timedelta(days=4)),
        }

        # Other BD who did not create the lead is forbidden
        self.client.force_authenticate(user=self.other_bd)
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Creator BD succeeds
        self.client.force_authenticate(user=self.bd_user)
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_phase_assign_manager_permissions(self):
        url = reverse("leads:phase-assign-manager", kwargs={"pk": self.phase.pk})

        # Non-creator BD is forbidden
        self.client.force_authenticate(user=self.other_bd)
        response = self.client.post(url, {"manager_id": self.tm_user.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_phase_accept_and_decline_api(self):
        accept_url = reverse("leads:phase-accept", kwargs={"pk": self.phase.pk})

        # Engineer cannot accept phase
        self.client.force_authenticate(user=self.eng_user)
        response = self.client.post(accept_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Assigned TM accepts phase
        self.client.force_authenticate(user=self.tm_user)
        response = self.client.post(accept_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], PhaseStatus.ACCEPTED)

    def test_phase_add_engineer_api(self):
        self.phase.status = PhaseStatus.ACCEPTED
        self.phase.save()

        url = reverse("leads:phase-add-engineer", kwargs={"pk": self.phase.pk})
        self.client.force_authenticate(user=self.tm_user)
        response = self.client.post(url, {"engineer_id": self.eng_user.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_phase_engineer_actions(self):
        pe = PhaseEngineer.objects.create(
            phase=self.phase,
            engineer=self.eng_user,
            assigned_by=self.tm_user,
        )
        accept_url = reverse("leads:phase-engineer-accept", kwargs={"pk": pe.pk})
        done_url = reverse("leads:phase-engineer-done", kwargs={"pk": pe.pk})

        # Engineer accepts
        self.client.force_authenticate(user=self.eng_user)
        response = self.client.post(accept_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Engineer marks done
        response = self.client.post(done_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pe.refresh_from_db()
        self.assertEqual(pe.status, PhaseEngineer.Status.DONE)
