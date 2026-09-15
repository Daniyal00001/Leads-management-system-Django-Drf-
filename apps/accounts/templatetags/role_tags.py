from django import template
from apps.accounts import permissions

register = template.Library()


@register.filter(name="has_role")
def has_role_filter(user, role_name):
    return permissions.has_role(user, role_name)


@register.filter
def role_slug(role_name):
    return (role_name or "").lower().replace(" ", "-")
