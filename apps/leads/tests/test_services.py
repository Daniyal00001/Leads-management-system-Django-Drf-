from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from apps.accounts.models import User
from apps.accounts.roles import Roles
from apps.commissions.models import CommissionRule
from apps.core.choices import TestType
from apps.leads.choices import LeadStatus, PhaseStatus
from apps.leads.models import Lead, Phase, PhaseEngineer, PhaseManagerHistory
from apps.leads import services


class LeadServicesTests(TestCase):
    def setUp(self):
        self.bd_group, _ = Group.objects.get_or_create(name=Roles.BUSINESS_DEVELOPER)
        self.tm_group, _ = Group.objects.get_or_create(name=Roles.TECHNICAL_MANAGER)
        self.eng_group, _ = Group.objects.get_or_create(name=Roles.ENGINEER)

        self.bd_user = User.objects.create_user(email="bd@service.com", password="pw")
        self.bd_user.groups.add(self.bd_group)

        self.tm_user = User.objects.create_user(email="tm@service.com", password="pw")
        self.tm_user.groups.add(self.tm_group)

        self.eng_user = User.objects.create_user(email="eng@service.com", password="pw")
        self.eng_user.groups.add(self.eng_group)

        CommissionRule.objects.get_or_create(
            role_name=Roles.BUSINESS_DEVELOPER,
            defaults={"commission_percentage": Decimal("5.00"), "is_active": True},
        )
        CommissionRule.objects.get_or_create(
            role_name=Roles.TECHNICAL_MANAGER,
            defaults={"commission_percentage": Decimal("10.00"), "is_active": True},
        )

        self.lead = services.create_lead(
            {
                "project_name": "Healthcare Portal",
                "client_name": "Med Corp",
                "client_email": "med@corp.com",
                "client_contact": "555-4321",
                "platform_used": "Referral",
            },
            created_by=self.bd_user,
        )

    def test_create_lead_success(self):
        self.assertEqual(self.lead.created_by, self.bd_user)
        self.assertEqual(self.lead.status, LeadStatus.OPEN)

    def test_create_phase_success(self):
        phase = services.create_phase(
            self.lead,
            {
                "type": TestType.TEST_PROJECT,
                "start_date": date.today(),
                "due_date": date.today() + timedelta(days=7),
            },
            created_by=self.bd_user,
        )
        self.assertEqual(phase.order, 1)
        self.assertEqual(phase.status, PhaseStatus.PENDING_ACCEPTANCE)

    def test_assign_and_accept_phase(self):
        phase = services.create_phase(
            self.lead,
            {
                "type": TestType.TEST_PROJECT,
                "start_date": date.today(),
                "due_date": date.today() + timedelta(days=7),
            },
            created_by=self.bd_user,
        )
        services.assign_phase_manager(phase, manager=self.tm_user, performed_by=self.bd_user)
        self.assertEqual(phase.current_manager, self.tm_user)
        self.assertEqual(phase.status, PhaseStatus.PENDING_ACCEPTANCE)

        # Non-assigned manager cannot accept
        other_user = User.objects.create_user(email="other@service.com", password="pw")
        with self.assertRaises(PermissionDenied):
            services.accept_phase(phase, manager=other_user)

        # Assigned manager accepts
        services.accept_phase(phase, manager=self.tm_user)
        phase.refresh_from_db()
        self.assertEqual(phase.status, PhaseStatus.ACCEPTED)

    def test_decline_phase(self):
        phase = services.create_phase(
            self.lead,
            {
                "type": TestType.TEST_PROJECT,
                "start_date": date.today(),
                "due_date": date.today() + timedelta(days=7),
            },
            created_by=self.bd_user,
        )
        services.assign_phase_manager(phase, manager=self.tm_user, performed_by=self.bd_user)
        services.decline_phase(phase, manager=self.tm_user, comment="Too busy")
        phase.refresh_from_db()
        self.assertEqual(phase.status, PhaseStatus.PENDING_REASSIGNMENT)
        self.assertIsNone(phase.current_manager)

    def test_engineer_assignment_lifecycle(self):
        phase = services.create_phase(
            self.lead,
            {
                "type": TestType.TEST_PROJECT,
                "start_date": date.today(),
                "due_date": date.today() + timedelta(days=7),
            },
            created_by=self.bd_user,
        )
        services.assign_phase_manager(phase, manager=self.tm_user, performed_by=self.bd_user)
        services.accept_phase(phase, manager=self.tm_user)

        # Add engineer
        assignment = services.add_engineer_to_phase(
            phase, engineer=self.eng_user, assigned_by=self.tm_user
        )
        phase.refresh_from_db()
        self.assertEqual(phase.status, PhaseStatus.IN_PROGRESS)
        self.assertEqual(assignment.status, PhaseEngineer.Status.PENDING)

        # Engineer accepts
        services.accept_engineer_assignment(assignment, engineer=self.eng_user)
        assignment.refresh_from_db()
        self.assertEqual(assignment.status, PhaseEngineer.Status.ACCEPTED)

        # Engineer marks done
        services.mark_engineer_done(assignment, engineer=self.eng_user)
        assignment.refresh_from_db()
        self.assertEqual(assignment.status, PhaseEngineer.Status.DONE)

    def test_complete_phase(self):
        phase = services.create_phase(
            self.lead,
            {
                "type": TestType.TEST_PROJECT,
                "start_date": date.today(),
                "due_date": date.today() + timedelta(days=7),
            },
            created_by=self.bd_user,
        )
        services.assign_phase_manager(phase, manager=self.tm_user, performed_by=self.bd_user)
        services.accept_phase(phase, manager=self.tm_user)

        services.complete_phase(phase, completed_by=self.tm_user)
        phase.refresh_from_db()
        self.assertEqual(phase.status, PhaseStatus.COMPLETED)
        self.assertIsNotNone(phase.completed_at)
        self.assertEqual(phase.completed_by, self.tm_user)

    def test_mark_lead_as_sale_and_no_sale(self):
        phase = services.create_phase(
            self.lead,
            {
                "type": TestType.TEST_PROJECT,
                "start_date": date.today(),
                "due_date": date.today() + timedelta(days=7),
            },
            created_by=self.bd_user,
        )
        # Cannot mark as sale if phases incomplete
        with self.assertRaises(ValidationError):
            services.mark_lead_as_sale(
                self.lead,
                decided_by=self.bd_user,
                sale_amount=Decimal("15000.00"),
                manager_id=self.tm_user.id,
            )

        # Complete phase
        services.assign_phase_manager(phase, manager=self.tm_user, performed_by=self.bd_user)
        services.accept_phase(phase, manager=self.tm_user)
        services.complete_phase(phase, completed_by=self.tm_user)

        # Mark as sale
        project = services.mark_lead_as_sale(
            self.lead,
            decided_by=self.bd_user,
            sale_amount=Decimal("15000.00"),
            manager_id=self.tm_user.id,
        )
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.status, LeadStatus.SALE)
        self.assertEqual(project.sale_amount, Decimal("15000.00"))
        self.assertEqual(project.manager, self.tm_user)
