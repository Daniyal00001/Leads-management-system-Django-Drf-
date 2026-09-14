from rest_framework.permissions import IsAuthenticated
# any authenticated user. Reusing DRF's built-in IsAuthenticated


from apps.core.permissions import HasAnyRole
from apps.accounts.roles import Roles


class IsBusinessDeveloper(HasAnyRole):
    allowed_roles = [Roles.BUSINESS_DEVELOPER]


class IsTechnicalManager(HasAnyRole):
    allowed_roles = [Roles.TECHNICAL_MANAGER]


class IsBDOrTechnicalManager(HasAnyRole):
    allowed_roles = [Roles.BUSINESS_DEVELOPER, Roles.TECHNICAL_MANAGER]


class IsEngineer(HasAnyRole):
    allowed_roles = [Roles.ENGINEER]