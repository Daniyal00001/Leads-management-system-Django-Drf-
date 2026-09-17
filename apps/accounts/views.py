from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.permissions import is_super_admin
from apps.core.permissions import IsSuperAdmin
from .models import User
from .roles import Roles
from .serializers import UserListSerializer, UserRoleUpdateSerializer


class RoleUserListAPIView(generics.ListAPIView):
    serializer_class = UserListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        qs = User.objects.filter(is_active=True).prefetch_related("groups").order_by("email")
        role = self.request.query_params.get("role")
        if role:
            return qs.filter(groups__name=role).distinct()
        if not is_super_admin(self.request.user):
            return qs.none()
        return qs


class UserRoleUpdateAPIView(APIView):
    permission_classes = [IsSuperAdmin]

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        serializer = UserRoleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        groups = Group.objects.filter(name__in=serializer.validated_data["roles"])
        user.groups.set(groups)
        return Response(UserListSerializer(user).data, status=status.HTTP_200_OK)


@login_required       #admin users and roles page
def users_page(request):
    if not is_super_admin(request.user):
        raise PermissionDenied("Only Super Admins can manage users.")

    users = User.objects.prefetch_related("groups").order_by("email")
    return render(
        request,
        "accounts/user_list.html",
        {
            "users": users,
            "all_roles": Roles.ALL,
        },
    )
