from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.core.exceptions import ValidationError, PermissionDenied
from django.shortcuts import get_object_or_404

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