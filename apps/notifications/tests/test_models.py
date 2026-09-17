from django.test import TestCase

from apps.accounts.models import User
from apps.notifications.models import Notification, NotificationType


class NotificationModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="notifuser@example.com",
            password="password123",
        )

    def test_notification_creation_and_defaults(self):
        notif = Notification.objects.create(
            user=self.user,
            type=NotificationType.LEAD_CREATED,
            message="A new lead has arrived.",
        )
        self.assertFalse(notif.is_read)
        self.assertEqual(str(notif), f"[{NotificationType.LEAD_CREATED}] to {self.user}")

    def test_notification_ordering(self):
        n1 = Notification.objects.create(
            user=self.user,
            type=NotificationType.PHASE_ASSIGNED,
            message="Phase 1 assigned",
        )
        n2 = Notification.objects.create(
            user=self.user,
            type=NotificationType.PHASE_ACCEPTED,
            message="Phase 1 accepted",
        )
        notifications = list(Notification.objects.filter(user=self.user))
        self.assertEqual(notifications[0], n2)
        self.assertEqual(notifications[1], n1)
