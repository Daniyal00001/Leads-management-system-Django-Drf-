from django.urls import path

from .views import (
    NotificationListAPIView,
    NotificationMarkReadAPIView,
    NotificationMarkAllReadAPIView,
    notification_list_page,
)

app_name = "notifications"

urlpatterns = [
    path("api/notifications/", NotificationListAPIView.as_view(), name="notification-list"),
    path(
        "api/notifications/<int:pk>/read/",
        NotificationMarkReadAPIView.as_view(),
        name="notification-read",
    ),
    path(
        "api/notifications/read-all/",
        NotificationMarkAllReadAPIView.as_view(),
        name="notification-read-all",
    ),
    path("notifications/", notification_list_page, name="notification-page-list"),
]
