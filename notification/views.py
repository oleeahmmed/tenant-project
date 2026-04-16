from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from .mixins import NotificationDashboardAccessMixin, NotificationPageContextMixin
from .models import Notification


class NotificationListView(NotificationDashboardAccessMixin, NotificationPageContextMixin, ListView):
    model = Notification
    template_name = "notification/list.html"
    context_object_name = "notifications"
    paginate_by = 30
    page_title = "Notifications"

    def get_queryset(self):
        tenant = self.request.hrm_tenant
        if tenant is None:
            return Notification.objects.none()
        return (
            Notification.objects.filter(tenant=tenant, recipient=self.request.user)
            .select_related("actor")
            .order_by("-created_at")
        )


class NotificationMarkReadView(NotificationDashboardAccessMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        tenant = request.hrm_tenant
        if tenant is None:
            return HttpResponseRedirect(reverse_lazy("notification:list"))
        pk = kwargs.get("pk")
        n = get_object_or_404(
            Notification,
            pk=pk,
            tenant=tenant,
            recipient=request.user,
        )
        if n.read_at is None:
            n.read_at = timezone.now()
            n.save(update_fields=["read_at"])
        next_url = request.POST.get("next") or reverse("notification:list")
        return HttpResponseRedirect(next_url)


class NotificationMarkAllReadView(NotificationDashboardAccessMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        tenant = request.hrm_tenant
        if tenant is None:
            return HttpResponseRedirect(reverse_lazy("notification:list"))
        now = timezone.now()
        Notification.objects.filter(
            tenant=tenant,
            recipient=request.user,
            read_at__isnull=True,
        ).update(read_at=now)
        return HttpResponseRedirect(reverse_lazy("notification:list"))
