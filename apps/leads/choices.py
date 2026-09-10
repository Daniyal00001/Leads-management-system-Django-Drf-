from django.db import models


class LeadStatus(models.TextChoices):
    OPEN = "open", "Open"
    SALE = "sale", "Sale"
    NO_SALE = "no_sale", "No Sale"


class PhaseStatus(models.TextChoices):
    PENDING_ACCEPTANCE = "pending_acceptance", "Pending Acceptance"
    ACCEPTED = "accepted", "Accepted"
    DECLINED = "declined", "Declined"
    PENDING_REASSIGNMENT = "pending_reassignment", "Pending Reassignment"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"