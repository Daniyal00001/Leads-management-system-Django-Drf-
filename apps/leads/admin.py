from django.contrib import admin

from .models import (
    Lead,
    Phase,
    PhaseManagerHistory,
    PhaseEngineer,
    PhaseEngineerHistory,
)


class PhaseInline(admin.TabularInline):
    model = Phase
    extra = 0
    fields = [
        "order",
        "type",
        "current_manager",
        "status",
        "start_date",
        "due_date",
    ]
    show_change_link = True


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = [
        "project_name",
        "client_name",
        "status",
        "created_by",
        "created_at",
    ]

    list_filter = [
        "status",
        "test_type",
        "created_at",
    ]

    search_fields = [
        "project_name",
        "client_name",
        "client_email",
    ]

    readonly_fields = [
        "sale_decided_at",
        "created_at",
        "updated_at",
    ]

    inlines = [PhaseInline]

    def save_model(self, request, obj, form, change): # here created by cannot be null ....so , created_by = logged-in user...
        if not obj.pk:
            obj.created_by = request.user

        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)

        for instance in instances:
            if isinstance(instance, Phase) and not instance.pk:
                instance.created_by = request.user

            instance.save()

        for obj in formset.deleted_objects:
            obj.delete()

        formset.save_m2m()


class PhaseManagerHistoryInline(admin.TabularInline):
    model = PhaseManagerHistory
    extra = 0

    readonly_fields = [
        "manager",
        "action",
        "comment",
        "performed_by",
        "action_at",
    ]

    can_delete = False


class PhaseEngineerInline(admin.TabularInline):
    model = PhaseEngineer
    extra = 0

    fields = [
        "engineer",
        "status",
        "assigned_by",
    ]


@admin.register(Phase)
class PhaseAdmin(admin.ModelAdmin):
    list_display = [
        "lead",
        "order",
        "type",
        "current_manager",
        "status",
        "due_date",
    ]

    list_filter = [
        "status",
        "type",
    ]

    search_fields = [
        "lead__project_name",
    ]

    inlines = [
        PhaseManagerHistoryInline,
        PhaseEngineerInline,
    ]

    def save_formset(self, request, form, formset, change): # here created by cannot be null ....so , created_by = logged-in user...
        instances = formset.save(commit=False)

        for instance in instances:
            if isinstance(instance, PhaseEngineer) and not instance.pk:
                instance.assigned_by = request.user

            instance.save()

        for obj in formset.deleted_objects:
            obj.delete()

        formset.save_m2m()


@admin.register(PhaseEngineerHistory)
class PhaseEngineerHistoryAdmin(admin.ModelAdmin):
    list_display = [
        "phase",
        "engineer",
        "action",
        "performed_by",
        "action_at",
    ]

    list_filter = [
        "action",
    ]

    readonly_fields = [
        "action_at",
    ]