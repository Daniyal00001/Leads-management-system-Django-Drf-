from datetime import date
from decimal import Decimal
from django.contrib.auth.models import Group
from django.test import TestCase

from apps.accounts.models import User
from apps.accounts.roles import Roles
from apps.commissions.models import CommissionRecord, CommissionRule
from apps.commissions.services import _build_record, calculate_commissions_for_sale
from apps.core.choices import TestType
from apps.leads.choices import PhaseStatus
from apps.leads.models import Lead, Phase, PhaseManagerHistory
from apps.projects.models import Project


class CommissionServicesTests(TestCase):
    def setUp(self):
        self.bd_group, _ = Group.objects.get_or_create(name=Roles.BUSINESS_DEVELOPER)
        self.tm_group, _ = Group.objects.get_or_create(name=Roles.TECHNICAL_MANAGER)

        self.bd_user = User.objects.create_user(
            email="bd@example.com",
            password="password123",
        )
        self.bd_user.groups.add(self.bd_group)

        self.tm_user = User.objects.create_user(
            email="tm@example.com",
            password="password123",
        )
        self.tm_user.groups.add(self.tm_group)

        self.other_tm = User.objects.create_user(
            email="othertm@example.com",
            password="password123",
        )
        self.other_tm.groups.add(self.tm_group)

        self.lead = Lead.objects.create(
            project_name="E-Commerce Store",
            client_name="Client A",
            client_email="clienta@example.com",
            client_contact="12345",
            platform_used="Upwork",
            created_by=self.bd_user,
        )

        self.phase = Phase.objects.create(
            lead=self.lead,
            order=1,
            type=TestType.TEST_PROJECT,
            start_date=date.today(),
            due_date=date.today(),
            current_manager=self.tm_user,
            status=PhaseStatus.ACCEPTED,
            created_by=self.bd_user,
        )

        # Log ACCEPTED in history for self.tm_user
        PhaseManagerHistory.objects.create(
            phase=self.phase,
            manager=self.tm_user,
            action=PhaseManagerHistory.Action.ACCEPTED,
            performed_by=self.tm_user,
        )

        self.project = Project.objects.create(
            lead=self.lead,
            title="E-Commerce Store Project",
            sale_amount=Decimal("10000.00"),
            created_by=self.bd_user,
        )

        # Ensure rules exist (migration 0002 seeds them, or create if missing)
        self.bd_rule, _ = CommissionRule.objects.get_or_create(
            role_name=Roles.BUSINESS_DEVELOPER,
            defaults={"commission_percentage": Decimal("5.00"), "is_active": True},
        )
        self.tm_rule, _ = CommissionRule.objects.get_or_create(
            role_name=Roles.TECHNICAL_MANAGER,
            defaults={"commission_percentage": Decimal("10.00"), "is_active": True},
        )

    def test_calculate_commissions_for_sale_success(self):
        records = calculate_commissions_for_sale(self.project)
        self.assertEqual(len(records), 2)

        bd_record = CommissionRecord.objects.get(
            project=self.project,
            user=self.bd_user,
            role_name=Roles.BUSINESS_DEVELOPER,
        )
        self.assertEqual(bd_record.sale_amount, Decimal("10000.00"))
        self.assertEqual(bd_record.commission_amount, Decimal("500.00"))

        tm_record = CommissionRecord.objects.get(
            project=self.project,
            user=self.tm_user,
            role_name=Roles.TECHNICAL_MANAGER,
        )
        self.assertEqual(tm_record.sale_amount, Decimal("10000.00"))
        self.assertEqual(tm_record.commission_amount, Decimal("1000.00"))

        # The other TM who did not accept a phase should have no commission
        self.assertFalse(
            CommissionRecord.objects.filter(project=self.project, user=self.other_tm).exists()
        )

    def test_calculate_commissions_inactive_rule_skipped(self):
        self.bd_rule.is_active = False
        self.bd_rule.save()

        records = calculate_commissions_for_sale(self.project)
        # Only TM commission created
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].user, self.tm_user)

    def test_build_record_rounding(self):
        rule = CommissionRule(
            role_name=Roles.BUSINESS_DEVELOPER,
            commission_percentage=Decimal("3.33"),
        )
        record = _build_record(
            project=self.project,
            user=self.bd_user,
            rule=rule,
            sale_amount=Decimal("100.00"),
        )
        self.assertEqual(record.commission_amount, Decimal("3.33"))
