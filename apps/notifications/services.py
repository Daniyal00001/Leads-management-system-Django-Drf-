from django.core.mail import send_mail
from django.conf import settings

from .models import Notification, NotificationType


def notify_phase_assigned(phase, manager):
    Notification.objects.create(
        user=manager,
        type=NotificationType.PHASE_ASSIGNED,
        content_object=phase,
        message=f"You have been assigned to Phase {phase.order} on '{phase.lead.project_name}'.",
    )
    # =========
    send_mail(
        subject=f"New Phase Assignment: {phase.lead.project_name}",
        message=(
            f"You have been assigned to Phase {phase.order} "
            f"({phase.get_type_display()}) on '{phase.lead.project_name}'.\n"
            f"Due date: {phase.due_date}\n\n"
            f"Please log in to accept or decline this assignment."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[manager.email],
        fail_silently=False,
    )


def notify_phase_declined(phase, bd_or_relevant_user):
    # Notify the BD who owns the lead that reassignment is needed
    Notification.objects.create(
        user=phase.lead.created_by,
        type=NotificationType.PHASE_DECLINED,
        content_object=phase,
        message=f"Phase {phase.order} on '{phase.lead.project_name}' was declined and needs reassignment.",
    )