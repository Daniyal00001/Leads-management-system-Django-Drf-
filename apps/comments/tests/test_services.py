from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from apps.accounts.models import User
from apps.comments.models import Comment, CommentAttachment
from apps.leads.models import Lead, Phase
from apps.core.choices import TestType
from apps.leads.choices import PhaseStatus
from datetime import date


class CommentServicesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="writer@example.com",
            password="password123",
        )
        self.lead = Lead.objects.create(
            project_name="E-Commerce App",
            client_name="Retailer Inc",
            client_email="retailer@example.com",
            client_contact="987654",
            platform_used="LinkedIn",
            created_by=self.user,
        )
        self.phase = Phase.objects.create(
            lead=self.lead,
            order=1,
            type=TestType.TEST_PROJECT,
            start_date=date.today(),
            due_date=date.today(),
            created_by=self.user,
            status=PhaseStatus.PENDING_ACCEPTANCE,
        )

    def test_comment_generic_resolution_on_lead_and_phase(self):
        lead_ct = ContentType.objects.get_for_model(Lead)
        phase_ct = ContentType.objects.get_for_model(Phase)

        c1 = Comment.objects.create(
            content_type=lead_ct,
            object_id=self.lead.id,
            user=self.user,
            body="First comment on lead",
        )
        c2 = Comment.objects.create(
            content_type=phase_ct,
            object_id=self.phase.id,
            user=self.user,
            body="First comment on phase",
        )

        lead_comments = Comment.objects.filter(content_type=lead_ct, object_id=self.lead.id)
        phase_comments = Comment.objects.filter(content_type=phase_ct, object_id=self.phase.id)

        self.assertEqual(lead_comments.count(), 1)
        self.assertEqual(lead_comments.first(), c1)
        self.assertEqual(phase_comments.count(), 1)
        self.assertEqual(phase_comments.first(), c2)

    def test_comment_attachments_prefetch(self):
        lead_ct = ContentType.objects.get_for_model(Lead)
        comment = Comment.objects.create(
            content_type=lead_ct,
            object_id=self.lead.id,
            user=self.user,
            body="Checking attachments prefetch",
        )
        CommentAttachment.objects.create(comment=comment, image="attachments/photo1.png")
        CommentAttachment.objects.create(comment=comment, image="attachments/photo2.png")

        queried = (
            Comment.objects.filter(id=comment.id)
            .prefetch_related("attachments")
            .first()
        )
        self.assertEqual(queried.attachments.count(), 2)
