from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from .choices import PhaseStatus, LeadStatus
from .models import Lead, Phase, PhaseManagerHistory, PhaseEngineer, PhaseEngineerHistory


def assign_phase_manager(phase, manager, performed_by):
    if phase.status in [PhaseStatus.ACCEPTED, PhaseStatus.IN_PROGRESS, PhaseStatus.COMPLETED]:
        raise ValidationError("Cannot reassign manager once the phase has been accepted or completed.")

    # BD assigns (or re-assigns after a decline) a manager to a phase.
    # Triggers pending_acceptance state + history entry + notification (via signal).
    
    with transaction.atomic():
        phase.current_manager = manager
        phase.status = PhaseStatus.PENDING_ACCEPTANCE
        phase.save(update_fields=["current_manager", "status", "updated_at"])

        PhaseManagerHistory.objects.create(
            phase=phase,
            manager=manager,
            action=PhaseManagerHistory.Action.ASSIGNED,
            performed_by=performed_by,
        )
    return phase


def accept_phase(phase, manager):
    if phase.current_manager_id != manager.id:
        raise PermissionDenied("Only the assigned manager can accept this phase.")
    if phase.status != PhaseStatus.PENDING_ACCEPTANCE:
        raise ValidationError("Phase is not pending acceptance.")

    with transaction.atomic():
        phase.status = PhaseStatus.ACCEPTED
        phase.save(update_fields=["status", "updated_at"])

        PhaseManagerHistory.objects.create(
            phase=phase,
            manager=manager,
            action=PhaseManagerHistory.Action.ACCEPTED,
            performed_by=manager,
        )
    return phase


def decline_phase(phase, manager, comment=""):
    if phase.current_manager_id != manager.id:
        raise PermissionDenied("Only the assigned manager can decline this phase.")
    if phase.status != PhaseStatus.PENDING_ACCEPTANCE:
        raise ValidationError("Phase is not pending acceptance.")

    with transaction.atomic():
        phase.status = PhaseStatus.PENDING_REASSIGNMENT
        phase.current_manager = None
        phase.save(update_fields=["status", "current_manager", "updated_at"])

        PhaseManagerHistory.objects.create(
            phase=phase,
            manager=manager,
            action=PhaseManagerHistory.Action.DECLINED,
            comment=comment,
            performed_by=manager,
        )
    return phase


def add_engineer_to_phase(phase, engineer, assigned_by):
    if phase.status not in [PhaseStatus.ACCEPTED, PhaseStatus.IN_PROGRESS]:
        raise ValidationError("Manager can only add engineers to an accepted phase.")

    with transaction.atomic():
        phase_engineer, created = PhaseEngineer.objects.get_or_create(
            phase=phase,
            engineer=engineer,
            defaults={"assigned_by": assigned_by},
        )
        if not created:
            raise ValidationError("Engineer is already assigned to this phase.")

        PhaseEngineerHistory.objects.create(
            phase=phase,
            engineer=engineer,
            action=PhaseEngineerHistory.Action.ASSIGNED,
            performed_by=assigned_by,
        )

        if phase.status == PhaseStatus.ACCEPTED:
            phase.status = PhaseStatus.IN_PROGRESS
            phase.save(update_fields=["status", "updated_at"])

    from apps.notifications.services import notify_engineer_assigned

    notify_engineer_assigned(phase, engineer)
    return phase_engineer


def accept_engineer_assignment(phase_engineer, engineer):
    if phase_engineer.engineer_id != engineer.id:
        raise PermissionDenied("Only the assigned engineer can accept this work.")
    if phase_engineer.status != PhaseEngineer.Status.PENDING:
        raise ValidationError("This assignment is not pending.")

    with transaction.atomic():
        phase_engineer.status = PhaseEngineer.Status.ACCEPTED
        phase_engineer.save(update_fields=["status", "updated_at"])

        PhaseEngineerHistory.objects.create(
            phase=phase_engineer.phase,
            engineer=engineer,
            action=PhaseEngineerHistory.Action.ACCEPTED,
            performed_by=engineer,
        )
    return phase_engineer


def decline_engineer_assignment(phase_engineer, engineer, comment=""):
    if phase_engineer.engineer_id != engineer.id:
        raise PermissionDenied("Only the assigned engineer can decline this work.")
    if phase_engineer.status != PhaseEngineer.Status.PENDING:
        raise ValidationError("This assignment is not pending.")

    with transaction.atomic():
        phase_engineer.status = PhaseEngineer.Status.DECLINED
        phase_engineer.save(update_fields=["status", "updated_at"])

        PhaseEngineerHistory.objects.create(
            phase=phase_engineer.phase,
            engineer=engineer,
            action=PhaseEngineerHistory.Action.DECLINED,
            comment=comment,
            performed_by=engineer,
        )
    return phase_engineer


def mark_engineer_done(phase_engineer, engineer):
    if phase_engineer.engineer_id != engineer.id:
        raise PermissionDenied("Only the assigned engineer can mark this work done.")
    if phase_engineer.status != PhaseEngineer.Status.ACCEPTED:
        raise ValidationError("Only accepted work can be marked done.")

    with transaction.atomic():
        phase_engineer.status = PhaseEngineer.Status.DONE
        phase_engineer.save(update_fields=["status", "updated_at"])

        PhaseEngineerHistory.objects.create(
            phase=phase_engineer.phase,
            engineer=engineer,
            action=PhaseEngineerHistory.Action.MARKED_DONE,
            performed_by=engineer,
        )
    return phase_engineer


def complete_phase(phase, completed_by):
     # Manager OR BD can mark complete 
    if phase.status == PhaseStatus.COMPLETED:
        raise ValidationError("Phase is already completed.")
    if phase.status not in [PhaseStatus.ACCEPTED, PhaseStatus.IN_PROGRESS]:
        raise ValidationError("Only an accepted/in-progress phase can be completed.")

    with transaction.atomic():
        phase.status = PhaseStatus.COMPLETED
        phase.completed_at = timezone.now()
        phase.completed_by = completed_by
        phase.save(update_fields=["status", "completed_at", "completed_by", "updated_at"])

    return phase

def mark_lead_as_sale(lead, decided_by, sale_amount, manager_id=None):
    from apps.projects.models import Project
    from apps.commissions.services import calculate_commissions_for_sale

    if not lead.all_phases_completed:
        raise ValidationError("All phases must be completed before marking as sale.")
    if lead.status != LeadStatus.OPEN:
        raise ValidationError("Lead has already been decided.")

    # Resolve the chosen project manager (required)
    project_manager = None
    if manager_id:
        from apps.accounts.models import User
        try:
            project_manager = User.objects.get(pk=manager_id)
        except User.DoesNotExist:
            raise ValidationError("Selected manager does not exist.")

    with transaction.atomic():
        lead.status = LeadStatus.SALE
        lead.sale_decided_at = timezone.now()
        lead.sale_decided_by = decided_by
        lead.save(update_fields=["status", "sale_decided_at", "sale_decided_by", "updated_at"])

        project = Project.objects.create(
            lead=lead,
            title=lead.project_name,
            sale_amount=sale_amount,
            created_by=decided_by,
            manager=project_manager,
        )

        calculate_commissions_for_sale(project)

    return project

def mark_lead_as_no_sale(lead, decided_by):
    if not lead.all_phases_completed:
        raise ValidationError("All phases must be completed before deciding.")
    if lead.status != LeadStatus.OPEN:
        raise ValidationError("Lead has already been decided.")

    with transaction.atomic():
        lead.status = LeadStatus.NO_SALE
        lead.sale_decided_at = timezone.now()
        lead.sale_decided_by = decided_by
        lead.save(update_fields=["status", "sale_decided_at", "sale_decided_by", "updated_at"])

    return lead


   # ========================================
   # =========================================

def create_lead(validated_data, created_by):
    with transaction.atomic():
        lead = Lead.objects.create(created_by=created_by, **validated_data)    #** → dictionary unpack
    return lead


def create_phase(lead, validated_data, created_by):
    if lead.status != LeadStatus.OPEN:
        raise ValidationError("Cannot add phases to a lead that has already been decided.")

    manager_id = validated_data.pop("manager_id", None)
    with transaction.atomic():
        last_order = lead.phases.aggregate(Max("order"))["order__max"] or 0
        phase = Phase.objects.create(
            lead=lead,
            created_by=created_by,
            order=last_order + 1,
            **validated_data,
        )
        if manager_id:
            from apps.accounts.models import User
            try:
                manager = User.objects.get(pk=manager_id)
                assign_phase_manager(phase, manager=manager, performed_by=created_by)
            except User.DoesNotExist:
                raise ValidationError("Selected technical manager does not exist.")
    return phase