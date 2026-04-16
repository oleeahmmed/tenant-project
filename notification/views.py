from django.http import HttpResponseRedirect
from django.http import JsonResponse
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


def _user_notification_qs(request):
    tenant = request.hrm_tenant
    if tenant is None:
        return Notification.objects.none()
    return Notification.objects.filter(tenant=tenant, recipient=request.user).select_related("actor")


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


class NotificationUnreadCountApiView(NotificationDashboardAccessMixin, View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        unread = _user_notification_qs(request).filter(read_at__isnull=True).count()
        return JsonResponse({"ok": True, "unread": unread})


class NotificationInboxApiView(NotificationDashboardAccessMixin, View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        try:
            limit = min(max(int(request.GET.get("limit", 8)), 1), 30)
        except (TypeError, ValueError):
            limit = 8
        rows = _user_notification_qs(request).order_by("-created_at")[:limit]
        data = []
        for n in rows:
            data.append(
                {
                    "id": n.pk,
                    "title": n.title,
                    "body": n.body,
                    "kind": n.kind,
                    "link_url": n.link_url or "",
                    "read": bool(n.read_at),
                    "created_at": n.created_at.isoformat(),
                    "actor_name": (getattr(n.actor, "name", None) or getattr(n.actor, "email", "")) if n.actor_id else "",
                }
            )
        return JsonResponse({"ok": True, "results": data})
