from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.notifications.models import Notification, NotificationType
from apps.notifications.views import _notification_url
from apps.leads.models import Lead


class NotificationViewsAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="recipient@example.com",
            password="password123",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="password123",
        )
        self.notif1 = Notification.objects.create(
            user=self.user,
            type=NotificationType.LEAD_CREATED,
            message="Lead 1 created",
        )
        self.notif2 = Notification.objects.create(
            user=self.user,
            type=NotificationType.PHASE_ASSIGNED,
            message="Phase assigned",
        )
        self.other_notif = Notification.objects.create(
            user=self.other_user,
            type=NotificationType.LEAD_CREATED,
            message="Other user notification",
        )

        self.list_url = reverse("notifications:notification-list")
        self.read_url = reverse("notifications:notification-read", kwargs={"pk": self.notif1.pk})
        self.read_all_url = reverse("notifications:notification-read-all")
        self.page_url = reverse("notifications:notification-page-list")

    def test_notification_list_unauthenticated(self):
        response = self.client.get(self.list_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_notification_list_shows_only_user_notifications(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"] if "results" in response.data else response.data
        self.assertEqual(len(results), 2)

    def test_mark_read_single_notification(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.read_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notif1.refresh_from_db()
        self.assertTrue(self.notif1.is_read)

    def test_mark_read_all_notifications(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.read_all_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Notification.objects.filter(user=self.user, is_read=False).count(),
            0,
        )

    def test_notification_list_page(self):
        self.client.force_login(self.user)
        response = self.client.get(self.page_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, "notifications/notification_list.html")

    def test_notification_url_helper(self):
        lead = Lead.objects.create(
            project_name="URL Helper Test",
            client_name="Test",
            client_email="t@t.com",
            client_contact="123",
            platform_used="Direct",
            created_by=self.user,
        )
        notif = Notification.objects.create(
            user=self.user,
            type=NotificationType.LEAD_CREATED,
            content_object=lead,
            message="Lead url helper test",
        )
        url = _notification_url(notif)
        self.assertEqual(url, f"/leads/{lead.id}/")
