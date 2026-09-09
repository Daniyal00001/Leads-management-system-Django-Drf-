from django.urls import path
from .views import CommentListAPIView, CommentCreateAPIView

app_name = "comments"

urlpatterns = [
    path("api/comments/", CommentListAPIView.as_view(), name="comment-list"),
    path("api/comments/create/", CommentCreateAPIView.as_view(), name="comment-create"),
]