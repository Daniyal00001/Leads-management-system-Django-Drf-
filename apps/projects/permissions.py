from apps.core.permissions import HasAnyRole
from apps.accounts.roles import Roles


class IsBDOrSuperAdmin(HasAnyRole):   # BD or admin can assign the project to any managers
    allowed_roles = [Roles.BUSINESS_DEVELOPER, Roles.SUPER_ADMIN]