from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.core.exceptions import ValidationError, PermissionDenied
from django.shortcuts import get_object_or_404

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.paginator import Paginator



from apps.accounts.models import User

from . import services
from .permissions import (
    IsBusinessDeveloper,
    IsTechnicalManager,
    IsBDOrTechnicalManager,
    IsEngineer,
)
from .serializers import (
    LeadListSerializer,
    LeadDetailSerializer,
    PhaseDetailSerializer,
    PhaseDeclineSerializer,
    PhaseManagerAssignSerializer,
    PhaseEngineerAssignSerializer,
    PhaseEngineerSerializer,
    LeadCreateSerializer,
    PhaseCreateSerializer,
    LeadMarkSaleSerializer,
)
from .models import Lead, Phase, PhaseEngineer


# =========================================================
# Lead Views
# =========================================================

class LeadListAPIView(generics.ListAPIView):
    queryset = (
        Lead.objects
        .select_related("created_by")
        .prefetch_related("phases")
    )
    serializer_class = LeadListSerializer
    permission_classes = [IsAuthenticated]


class LeadDetailAPIView(generics.RetrieveAPIView):
    queryset = (
        Lead.objects
        .select_related(
            "created_by",
            "sale_decided_by",
        )
        .prefetch_related(
            "phases__current_manager"
        )
    )
    serializer_class = LeadDetailSerializer
    permission_classes = [IsAuthenticated]


class LeadMarkSaleAPIView(APIView):
    permission_classes = [IsBusinessDeveloper]

    def post(self, request, pk):
        lead = get_object_or_404(Lead, pk=pk)
        serializer = LeadMarkSaleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            project = services.mark_lead_as_sale(
                lead,
                decided_by=request.user,
                sale_amount=serializer.validated_data["sale_amount"],
                manager_id=serializer.validated_data["manager_id"],
            )
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Lead marked as sale.", "project_id": project.id})




class LeadMarkNoSaleAPIView(APIView):
    permission_classes = [IsBusinessDeveloper]

    def post(self, request, pk):
        lead = get_object_or_404(Lead, pk=pk)

        try:
            services.mark_lead_as_no_sale(
                lead,
                decided_by=request.user,
            )
        except (ValidationError, PermissionDenied) as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": "Lead marked as no sale."}
        )


# =========================================================
# Phase Views
# =========================================================

class PhaseDetailAPIView(generics.RetrieveAPIView):
    queryset = (
        Phase.objects
        .select_related(
            "lead",
            "current_manager",
            "created_by",
        )
        .prefetch_related(
            "phase_engineers__engineer"
        )
    )
    serializer_class = PhaseDetailSerializer
    permission_classes = [IsAuthenticated]


class PhaseAssignManagerAPIView(APIView):
    permission_classes = [IsBusinessDeveloper]

    def post(self, request, pk):
        phase = get_object_or_404(Phase, pk=pk)

        serializer = PhaseManagerAssignSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        manager = get_object_or_404(
            User,
            pk=serializer.validated_data["manager_id"],
        )

        try:
            services.assign_phase_manager(
                phase,
                manager,
                performed_by=request.user,
            )
        except (ValidationError, PermissionDenied) as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            PhaseDetailSerializer(phase).data
        )


class PhaseAcceptAPIView(APIView):
    permission_classes = [IsTechnicalManager]

    def post(self, request, pk):
        phase = get_object_or_404(Phase, pk=pk)

        try:
            services.accept_phase(
                phase,
                manager=request.user,
            )
        except (ValidationError, PermissionDenied) as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            PhaseDetailSerializer(phase).data
        )


class PhaseDeclineAPIView(APIView):
    permission_classes = [IsTechnicalManager]

    def post(self, request, pk):
        phase = get_object_or_404(Phase, pk=pk)

        serializer = PhaseDeclineSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        try:
            services.decline_phase(
                phase,
                manager=request.user,
                comment=serializer.validated_data["comment"],
            )
        except (ValidationError, PermissionDenied) as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            PhaseDetailSerializer(phase).data
        )


class PhaseAddEngineerAPIView(APIView):
    permission_classes = [IsTechnicalManager]

    def post(self, request, pk):
        phase = get_object_or_404(Phase, pk=pk)

        serializer = PhaseEngineerAssignSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        engineer = get_object_or_404(
            User,
            pk=serializer.validated_data["engineer_id"],
        )

        try:
            services.add_engineer_to_phase(
                phase,
                engineer,
                assigned_by=request.user,
            )
        except (ValidationError, PermissionDenied) as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            PhaseDetailSerializer(phase).data
        )


class PhaseCompleteAPIView(APIView):
    permission_classes = [IsBDOrTechnicalManager]

    def post(self, request, pk):
        phase = get_object_or_404(Phase, pk=pk)

        try:
            services.complete_phase(
                phase,
                completed_by=request.user,
            )
        except (ValidationError, PermissionDenied) as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            PhaseDetailSerializer(phase).data
        )


# ===================================================================

class LeadCreateAPIView(APIView):
    permission_classes = [IsBusinessDeveloper]

    def post(self, request):
        serializer = LeadCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lead = services.create_lead(serializer.validated_data, created_by=request.user)
        return Response(LeadDetailSerializer(lead).data, status=status.HTTP_201_CREATED)


class PhaseCreateAPIView(APIView):
    permission_classes = [IsBusinessDeveloper]

    def post(self, request, lead_pk):
        from apps.accounts.permissions import is_super_admin
        lead = get_object_or_404(Lead, pk=lead_pk)

        # Only the BD who created this lead (or a super admin) can add phases
        if lead.created_by != request.user and not is_super_admin(request.user):
            return Response(
                {"detail": "Only the BD who created this lead can add phases."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = PhaseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            phase = services.create_phase(lead, serializer.validated_data, created_by=request.user)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(PhaseDetailSerializer(phase).data, status=status.HTTP_201_CREATED)


class PhaseEngineerAcceptAPIView(APIView):
    permission_classes = [IsEngineer]

    def post(self, request, pk):
        assignment = get_object_or_404(PhaseEngineer, pk=pk)
        try:
            services.accept_engineer_assignment(assignment, engineer=request.user)
        except (ValidationError, PermissionDenied) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PhaseEngineerSerializer(assignment).data)


class PhaseEngineerDeclineAPIView(APIView):
    permission_classes = [IsEngineer]

    def post(self, request, pk):
        assignment = get_object_or_404(PhaseEngineer, pk=pk)
        serializer = PhaseDeclineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            services.decline_engineer_assignment(
                assignment,
                engineer=request.user,
                comment=serializer.validated_data.get("comment", ""),
            )
        except (ValidationError, PermissionDenied) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PhaseEngineerSerializer(assignment).data)


class PhaseEngineerMarkDoneAPIView(APIView):
    permission_classes = [IsEngineer]

    def post(self, request, pk):
        assignment = get_object_or_404(PhaseEngineer, pk=pk)
        try:
            services.mark_engineer_done(assignment, engineer=request.user)
        except (ValidationError, PermissionDenied) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PhaseEngineerSerializer(assignment).data)


@login_required
def lead_list_page(request):
    from django.db.models import Q
    from .choices import LeadStatus

    leads_qs = (
        Lead.objects.select_related("created_by")
        .prefetch_related("phases")
        .order_by("-created_at")
    )

    status_filter = request.GET.get("status", "")
    query = request.GET.get("q", "").strip()

    if status_filter in {choice[0] for choice in LeadStatus.choices}:
        leads_qs = leads_qs.filter(status=status_filter)
    if query:
        leads_qs = leads_qs.filter(
            Q(project_name__icontains=query)
            | Q(client_name__icontains=query)
            | Q(client_email__icontains=query)
        )

    paginator = Paginator(leads_qs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "leads/lead_list.html",
        {
            "page_obj": page_obj,
            "status_filter": status_filter,
            "query": query,
        },
    )



    # ======================================

@login_required
def lead_detail_page(request, pk):
    from apps.accounts.roles import Roles
    from apps.accounts.permissions import is_super_admin, is_business_developer, is_technical_manager

    lead = get_object_or_404(
        Lead.objects.select_related("created_by", "sale_decided_by", "project")
        .prefetch_related("phases__current_manager", "phases__phase_engineers__engineer"),
        pk=pk,
    )

    user = request.user
    is_superadmin = is_super_admin(user)
    is_lead_creator = (lead.created_by == user)

    # TMs who are assigned to any phase of this lead can see full details
    is_assigned_tm = (
        is_technical_manager(user)
        and lead.phases.filter(current_manager=user).exists()
    )

    # Full details: superadmin, BD who created, or assigned TM
    can_see_full_details = is_superadmin or is_lead_creator or is_assigned_tm

    # Engineers and non-owner BDs and unassigned TMs see only basic view
    # (we show a restricted page rather than 403 so they at least see what they're assigned to)

    technical_managers = User.objects.filter(
        groups__name=Roles.TECHNICAL_MANAGER,
        is_active=True,
    ).order_by("email")
    engineers = User.objects.filter(
        groups__name=Roles.ENGINEER,
        is_active=True,
    ).order_by("email")
    return render(
        request,
        "leads/lead_detail.html",
        {
            "lead": lead,
            "technical_managers": technical_managers,
            "engineers": engineers,
            "can_see_full_details": can_see_full_details,
            "is_lead_creator": is_lead_creator,
            "is_superadmin": is_superadmin,
        },
    )


    # ========================================

@login_required
def lead_create_page(request):
    from apps.accounts.permissions import is_business_developer, is_super_admin

    if not (is_business_developer(request.user) or is_super_admin(request.user)):
        raise PermissionDenied("Only Business Developers can create leads.")

    return render(request, "leads/lead_create.html")


@login_required
def assignments_page(request):
    from apps.accounts.permissions import (
        is_engineer,
        is_super_admin,
        is_technical_manager,
    )
    from .choices import PhaseStatus

    user = request.user
    can_tm = is_technical_manager(user) or is_super_admin(user)
    can_eng = is_engineer(user) or is_super_admin(user)

    if not (can_tm or can_eng):
        raise PermissionDenied("This page is for Technical Managers and Engineers.")

    manager_phases = Phase.objects.none()
    engineer_assignments = PhaseEngineer.objects.none()

    if is_technical_manager(user):
        manager_phases = (
            Phase.objects.filter(current_manager=user)
            .exclude(status=PhaseStatus.COMPLETED)
            .select_related("lead", "current_manager")
            .prefetch_related("phase_engineers__engineer")
            .order_by("due_date")
        )
    elif is_super_admin(user):
        manager_phases = (
            Phase.objects.filter(
                status__in=[
                    PhaseStatus.PENDING_ACCEPTANCE,
                    PhaseStatus.PENDING_REASSIGNMENT,
                    PhaseStatus.ACCEPTED,
                    PhaseStatus.IN_PROGRESS,
                ]
            )
            .select_related("lead", "current_manager")
            .prefetch_related("phase_engineers__engineer")
            .order_by("due_date")
        )

    if is_engineer(user):
        engineer_assignments = (
            PhaseEngineer.objects.filter(engineer=user)
            .exclude(status=PhaseEngineer.Status.DECLINED)
            .select_related("phase__lead", "assigned_by", "engineer")
            .order_by("phase__due_date")
        )
    elif is_super_admin(user):
        engineer_assignments = (
            PhaseEngineer.objects.filter(
                status__in=[PhaseEngineer.Status.PENDING, PhaseEngineer.Status.ACCEPTED]
            )
            .select_related("phase__lead", "engineer", "assigned_by")
            .order_by("phase__due_date")
        )

    return render(
        request,
        "leads/assignments.html",
        {
            "manager_phases": manager_phases,
            "engineer_assignments": engineer_assignments,
            "show_manager_section": can_tm,
            "show_engineer_section": can_eng,
        },
    )