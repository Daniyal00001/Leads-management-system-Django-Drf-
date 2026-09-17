from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.accounts.models import User
from apps.comments.models import Comment, CommentAttachment
from apps.leads.models import Lead


class CommentModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="author@example.com",
            password="password123",
        )
        self.lead = Lead.objects.create(
            project_name="AI Dashboard",
            client_name="Acme Corp",
            client_email="acme@example.com",
            client_contact="12345",
            platform_used="Upwork",
            created_by=self.user,
        )
        self.lead_ct = ContentType.objects.get_for_model(Lead)

    def test_create_comment_with_generic_relation(self):
        comment = Comment.objects.create(
            content_type=self.lead_ct,
            object_id=self.lead.id,
            user=self.user,
            body="This is an initial lead inquiry comment.",
        )
        self.assertEqual(comment.content_object, self.lead)
        self.assertEqual(
            str(comment),
            f"Comment by {self.user} on {self.lead}",
        )
        self.assertIsNotNone(comment.created_at)

    def test_comment_attachment_creation_and_str(self):
        comment = Comment.objects.create(
            content_type=self.lead_ct,
            object_id=self.lead.id,
            user=self.user,
            body="Comment with an attachment.",
        )
        fake_image = SimpleUploadedFile(
            name="test_image.png",
            content=b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x05\x04\x04\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b",
            content_type="image/gif",
        )
        attachment = CommentAttachment.objects.create(
            comment=comment,
            image=fake_image,
        )
        self.assertEqual(attachment.comment, comment)
        self.assertEqual(str(attachment), f"Attachment for comment #{comment.id}")
