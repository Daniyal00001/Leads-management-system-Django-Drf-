from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.comments.models import Comment
from apps.leads.models import Lead


class CommentViewsAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="commenter@example.com",
            password="password123",
            first_name="Alice",
            last_name="Smith",
        )
        self.lead = Lead.objects.create(
            project_name="Web Redesign",
            client_name="Global Corp",
            client_email="client@example.com",
            client_contact="111-222",
            platform_used="Direct",
            created_by=self.user,
        )
        self.lead_ct = ContentType.objects.get_for_model(Lead)
        self.list_url = reverse("comments:comment-list")
        self.create_url = reverse("comments:comment-create")

    def test_comment_list_unauthenticated(self):
        response = self.client.get(self.list_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_comment_list_filtering(self):
        Comment.objects.create(
            content_type=self.lead_ct,
            object_id=self.lead.id,
            user=self.user,
            body="First comment for lead",
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            self.list_url,
            {"model_name": "lead", "object_id": self.lead.id},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["body"], "First comment for lead")
        self.assertEqual(results[0]["user"]["email"], "commenter@example.com")


    def test_comment_create_unauthenticated(self):
        response = self.client.post(self.create_url, {"body": "Test comment"})
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_comment_create_non_existent_target_object(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "model_name": "lead",
            "object_id": 99999,
            "body": "Comment for missing lead",
        }
        response = self.client.post(self.create_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_comment_create_success_without_images(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "model_name": "lead",
            "object_id": self.lead.id,
            "body": "A valid comment body",
        }
        response = self.client.post(self.create_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["body"], "A valid comment body")
        self.assertEqual(Comment.objects.filter(object_id=self.lead.id).count(), 1)

    def test_comment_create_success_with_image_attachment(self):
        self.client.force_authenticate(user=self.user)
        fake_image = SimpleUploadedFile(
            name="test.gif",
            content=b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x05\x04\x04\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b",
            content_type="image/gif",
        )
        payload = {
            "model_name": "lead",
            "object_id": self.lead.id,
            "body": "Comment with file attached",
            "images": [fake_image],
        }
        response = self.client.post(self.create_url, payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data["attachments"]), 1)
