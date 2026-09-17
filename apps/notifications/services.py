from django.core.mail import send_mail
from django.conf import settings

from apps.core.utils import absolute_url
from .models import Notification, NotificationType


def _send_mail(subject, message, recipient_email):    #helper func
    if not recipient_email:
        return
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL or "noreply@localhost",
        recipient_list=[recipient_email],
        fail_silently=True,
    )


def get_super_admin_users():
    from apps.accounts.models import User
    from apps.accounts.roles import Roles
    from django.db.models import Q

    return list(
        User.objects.filter(
            Q(is_superuser=True) | Q(groups__name=Roles.SUPER_ADMIN),
            is_active=True,
        ).distinct()
    )


def notify_admins(type, message, content_object=None, exclude_user=None):
    admins = get_super_admin_users()
    for admin in admins:
        if exclude_user and admin.id == exclude_user.id:
            continue
        Notification.objects.create(
            user=admin,
            type=type,
            content_object=content_object,
            message=message,
        )


def notify_phase_assigned(phase, manager):
    Notification.objects.create(
        user=manager,
        type=NotificationType.PHASE_ASSIGNED,
        content_object=phase,
        message=f"You have been assigned to Phase {phase.order} on '{phase.lead.project_name}'.",
    )
    _send_mail(
        subject=f"New Phase Assignment: {phase.lead.project_name}",
        message=(
            f"Hi {manager.display_name},\n\n"
            f"You have been assigned as Technical Manager for Phase {phase.order} "
            f"({phase.get_type_display()}) on the lead '{phase.lead.project_name}'.\n"
            f"Due date: {phase.due_date}\n\n"
            f"Please log in and go to your Assignments page to Accept or Decline:\n"
            f"{absolute_url('leads:assignments')}\n\n"
            f"You can also accept/decline directly from the lead detail page:\n"
            f"{absolute_url('leads:lead-page-detail', phase.lead_id)}\n\n"
            f"— Lead Management System"
        ),
        recipient_email=manager.email,
    )


def notify_phase_declined(phase, performed_by=None):
    if phase.lead.created_by:
        Notification.objects.create(
            user=phase.lead.created_by,
            type=NotificationType.PHASE_DECLINED,
            content_object=phase,
            message=f"Phase {phase.order} on '{phase.lead.project_name}' was declined and needs reassignment.",
        )
    manager_str = performed_by.email if performed_by else "Technical Manager"
    notify_admins(
        type=NotificationType.PHASE_DECLINED,
        message=f"Phase {phase.order} on '{phase.lead.project_name}' was declined by {manager_str} and needs reassignment.",
        content_object=phase,
        exclude_user=performed_by,
    )


def notify_phase_accepted(phase, manager):
    if phase.lead.created_by and phase.lead.created_by_id != manager.id:
        Notification.objects.create(
            user=phase.lead.created_by,
            type=NotificationType.PHASE_ACCEPTED,
            content_object=phase,
            message=f"Phase {phase.order} on '{phase.lead.project_name}' was accepted by {manager.email}.",
        )
    notify_admins(
        type=NotificationType.PHASE_ACCEPTED,
        message=f"Phase {phase.order} on '{phase.lead.project_name}' was accepted by {manager.email}.",
        content_object=phase,
        exclude_user=manager,
    )


def notify_phase_completed(phase, completed_by):
    if phase.lead.created_by and phase.lead.created_by_id != completed_by.id:
        Notification.objects.create(
            user=phase.lead.created_by,
            type=NotificationType.PHASE_COMPLETED,
            content_object=phase,
            message=f"Phase {phase.order} on '{phase.lead.project_name}' was marked as completed.",
        )
    notify_admins(
        type=NotificationType.PHASE_COMPLETED,
        message=f"Phase {phase.order} on '{phase.lead.project_name}' was completed by {completed_by.email}.",
        content_object=phase,
        exclude_user=completed_by,
    )


def notify_engineer_assigned(phase, engineer):
    Notification.objects.create(
        user=engineer,
        type=NotificationType.ENGINEER_ASSIGNED,
        content_object=phase,
        message=f"You have been added to Phase {phase.order} on '{phase.lead.project_name}'.",
    )
    _send_mail(
        subject=f"New Work Assignment: {phase.lead.project_name}",
        message=(
            f"You have been assigned to Phase {phase.order} "
            f"({phase.get_type_display()}) on '{phase.lead.project_name}'.\n"
            f"Due date: {phase.due_date}\n\n"
            f"Please log in and go to your Assignments page to Accept or Decline:\n"
            f"{absolute_url('leads:assignments')}\n\n"
            f"Lead detail:\n"
            f"{absolute_url('leads:lead-page-detail', phase.lead_id)}\n\n"
            f"— Lead Management System"
        ),
        recipient_email=engineer.email,
    )


def notify_engineer_declined(phase, engineer, comment=""):
    if phase.current_manager and phase.current_manager_id != engineer.id:
        Notification.objects.create(
            user=phase.current_manager,
            type=NotificationType.ENGINEER_DECLINED,
            content_object=phase,
            message=f"Engineer {engineer.email} declined Phase {phase.order} on '{phase.lead.project_name}'.",
        )
    notify_admins(
        type=NotificationType.ENGINEER_DECLINED,
        message=f"Engineer {engineer.email} declined Phase {phase.order} on '{phase.lead.project_name}'.",
        content_object=phase,
        exclude_user=engineer,
    )


def notify_lead_created(lead, created_by):
    notify_admins(
        type=NotificationType.LEAD_CREATED,
        message=f"New lead '{lead.project_name}' was created by {created_by.email}.",
        content_object=lead,
        exclude_user=created_by,
    )


def notify_lead_sale(lead, project, decided_by):
    if lead.created_by and lead.created_by_id != decided_by.id:
        Notification.objects.create(
            user=lead.created_by,
            type=NotificationType.LEAD_SALE,
            content_object=project,
            message=f"Lead '{lead.project_name}' has been marked as a SALE (Rs. {project.sale_amount:,.0f}).",
        )
    if project.manager and project.manager_id != decided_by.id:
        Notification.objects.create(
            user=project.manager,
            type=NotificationType.PROJECT_ASSIGNED,
            content_object=project,
            message=f"You have been assigned as manager on project '{project.title}'.",
        )
    notify_admins(
        type=NotificationType.LEAD_SALE,
        message=f"Lead '{lead.project_name}' was closed as a SALE (Rs. {project.sale_amount:,.0f}) by {decided_by.email}.",
        content_object=project,
        exclude_user=decided_by,
    )


def notify_lead_no_sale(lead, decided_by):
    if lead.created_by and lead.created_by_id != decided_by.id:
        Notification.objects.create(
            user=lead.created_by,
            type=NotificationType.LEAD_NO_SALE,
            content_object=lead,
            message=f"Lead '{lead.project_name}' was decided as NO-SALE.",
        )
    notify_admins(
        type=NotificationType.LEAD_NO_SALE,
        message=f"Lead '{lead.project_name}' was marked as NO-SALE by {decided_by.email}.",
        content_object=lead,
        exclude_user=decided_by,
    )


def notify_project_assigned(project, manager):
    Notification.objects.create(
        user=manager,
        type=NotificationType.PROJECT_ASSIGNED,
        content_object=project,
        message=f"You have been assigned as a manager on project '{project.title}'.",
    )
