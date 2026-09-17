from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.projects.models import Project


class CommissionRule(TimeStampedModel):
    """
       commission percentage 

        Business Developer -> 5%
        Technical Manager  -> 10%

    The percentage is calculated against the project's sale amount.
    """

    role_name = models.CharField(
        max_length=100,
        unique=True,
    )

    commission_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["role_name"]

    def __str__(self):
        return f"{self.role_name}: {self.commission_percentage}%"


class CommissionRecord(TimeStampedModel):
    """
    Stores the actual commission earned by a user for a project sale.
    """

    project = models.ForeignKey(
        Project,
        on_delete=models.PROTECT,
        related_name="commission_records",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="commission_records",
    )

    role_name = models.CharField(
        max_length=100,
    )

    sale_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    commission_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    commission_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["project", "user", "role_name"],
                name="unique_project_user_role_commission",
            )
        ]

    def __str__(self):
        return (
            f"{self.user} - {self.role_name} - "
            f"{self.commission_amount} on {self.project}"
        )