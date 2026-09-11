from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.leads.models import Lead


class ProjectStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    ON_HOLD = "on_hold", "On Hold"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class Project(TimeStampedModel):
    lead = models.OneToOneField(
        Lead,
        on_delete=models.PROTECT,
        related_name="project",
    )
    title = models.CharField(max_length=255)

    sale_amount = models.DecimalField(max_digits=12, decimal_places=2) 

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="projects_created",
    )

    status = models.CharField(
        max_length=20,
        choices=ProjectStatus.choices,
        default=ProjectStatus.ACTIVE,
    )

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):   
        if not self.title:
            self.title = self.lead.project_name
        super().save(*args, **kwargs)


# ============================================================================
class ProjectManager(TimeStampedModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="project_managers")
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="projects_managed",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="project_managers_assigned",
    )

    class Meta:
        unique_together = [("project", "manager")]

    def __str__(self):
        return f"{self.manager} → {self.project}" 