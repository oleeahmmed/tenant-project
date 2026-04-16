from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "tenant", "recipient", "kind", "read_at", "created_at")
    list_filter = ("kind", "tenant")
    search_fields = ("title", "body", "recipient__email")
    readonly_fields = ("created_at",)
