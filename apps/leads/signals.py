from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import PhaseManagerHistory
from apps.notifications.services import notify_phase_assigned, notify_phase_declined


@receiver(post_save, sender=PhaseManagerHistory)
def handle_phase_manager_history(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.action == PhaseManagerHistory.Action.ASSIGNED:
        notify_phase_assigned(instance.phase, instance.manager)
    elif instance.action == PhaseManagerHistory.Action.DECLINED:
        notify_phase_declined(instance.phase, instance.performed_by)