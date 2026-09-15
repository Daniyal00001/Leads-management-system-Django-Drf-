from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.core.models import TimeStampedModel


class NotificationType(models.TextChoices):
    PHASE_ASSIGNED = "phase_assigned", "Phase Assigned"
    PHASE_ACCEPTED = "phase_accepted", "Phase Accepted"
    PHASE_DECLINED = "phase_declined", "Phase Declined"
    PHASE_COMPLETED = "phase_completed", "Phase Completed"
    ENGINEER_ASSIGNED = "engineer_assigned", "Engineer Assigned"
    LEAD_SALE = "lead_sale", "Lead Marked as Sale"
    PROJECT_ASSIGNED = "project_assigned", "Project Assigned"


class Notification(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(max_length=30, choices=NotificationType.choices)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

    message = models.TextField()
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
        ]

    def __str__(self):
        return f"[{self.type}] to {self.user}"