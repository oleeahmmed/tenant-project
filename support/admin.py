from django.contrib import admin

from .models import SupportAttachment, SupportTicket, SupportTicketMessage


class SupportTicketMessageInline(admin.TabularInline):
    model = SupportTicketMessage
    extra = 0
    readonly_fields = ("author", "created_at")


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("reference", "tenant", "subject", "status", "priority", "requester", "assignee", "updated_at")
    list_filter = ("status", "priority", "product_area", "tenant")
    search_fields = ("reference", "subject", "requester__email")
    raw_id_fields = ("requester", "assignee", "tenant")
    inlines = [SupportTicketMessageInline]


@admin.register(SupportTicketMessage)
class SupportTicketMessageAdmin(admin.ModelAdmin):
    list_display = ("ticket", "author", "is_internal", "created_at")
    list_filter = ("is_internal",)


@admin.register(SupportAttachment)
class SupportAttachmentAdmin(admin.ModelAdmin):
    list_display = ("message", "name", "uploaded_at")
