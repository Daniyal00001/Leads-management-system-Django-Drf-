from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.core.views import dashboard_page


urlpatterns = [

    path("admin/", admin.site.urls),

    path("", dashboard_page, name="home"),

    path("", include("apps.accounts.urls")),

    path("", include("apps.leads.urls")),

    path("", include("apps.comments.urls")),

    path("", include("apps.projects.urls")),

    path("", include("apps.commissions.urls")),

    path("", include("apps.notifications.urls")),

]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )