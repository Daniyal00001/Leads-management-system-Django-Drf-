from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from apps.accounts.models import User
from apps.accounts.roles import Roles
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

        manager = get_object_or_404(User, pk=serializer.validated_data["manager_id"])

        try:
            services.assign_project_manager(project, manager, assigned_by=request.user)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ProjectDetailSerializer(project).data)


@login_required
def project_list_page(request):
    projects = (
        Project.objects.select_related("created_by", "lead")
        .prefetch_related("project_managers__manager")
        .order_by("-created_at")
    )
    paginator = Paginator(projects, 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "projects/project_list.html", {"page_obj": page_obj})


@login_required
def project_detail_page(request, pk):
    from apps.accounts.permissions import is_super_admin, is_engineer

    project = get_object_or_404(
        Project.objects.select_related("lead", "created_by", "manager")
        .prefetch_related(
            "project_managers__manager",
            "project_managers__assigned_by",
            "commission_records__user",
        ),
        pk=pk,
    )

    user = request.user
    is_superadmin = is_super_admin(user)
    is_lead_creator = (project.lead.created_by == user)
    is_project_manager = (
        (project.manager_id and project.manager == user)
        or project.project_managers.filter(manager=user).exists()
    )

    # Commission visibility: only lead creator BD, assigned project manager, or super admin
    can_see_commissions = is_superadmin or is_lead_creator or is_project_manager

    # Engineers should not see sale amount either
    can_see_financials = not is_engineer(user) or is_superadmin

    technical_managers = User.objects.filter(
        groups__name=Roles.TECHNICAL_MANAGER,
        is_active=True,
    ).order_by("email")
    return render(
        request,
        "projects/project_detail.html",
        {
            "project": project,
            "technical_managers": technical_managers,
            "can_see_commissions": can_see_commissions,
            "can_see_financials": can_see_financials,
        },
    )