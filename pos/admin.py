from django.contrib import admin

from .models import POSPayment, POSRegister, POSSale, POSSaleLine, POSSession


class POSSaleLineInline(admin.TabularInline):
    model = POSSaleLine
    extra = 0


class POSPaymentInline(admin.TabularInline):
    model = POSPayment
    extra = 0


@admin.register(POSRegister)
class POSRegisterAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "tenant", "default_warehouse", "is_active")
    list_filter = ("tenant", "is_active")


@admin.register(POSSession)
class POSSessionAdmin(admin.ModelAdmin):
    list_display = ("register", "opened_at", "status", "opened_by", "closed_at")
    list_filter = ("status",)


@admin.register(POSSale)
class POSSaleAdmin(admin.ModelAdmin):
    list_display = ("doc_no", "tenant", "session", "total_amount", "status", "sale_datetime")
    list_filter = ("status", "tenant")
    search_fields = ("doc_no",)
    inlines = [POSSaleLineInline, POSPaymentInline]
