from rest_framework import serializers
from .models import CommissionRecord


class CommissionRecordSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(source="project.title", read_only=True)

    class Meta:
        model = CommissionRecord
        fields = ["id", "project", "project_title", "role_name", "share_percentage", "amount", "created_at"]