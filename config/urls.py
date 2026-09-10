from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [

    path("admin/", admin.site.urls),

    path(
        "",
        RedirectView.as_view(pattern_name="leads:lead-page-list"),
        name="home",
    ),

    path("accounts/", include("apps.accounts.urls")),

    path("", include("apps.leads.urls")),

    path("", include("apps.comments.urls")),

    path("", include("apps.projects.urls")),

]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )