from rest_framework import serializers

from apps.accounts.models import User
from .models import Project, ProjectManager


class UserBasicSerializer(serializers.ModelSerializer):    #base
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]


class ProjectManagerSerializer(serializers.ModelSerializer):
    manager = UserBasicSerializer(read_only=True)

    class Meta:
        model = ProjectManager
        fields = ["id", "manager", "assigned_at"]


class ProjectDetailSerializer(serializers.ModelSerializer):
    created_by = UserBasicSerializer(read_only=True)
    managers = ProjectManagerSerializer(source="project_managers", many=True, read_only=True)

    class Meta:
        model = Project
        fields = ["id", "lead", "title", "status", "created_by", "managers", "created_at"]


class ProjectManagerAssignSerializer(serializers.Serializer):
    manager_id = serializers.IntegerField()