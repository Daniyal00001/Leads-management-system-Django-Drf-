from rest_framework.permissions import BasePermission

# Base.....this class will be inherited by others
class HasAnyRole(BasePermission):

    allowed_roles = []

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name__in=self.allowed_roles).exists()