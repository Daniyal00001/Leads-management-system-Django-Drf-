from datetime import date, timedelta
from decimal import Decimal
from django.core import mail
from django.contrib.auth.models import Group
from django.test import TestCase

from apps.accounts.models import User
from apps.accounts.roles import Roles
from apps.core.choices import TestType
from apps.leads.models import Lead, Phase
from apps.notifications.models import Notification, NotificationType
from apps.notifications import services
from apps.projects.models import Project


class NotificationServicesTests(TestCase):
    def setUp(self):
        self.admin_group, _ = Group.objects.get_or_create(name=Roles.SUPER_ADMIN)
        self.bd_group, _ = Group.objects.get_or_create(name=Roles.BUSINESS_DEVELOPER)
        self.tm_group, _ = Group.objects.get_or_create(name=Roles.TECHNICAL_MANAGER)
        self.eng_group, _ = Group.objects.get_or_create(name=Roles.ENGINEER)

        self.admin = User.objects.create_superuser(email="admin@notify.com", password="pw")
        self.admin.groups.add(self.admin_group)

        self.bd_user = User.objects.create_user(email="bd@notify.com", password="pw")
        self.bd_user.groups.add(self.bd_group)

        self.tm_user = User.objects.create_user(email="tm@notify.com", password="pw")
        self.tm_user.groups.add(self.tm_group)

        self.eng_user = User.objects.create_user(email="eng@notify.com", password="pw")
        self.eng_user.groups.add(self.eng_group)

        self.lead = Lead.objects.create(
            project_name="E-Commerce Store",
            client_name="Client Notif",
            client_email="client@notif.com",
            client_contact="12345",
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
        )

    def test_notify_admins(self):
        services.notify_admins(
            type=NotificationType.LEAD_CREATED,
            message="New Lead Alert",
            exclude_user=self.bd_user,
        )
        notifs = Notification.objects.filter(user=self.admin)
        self.assertEqual(notifs.count(), 1)
        self.assertEqual(notifs.first().message, "New Lead Alert")

    def test_notify_phase_assigned_creates_notification_and_email(self):
        mail.outbox.clear()
        services.notify_phase_assigned(self.phase, self.tm_user)

        self.assertTrue(
            Notification.objects.filter(
                user=self.tm_user,
                type=NotificationType.PHASE_ASSIGNED,
            ).exists()
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.tm_user.email, mail.outbox[0].to)

    def test_notify_phase_accepted(self):
        services.notify_phase_accepted(self.phase, self.tm_user)
        self.assertTrue(
            Notification.objects.filter(
                user=self.bd_user,
                type=NotificationType.PHASE_ACCEPTED,
            ).exists()
        )

    def test_notify_lead_sale(self):
        project = Project.objects.create(
            lead=self.lead,
            title="E-Commerce Store",
            sale_amount=Decimal("10000.00"),
            created_by=self.bd_user,
            manager=self.tm_user,
        )
        services.notify_lead_sale(self.lead, project, decided_by=self.bd_user)

        # TM should get project assigned notification
        self.assertTrue(
            Notification.objects.filter(
                user=self.tm_user,
                type=NotificationType.PROJECT_ASSIGNED,
            ).exists()
        )
