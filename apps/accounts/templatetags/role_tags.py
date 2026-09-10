from django import template
from apps.accounts import permissions

register = template.Library()


@register.filter(name="has_role")   #runing has role function in accounts.permission through filter
def has_role_filter(user, role_name):
    return permissions.has_role(user, role_name)