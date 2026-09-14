from django.contrib import admin

from .models import CommissionRule, CommissionRecord


@admin.register(CommissionRule)
class CommissionRuleAdmin(admin.ModelAdmin):
    list_display = [
        "role_name",
        "commission_percentage",
        "is_active",
        "created_at",
    ]

    list_filter = ["is_active"]
    search_fields = ["role_name"]


@admin.register(CommissionRecord)
class CommissionRecordAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "project",
        "role_name",
        "sale_amount",
        "commission_percentage",
        "commission_amount",
        "created_at",
    ]

    list_filter = ["role_name"]
    search_fields = [
        "user__email",
        "project__title",
    ]

    readonly_fields = [
        "project",
        "user",
        "role_name",
        "sale_amount",
        "commission_percentage",
        "commission_amount",
        "created_at",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False