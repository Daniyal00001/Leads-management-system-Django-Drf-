import time
from django.test import TestCase

from apps.accounts.models import User
from apps.leads.models import Lead


class TimeStampedModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="coreuser@example.com",
            password="password123",
        )

    def test_timestamped_fields_auto_populated_and_updated(self):
        lead = Lead.objects.create(
            project_name="Core Test Project",
            client_name="Core Client",
            client_email="core@example.com",
            client_contact="123456",
            platform_used="Upwork",
            created_by=self.user,
        )
        self.assertIsNotNone(lead.created_at)
        self.assertIsNotNone(lead.updated_at)

        created_at_initial = lead.created_at
        updated_at_initial = lead.updated_at

        # Update field and save
        lead.project_name = "Core Test Project Updated"
        lead.save()
        lead.refresh_from_db()

        self.assertEqual(lead.created_at, created_at_initial)
        self.assertGreaterEqual(lead.updated_at, updated_at_initial)
