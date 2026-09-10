from django.contrib import admin

from .models import Project, ProjectManager


class ProjectManagerInline(admin.TabularInline):
    model = ProjectManager
    extra = 0
    fields = ["manager", "assigned_by"]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["title", "lead", "status", "created_by", "created_at"]
    list_filter = ["status"]
    search_fields = ["title", "lead__project_name"]
    inlines = [ProjectManagerInline]