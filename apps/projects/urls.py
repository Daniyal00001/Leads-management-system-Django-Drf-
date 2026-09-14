from django.urls import path
from .views import (
    ProjectListAPIView,
    ProjectDetailAPIView,
    ProjectAssignManagerAPIView,
    project_detail_page,
    project_list_page,
)

app_name = "projects"

urlpatterns = [
    path("api/projects/", ProjectListAPIView.as_view(), name="project-list"),
    path("api/projects/<int:pk>/", ProjectDetailAPIView.as_view(), name="project-detail"),
    path("api/projects/<int:pk>/assign-manager/", ProjectAssignManagerAPIView.as_view(), name="project-assign-manager"),
    path("projects/", project_list_page, name="project-page-list"),
    path("projects/<int:pk>/", project_detail_page, name="project-page-detail"),
]