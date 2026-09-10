from django.contrib import admin

from .models import Comment, CommentAttachment


class CommentAttachmentInline(admin.TabularInline):
    model = CommentAttachment
    extra = 0


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["user", "content_type", "object_id", "created_at"]
    list_filter = ["content_type", "created_at"]
    search_fields = ["body", "user__email"]
    inlines = [CommentAttachmentInline]