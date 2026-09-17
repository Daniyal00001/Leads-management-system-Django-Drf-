from apps.accounts.permissions import (
    is_business_developer,
    is_engineer,
    is_super_admin,
    is_technical_manager,
)


def app_context(request):                         #context file avaliable in all templates
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {
            "user_roles": [],
            "is_super_admin": False,
            "is_bd": False,
            "is_tm": False,
            "is_engineer": False,
            "unread_notification_count": 0,
        }

    roles = list(user.groups.values_list("name", flat=True))
    super_admin_flag = is_super_admin(user)
    if super_admin_flag and "Super Admin" not in roles:
        roles.insert(0, "Super Admin")
    unread = user.notifications.filter(is_read=False).count()

    return {
        "user_roles": roles,
        "is_super_admin": super_admin_flag,
        "is_bd": is_business_developer(user),
        "is_tm": is_technical_manager(user),
        "is_engineer": is_engineer(user),
        "unread_notification_count": unread,
    }
