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

from .models import Lead, Phase
from . import services
from .permissions import (
    IsBusinessDeveloper,
    IsTechnicalManager,
    IsBDOrTechnicalManager,
)
from .serializers import (
    LeadListSerializer,
    LeadDetailSerializer,
    PhaseDetailSerializer,
    PhaseDeclineSerializer,
    PhaseManagerAssignSerializer,
    PhaseEngineerAssignSerializer,
    LeadCreateSerializer,
    PhaseCreateSerializer,
)


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

        try:
            project = services.mark_lead_as_sale(
                lead,
                decided_by=request.user,
            )
        except (ValidationError, PermissionDenied) as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": "Lead marked as sale.",
                "project_id": project.id,
            }
        )


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
        lead = get_object_or_404(Lead, pk=lead_pk)
        serializer = PhaseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            phase = services.create_phase(lead, serializer.validated_data, created_by=request.user)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(PhaseDetailSerializer(phase).data, status=status.HTTP_201_CREATED)


        # ==============================================



@login_required
def lead_list_page(request):
    leads_qs = Lead.objects.select_related("created_by").prefetch_related("phases").order_by("-created_at")

    paginator = Paginator(leads_qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "leads/lead_list.html", {"page_obj": page_obj})



    # ======================================

@login_required
def lead_detail_page(request, pk):
    lead = get_object_or_404(
        Lead.objects.select_related("created_by", "sale_decided_by")
        .prefetch_related("phases__current_manager", "phases__phase_engineers__engineer"),
        pk=pk,
    )
    return render(request, "leads/lead_detail.html", {"lead": lead})


    # ========================================

@login_required
def lead_create_page(request):
    from apps.accounts.permissions import is_business_developer
    if not is_business_developer(request.user):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Only Business Developers can create leads.")

    return render(request, "leads/lead_create.html")