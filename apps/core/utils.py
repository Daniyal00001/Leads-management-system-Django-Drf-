from django.conf import settings
from django.urls import reverse


#absolute url for email links

def absolute_url(viewname, *args, **kwargs):
    """Build an absolute URL from APP_BASE_URL + a named Django route."""
    path = reverse(viewname, args=args, kwargs=kwargs)
    return f"{settings.APP_BASE_URL}{path}"
