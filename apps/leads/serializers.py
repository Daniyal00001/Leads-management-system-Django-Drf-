from rest_framework import serializers

from apps.accounts.models import User
from .models import Lead, Phase, PhaseManagerHistory, PhaseEngineer


class UserBasicSerializer(serializers.ModelSerializer):  # base class - acts as a parent
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]   # we donot expose all fields

# ==================================================================

class PhaseEngineerSerializer(serializers.ModelSerializer):
    engineer = UserBasicSerializer(read_only=True)    # inherit
    class Meta:
        model = PhaseEngineer
        fields = ["id", "engineer", "status"]


class PhaseListSerializer(serializers.ModelSerializer):
    current_manager = UserBasicSerializer(read_only=True)
    class Meta:
        model = Phase
        fields = [
            "id", "order", "type", "current_manager", "status",
            "start_date", "due_date", "completed_at",
        ]


class PhaseDetailSerializer(PhaseListSerializer):  # Fuller phase detail — includes engineers and manager history
    engineers = PhaseEngineerSerializer(source="phase_engineers", many=True, read_only=True)
    class Meta(PhaseListSerializer.Meta):
        fields = PhaseListSerializer.Meta.fields + ["engineers", "created_by", "created_at"]


class LeadListSerializer(serializers.ModelSerializer):
    created_by = UserBasicSerializer(read_only=True)
    class Meta:
        model = Lead
        fields = [
            "id", "project_name", "client_name", "status",
            "created_by", "created_at", "sale_decided_at",
        ]


class LeadDetailSerializer(LeadListSerializer): # from this we get user model
    phases = PhaseListSerializer(many=True, read_only=True)  # use phaselist serlizers fields
    all_phases_completed = serializers.ReadOnlyField()       # defined in model ...decorator func( claculated property)
    class Meta(LeadListSerializer.Meta):        # from this we get leadlist seriliazer meta behaviour
        fields = LeadListSerializer.Meta.fields + [
            "client_address", "client_email", "client_contact",
            "platform_used", "test_type", "comments_note",
            "phases", "all_phases_completed", "sale_decided_by",
        ]



        # =============================================================
        # =============================================================
        # =============================================================


class PhaseDeclineSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True, default="")


class PhaseManagerAssignSerializer(serializers.Serializer):
    manager_id = serializers.IntegerField()

    def validate_manager_id(self, value):
        from apps.accounts.models import User
        from apps.accounts.roles import Roles
        try:
            user = User.objects.get(pk=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        if not user.groups.filter(name=Roles.TECHNICAL_MANAGER).exists():
            raise serializers.ValidationError("User is not a Technical Manager.")
        return value


class PhaseEngineerAssignSerializer(serializers.Serializer):
    engineer_id = serializers.IntegerField()

    def validate_engineer_id(self, value):
        from apps.accounts.models import User
        from apps.accounts.roles import Roles
        try:
            user = User.objects.get(pk=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        if not user.groups.filter(name=Roles.ENGINEER).exists():
            raise serializers.ValidationError("User is not an Engineer.")
        return value



       # ==========================================================
       # ==========================================================
       # =========================================================

class LeadCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = [
            "id", "project_name", "client_name", "client_address",
            "client_email", "client_contact", "platform_used",
            "test_type", "comments_note",
        ]
        read_only_fields = ["id"]


class PhaseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Phase
        fields = ["id", "type", "start_date", "due_date"]  
        read_only_fields = ["id"]

    def validate(self, attrs):
        if attrs["due_date"] < attrs["start_date"]:
            raise serializers.ValidationError("due_date cannot be before start_date.")
        return attrs