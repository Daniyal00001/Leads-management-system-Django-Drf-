from django.core.mail import send_mail
from django.conf import settings

from .models import Notification, NotificationType


def _send_mail(subject, message, recipient_email):
    if not recipient_email:
        return
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL or "noreply@localhost",
        recipient_list=[recipient_email],
        fail_silently=True,
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
            f"You have been assigned to Phase {phase.order} "
            f"({phase.get_type_display()}) on '{phase.lead.project_name}'.\n"
            f"Due date: {phase.due_date}\n\n"
            f"Please log in to accept or decline this assignment."
        ),
        recipient_email=manager.email,
    )


def notify_phase_declined(phase, bd_or_relevant_user):
    Notification.objects.create(
        user=phase.lead.created_by,
        type=NotificationType.PHASE_DECLINED,
        content_object=phase,
        message=f"Phase {phase.order} on '{phase.lead.project_name}' was declined and needs reassignment.",
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
            f"Please log in to accept or decline this assignment."
        ),
        recipient_email=engineer.email,
    )


def notify_project_assigned(project, manager):
    Notification.objects.create(
        user=manager,
        type=NotificationType.PROJECT_ASSIGNED,
        content_object=project,
        message=f"You have been assigned as a manager on project '{project.title}'.",
    )
