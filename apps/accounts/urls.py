from django.urls import path
from django.contrib.auth import views as auth_views

from .views import RoleUserListAPIView, UserRoleUpdateAPIView, users_page

app_name = "accounts"

urlpatterns = [
    path("accounts/login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(next_page="accounts:login"), name="logout"),
    path("api/users/", RoleUserListAPIView.as_view(), name="user-list"),
    path("api/users/<int:pk>/roles/", UserRoleUpdateAPIView.as_view(), name="user-roles"),
    path("users/", users_page, name="user-page-list"),
]
