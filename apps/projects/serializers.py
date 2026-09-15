from rest_framework import serializers

from apps.accounts.models import User
from .models import Project, ProjectManager


class UserBasicSerializer(serializers.ModelSerializer):    #base
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]


class ProjectManagerSerializer(serializers.ModelSerializer):
    manager = UserBasicSerializer(read_only=True)
    assigned_by = UserBasicSerializer(read_only=True)
    assigned_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = ProjectManager
        fields = ["id", "manager", "assigned_by", "assigned_at"]


class ProjectDetailSerializer(serializers.ModelSerializer):
    created_by = UserBasicSerializer(read_only=True)
    managers = ProjectManagerSerializer(source="project_managers", many=True, read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "lead",
            "title",
            "status",
            "sale_amount",
            "created_by",
            "managers",
            "created_at",
        ]


class ProjectManagerAssignSerializer(serializers.Serializer):
    manager_id = serializers.IntegerField()

    def validate_manager_id(self, value):
        from apps.accounts.roles import Roles

        try:
            user = User.objects.get(pk=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        if not user.groups.filter(name=Roles.TECHNICAL_MANAGER).exists():
            raise serializers.ValidationError("User is not a Technical Manager.")
        return value