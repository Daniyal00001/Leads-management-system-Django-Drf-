from decimal import Decimal
from django.db import IntegrityError
from django.test import TestCase

from apps.accounts.models import User
from apps.accounts.roles import Roles
from apps.commissions.models import CommissionRecord, CommissionRule
from apps.leads.models import Lead
from apps.projects.models import Project


class CommissionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="agent@example.com",
            password="password123",
        )
        self.lead = Lead.objects.create(
            project_name="Mobile Banking",
            client_name="Fintech Corp",
            client_email="fintech@example.com",
            client_contact="98765",
            platform_used="Direct",
            created_by=self.user,
        )
        self.project = Project.objects.create(
            lead=self.lead,
            title="Mobile Banking App",
            sale_amount=Decimal("50000.00"),
            created_by=self.user,
        )
        self.rule = CommissionRule.objects.create(
            role_name=Roles.BUSINESS_DEVELOPER,
            commission_percentage=Decimal("5.00"),
            is_active=True,
        )

    def test_commission_rule_str(self):
        self.assertEqual(str(self.rule), f"{Roles.BUSINESS_DEVELOPER}: 5.00%")

    def test_commission_record_str(self):
        record = CommissionRecord.objects.create(
            project=self.project,
            user=self.user,
            role_name=Roles.BUSINESS_DEVELOPER,
            sale_amount=Decimal("50000.00"),
            commission_percentage=Decimal("5.00"),
            commission_amount=Decimal("2500.00"),
        )
        expected_str = f"{self.user} - {Roles.BUSINESS_DEVELOPER} - 2500.00 on {self.project}"
        self.assertEqual(str(record), expected_str)

    def test_commission_record_unique_constraint(self):
        CommissionRecord.objects.create(
            project=self.project,
            user=self.user,
            role_name=Roles.BUSINESS_DEVELOPER,
            sale_amount=Decimal("50000.00"),
            commission_percentage=Decimal("5.00"),
            commission_amount=Decimal("2500.00"),
        )
        with self.assertRaises(IntegrityError):
            CommissionRecord.objects.create(
                project=self.project,
                user=self.user,
                role_name=Roles.BUSINESS_DEVELOPER,
                sale_amount=Decimal("50000.00"),
                commission_percentage=Decimal("5.00"),
                commission_amount=Decimal("2500.00"),
            )
