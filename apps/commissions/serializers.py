from rest_framework import serializers
from .models import CommissionRecord


class CommissionRecordSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(source="project.title", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = CommissionRecord
        fields = [
            "id",
            "project",
            "project_title",
            "user_email",
            "role_name",
            "sale_amount",
            "commission_percentage",
            "commission_amount",
            "created_at",
        ]