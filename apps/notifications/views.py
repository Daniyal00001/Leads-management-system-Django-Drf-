from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListAPIView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class NotificationMarkReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save(update_fields=["is_read", "updated_at"])
        return Response({"detail": "Marked as read."})


class NotificationMarkAllReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"detail": "All notifications marked as read."})


def _notification_url(notification):
    obj = notification.content_object
    if obj is None:
        return ""
    model = notification.content_type.model
    if model == "phase":
        return f"/leads/{obj.lead_id}/"
    if model == "lead":
        return f"/leads/{obj.id}/"
    if model == "project":
        return f"/projects/{obj.id}/"
    return ""


@login_required
def notification_list_page(request):
    notifications = Notification.objects.filter(user=request.user)
    items = [
        {
            "notification": item,
            "url": _notification_url(item),
        }
        for item in notifications[:50]
    ]
    return render(
        request,
        "notifications/notification_list.html",
        {"items": items},
    )
