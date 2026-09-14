from django.urls import path

from .views import (
    LeadListAPIView,
    LeadDetailAPIView,
    PhaseDetailAPIView,
    PhaseAssignManagerAPIView,
    PhaseAcceptAPIView,
    PhaseDeclineAPIView,
    PhaseAddEngineerAPIView,
    PhaseCompleteAPIView,
    PhaseEngineerAcceptAPIView,
    PhaseEngineerDeclineAPIView,
    PhaseEngineerMarkDoneAPIView,
    LeadMarkSaleAPIView,
    LeadMarkNoSaleAPIView,
    LeadCreateAPIView,
    PhaseCreateAPIView,
    lead_list_page,
    lead_detail_page,
    lead_create_page,
    assignments_page,
)

app_name = "leads"

urlpatterns = [
    # Lead APIs
    path("api/leads/", LeadListAPIView.as_view(), name="lead-list"),
    path("api/leads/<int:pk>/", LeadDetailAPIView.as_view(), name="lead-detail"),
    path("api/leads/<int:pk>/mark-sale/", LeadMarkSaleAPIView.as_view(), name="lead-mark-sale"),
    path("api/leads/<int:pk>/mark-no-sale/", LeadMarkNoSaleAPIView.as_view(), name="lead-mark-no-sale"),

    # Phase APIs
    path("api/phases/<int:pk>/", PhaseDetailAPIView.as_view(), name="phase-detail"),
    path("api/phases/<int:pk>/assign-manager/", PhaseAssignManagerAPIView.as_view(), name="phase-assign-manager"),
    path("api/phases/<int:pk>/accept/", PhaseAcceptAPIView.as_view(), name="phase-accept"),
    path("api/phases/<int:pk>/decline/", PhaseDeclineAPIView.as_view(), name="phase-decline"),
    path("api/phases/<int:pk>/add-engineer/", PhaseAddEngineerAPIView.as_view(), name="phase-add-engineer"),
    path("api/phases/<int:pk>/complete/", PhaseCompleteAPIView.as_view(), name="phase-complete"),
    path("api/phase-engineers/<int:pk>/accept/", PhaseEngineerAcceptAPIView.as_view(), name="phase-engineer-accept"),
    path("api/phase-engineers/<int:pk>/decline/", PhaseEngineerDeclineAPIView.as_view(), name="phase-engineer-decline"),
    path("api/phase-engineers/<int:pk>/mark-done/", PhaseEngineerMarkDoneAPIView.as_view(), name="phase-engineer-done"),

    path("api/leads/create/", LeadCreateAPIView.as_view(), name="lead-create"),
    path("api/leads/<int:lead_pk>/phases/create/", PhaseCreateAPIView.as_view(), name="phase-create"),

    path("leads/", lead_list_page, name="lead-page-list"),
    path("leads/new/", lead_create_page, name="lead-page-create"),
    path("leads/<int:pk>/", lead_detail_page, name="lead-page-detail"),
    path("assignments/", assignments_page, name="assignments"),
]