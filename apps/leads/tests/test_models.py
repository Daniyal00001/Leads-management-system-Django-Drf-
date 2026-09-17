from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from apps.accounts.models import User
from apps.core.choices import TestType

# TestType.TEST_PROJECT and TestType.INTERVIEW are the valid choices
from apps.leads.choices import LeadStatus, PhaseStatus
from apps.leads.models import (
    Lead,
    Phase,
    PhaseEngineer,
    PhaseEngineerHistory,
    PhaseManagerHistory,
)


class LeadModelsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="leadowner@example.com",
            password="password123",
        )
        self.manager = User.objects.create_user(
            email="leadmanager@example.com",
            password="password123",
        )
        self.engineer = User.objects.create_user(
            email="leadengineer@example.com",
            password="password123",
        )
        self.lead = Lead.objects.create(
            project_name="AI SaaS Platform",
            client_name="Cloud Corp",
            client_email="cloud@example.com",
            client_contact="123456",
            platform_used="Upwork",
            created_by=self.user,
        )

    def test_lead_str(self):
        self.assertEqual(str(self.lead), "AI SaaS Platform (Cloud Corp)")

    def test_all_phases_completed_zero_phases(self):
        self.assertFalse(self.lead.all_phases_completed)

    def test_all_phases_completed_partially_completed(self):
        p1 = Phase.objects.create(
            lead=self.lead,
            order=1,
            type=TestType.TEST_PROJECT,
            start_date=date.today(),
            due_date=date.today() + timedelta(days=5),
            status=PhaseStatus.COMPLETED,
            created_by=self.user,
        )
        p2 = Phase.objects.create(
            lead=self.lead,
            order=2,
            type=TestType.INTERVIEW,
            start_date=date.today(),
            due_date=date.today() + timedelta(days=5),
            status=PhaseStatus.IN_PROGRESS,
            created_by=self.user,
        )
        self.assertFalse(self.lead.all_phases_completed)

        # Mark second completed
        p2.status = PhaseStatus.COMPLETED
        p2.save()
        self.assertTrue(self.lead.all_phases_completed)

    def test_phase_str(self):
        phase = Phase.objects.create(
            lead=self.lead,
            order=1,
            type=TestType.TEST_PROJECT,
            start_date=date.today(),
            due_date=date.today() + timedelta(days=3),
            created_by=self.user,
        )
        self.assertEqual(str(phase), "Phase 1 - AI SaaS Platform")

    def test_phase_clean_due_date_before_start_date(self):
        phase = Phase(
            lead=self.lead,
            order=1,
            type=TestType.TEST_PROJECT,
            start_date=date.today(),
            due_date=date.today() - timedelta(days=1),
            created_by=self.user,
        )
        with self.assertRaises(ValidationError):
            phase.clean()

    def test_phase_unique_together_lead_order(self):
        Phase.objects.create(
            lead=self.lead,
            order=1,
            type=TestType.TEST_PROJECT,
            start_date=date.today(),
            due_date=date.today() + timedelta(days=3),
            created_by=self.user,
        )
        with self.assertRaises(IntegrityError):
            Phase.objects.create(
                lead=self.lead,
                order=1,
                type=TestType.INTERVIEW,
                start_date=date.today(),
                due_date=date.today() + timedelta(days=3),
                created_by=self.user,
            )

    def test_phase_manager_history_model(self):
        phase = Phase.objects.create(
            lead=self.lead,
            order=1,
            type=TestType.TEST_PROJECT,
            start_date=date.today(),
            due_date=date.today() + timedelta(days=3),
            created_by=self.user,
        )
        history = PhaseManagerHistory.objects.create(
            phase=phase,
            manager=self.manager,
            action=PhaseManagerHistory.Action.ASSIGNED,
            performed_by=self.user,
        )
        self.assertEqual(
            str(history),
            f"{self.manager} {PhaseManagerHistory.Action.ASSIGNED} on {phase}",
        )

    def test_phase_engineer_and_history_models(self):
        phase = Phase.objects.create(
            lead=self.lead,
            order=1,
            type=TestType.TEST_PROJECT,
            start_date=date.today(),
            due_date=date.today() + timedelta(days=3),
            created_by=self.user,
        )
        pe = PhaseEngineer.objects.create(
            phase=phase,
            engineer=self.engineer,
            assigned_by=self.manager,
        )
        self.assertEqual(str(pe), f"{self.engineer} on {phase}")

        # Unique together on (phase, engineer)
        with self.assertRaises(IntegrityError):
            PhaseEngineer.objects.create(
                phase=phase,
                engineer=self.engineer,
                assigned_by=self.manager,
            )

        history = PhaseEngineerHistory.objects.create(
            phase=phase,
            engineer=self.engineer,
            action=PhaseEngineerHistory.Action.ACCEPTED,
            performed_by=self.engineer,
        )
        self.assertEqual(
            str(history),
            f"{self.engineer} {PhaseEngineerHistory.Action.ACCEPTED} on {phase}",
        )
