from .roles import Roles


def has_role(user, role_name):
    if not user.is_authenticated:
        return False
    return user.groups.filter(name=role_name).exists()


def is_super_admin(user):
    return user.is_superuser or has_role(user, Roles.SUPER_ADMIN)


def is_business_developer(user):
    return has_role(user, Roles.BUSINESS_DEVELOPER)


def is_technical_manager(user):
    return has_role(user, Roles.TECHNICAL_MANAGER)


def is_engineer(user):
    return has_role(user, Roles.ENGINEER)