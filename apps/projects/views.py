from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from .models import Project
from .permissions import IsBDOrSuperAdmin
from .serializers import ProjectDetailSerializer, ProjectManagerAssignSerializer
from . import services


class ProjectListAPIView(generics.ListAPIView):
    queryset = Project.objects.select_related("created_by", "lead").prefetch_related(
        "project_managers__manager"
    )
    serializer_class = ProjectDetailSerializer
    permission_classes = [IsAuthenticated]


class ProjectDetailAPIView(generics.RetrieveAPIView):
    queryset = Project.objects.select_related("created_by", "lead").prefetch_related(
        "project_managers__manager"
    )
    serializer_class = ProjectDetailSerializer
    permission_classes = [IsAuthenticated]


class ProjectAssignManagerAPIView(APIView):
    permission_classes = [IsBDOrSuperAdmin]

    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        serializer = ProjectManagerAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from apps.accounts.models import User
        manager = get_object_or_404(User, pk=serializer.validated_data["manager_id"])

        try:
            services.assign_project_manager(project, manager, assigned_by=request.user)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ProjectDetailSerializer(project).data)