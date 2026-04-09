from django.contrib import admin

from .models import Application, JobPosting


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ("title", "tenant", "status", "department", "employment_type", "openings", "created_at")
    list_filter = ("tenant", "status", "employment_type")
    search_fields = ("title", "location", "description")
    raw_id_fields = ("created_by",)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "job", "stage", "created_at")
    list_filter = ("stage", "job__tenant")
    search_fields = ("full_name", "email", "job__title")
    raw_id_fields = ("reviewed_by", "hired_employee")
