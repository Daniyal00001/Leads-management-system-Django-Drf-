from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from django.contrib.contenttypes.models import ContentType

from .models import Comment, CommentAttachment
from .serializers import CommentSerializer, CommentCreateSerializer


class CommentListAPIView(generics.ListAPIView):
    """
    GET /api/comments/?model_name=lead&object_id=3
    Returns all comments for a given target object.
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        model_name = self.request.query_params.get("model_name")
        object_id = self.request.query_params.get("object_id")

        app_label_map = {"lead": "leads", "phase": "leads", "project": "projects"}
        app_label = app_label_map.get(model_name)

        qs = Comment.objects.select_related("user").prefetch_related("attachments")
        if app_label and object_id:
            content_type = ContentType.objects.filter(app_label=app_label, model=model_name).first()
            if content_type:
                qs = qs.filter(content_type=content_type, object_id=object_id)
            else:
                qs = qs.none()
        return qs


class CommentCreateAPIView(APIView):
    """
    POST /api/comments/create/
    multipart/form-data — supports 1+ image files under 'images'.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        comment = Comment.objects.create(
            content_type=data["content_type"],
            object_id=data["object_id"],
            user=request.user,
            body=data["body"],
        )

        images = request.FILES.getlist("images")
        for image in images:
            CommentAttachment.objects.create(comment=comment, image=image)

        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)