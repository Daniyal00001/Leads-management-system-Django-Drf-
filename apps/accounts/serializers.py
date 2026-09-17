from rest_framework import serializers

from .models import User
from .roles import Roles


class UserListSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()    #Roles ki value  ek custom function se nikalni hai  --> get_roles()
    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "display_name",
            "phone",
            "is_active",
            "roles",
        ]

    def get_roles(self, obj):
        return list(obj.groups.values_list("name", flat=True))


class UserRoleUpdateSerializer(serializers.Serializer):
    roles = serializers.ListField(child=serializers.CharField(), allow_empty=True)  #incoming roles data ka basic structure/type check like in list of strings, allow_empty means empty list is allowed

    def validate_roles(self, value):
        invalid = sorted(set(value) - set(Roles.ALL))
        if invalid:
            raise serializers.ValidationError(f"Invalid roles: {', '.join(invalid)}")
        return value
