from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.core.choices import TestType
from .choices import LeadStatus, PhaseStatus


class Lead(TimeStampedModel):
    project_name = models.CharField(max_length=255)
    client_name = models.CharField(max_length=255)
    client_address = models.TextField(blank=True)
    client_email = models.EmailField()
    client_contact = models.CharField(max_length=50)
    platform_used = models.CharField(max_length=100)
    test_type = models.CharField(max_length=20, choices=TestType.choices)
    comments_note = models.TextField(blank=True)  

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="leads_created",
    )

    status = models.CharField(
        max_length=20,
        choices=LeadStatus.choices,
        default=LeadStatus.OPEN,
    )
    sale_decided_at = models.DateTimeField(null=True, blank=True)
    sale_decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="leads_decided",
    )

    def __str__(self):
        return f"{self.project_name} ({self.client_name})"

    @property
    def all_phases_completed(self):
        
        #  BD can only transition lead to when
        # sale/no_sale once ALL phases are completed
    
        phases = self.phases.all()
        if not phases.exists():
            return False  # a lead with zero phases shouldn't auto-qualify
        return not phases.exclude(status=PhaseStatus.COMPLETED).exists()


# ========================================================================

class Phase(TimeStampedModel):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="phases")
    order = models.PositiveIntegerField()  # dynamic ordering.....order = is phase ka sequence or position kya hai?

    type = models.CharField(max_length=20, choices=TestType.choices)

    current_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="phases_managed",
    )

    status = models.CharField(
        max_length=25,
        choices=PhaseStatus.choices,
        default=PhaseStatus.PENDING_ACCEPTANCE,
    )

    start_date = models.DateField()
    due_date = models.DateField()

    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="phases_completed",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="phases_created",
    )

    class Meta:
        ordering = ["lead", "order"]
        unique_together = [("lead", "order")]

    def __str__(self):
        return f"Phase {self.order} - {self.lead.project_name}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.due_date < self.start_date:
            raise ValidationError("due_date cannot be before start_date")


            # ==================================================================


class PhaseManagerHistory(TimeStampedModel):
    class Action(models.TextChoices):
        ASSIGNED = "assigned", "Assigned"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"

    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name="manager_history")
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="phase_manager_history_entries",
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    comment = models.TextField(blank=True)

    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="phase_manager_actions_performed",
        help_text="Who triggered this action — BD (assigned) or the manager themself (accepted/declined)",
    )
    action_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-action_at"]
        verbose_name_plural = "Phase manager histories"

    def __str__(self):
        return f"{self.manager} {self.action} on {self.phase}"



 # ============================================================================


class PhaseEngineer(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        DONE = "done", "Done"

    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name="phase_engineers")
    engineer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="phase_assignments",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="engineers_assigned",
        help_text="The technical manager who added this engineer to the phase",
    )

    class Meta:
        unique_together = [("phase", "engineer")]

    def __str__(self):
        return f"{self.engineer} on {self.phase}"



        # ================================================================================


class PhaseEngineerHistory(TimeStampedModel):
    class Action(models.TextChoices):
        ASSIGNED = "assigned", "Assigned"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        MARKED_DONE = "marked_done", "Marked Done"

    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name="engineer_history")
    engineer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="phase_engineer_history_entries",
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    comment = models.TextField(blank=True)

    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="phase_engineer_actions_performed", 
        # help_text = "The user who performed this action ----manager or engnierr"
    )
    action_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-action_at"]
        verbose_name_plural = "Phase engineer histories"

    def __str__(self):
        return f"{self.engineer} {self.action} on {self.phase}"