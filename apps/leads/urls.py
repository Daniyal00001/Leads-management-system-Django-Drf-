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
    LeadMarkSaleAPIView,
    LeadMarkNoSaleAPIView,
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
]