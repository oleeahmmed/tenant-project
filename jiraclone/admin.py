from django.contrib import admin

from .models import Issue, IssueComment, IssueStatus, IssueType, JiraProject, TenantLabel


@admin.register(JiraProject)
class JiraProjectAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "tenant", "is_active", "updated_at")
    list_filter = ("tenant", "is_active")
    search_fields = ("key", "name")


@admin.register(IssueType)
class IssueTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "order", "is_subtask")


@admin.register(IssueStatus)
class IssueStatusAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "slug", "order", "category", "is_default")


@admin.register(TenantLabel)
class TenantLabelAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "color")


class IssueCommentInline(admin.TabularInline):
    model = IssueComment
    extra = 0


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ("project", "number", "summary", "issue_type", "status", "priority", "updated_at")
    list_filter = ("project", "status", "priority", "issue_type")
    search_fields = ("summary", "description")
    filter_horizontal = ("assignees", "labels")
    inlines = [IssueCommentInline]
