from rest_framework.permissions import BasePermission

from apps.accounts.roles import Roles


class HasAnyRole(BasePermission):
    #Allow access if the user is a superuser, Super Admin, or has any allowed_roles    # base class

    allowed_roles = []

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name=Roles.SUPER_ADMIN).exists():
            return True
        if not self.allowed_roles:
            return False
        return request.user.groups.filter(name__in=self.allowed_roles).exists()


class IsSuperAdmin(HasAnyRole):
    allowed_roles = [Roles.SUPER_ADMIN]