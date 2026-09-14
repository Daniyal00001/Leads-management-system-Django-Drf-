from django.core.exceptions import ValidationError
from django.db import transaction

from .models import ProjectManager


def assign_project_manager(project, manager, assigned_by):
    from apps.accounts.roles import Roles

    if not manager.groups.filter(name=Roles.TECHNICAL_MANAGER).exists():
        raise ValidationError("Assigned user must be a Technical Manager.")

    with transaction.atomic():
        obj, created = ProjectManager.objects.get_or_create(
            project=project,
            manager=manager,
            defaults={"assigned_by": assigned_by},
        )
        if not created:
            raise ValidationError("Manager is already assigned to this project.")

    from apps.notifications.services import notify_project_assigned

    notify_project_assigned(project, manager)
    return obj