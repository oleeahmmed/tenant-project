from django.contrib import messages
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView

from auth_tenants.models import User

from hrm.tenant_scope import user_belongs_to_workspace_tenant

from .forms import SupportReplyForm, SupportTicketAgentForm, SupportTicketCreateForm
from .mixins import (
    SupportDashboardAccessMixin,
    SupportPageContextMixin,
)
from .models import SupportTicket, SupportTicketMessage


def _user_can_see_ticket(user, ticket: SupportTicket) -> bool:
    if user.role == "super_admin":
        return True
    if not user_belongs_to_workspace_tenant(user, ticket.tenant):
        return False
    if user.has_tenant_permission("support.supportticket.view"):
        return True
    return ticket.requester_id == user.id or ticket.assignee_id == user.id


def _user_is_agent(user) -> bool:
    if user.role == "super_admin":
        return True
    return user.has_tenant_permission("support.supportticket.change") or user.has_tenant_permission(
        "support.manage"
    )


class SupportTicketListView(
    SupportDashboardAccessMixin,
    SupportPageContextMixin,
    ListView,
):
    model = SupportTicket
    template_name = "support/ticket_list.html"
    context_object_name = "tickets"
    paginate_by = 25
    page_title = "Support tickets"

    def get_queryset(self):
        t = self.request.hrm_tenant
        if t is None:
            return SupportTicket.objects.none()
        qs = SupportTicket.objects.filter(tenant=t).select_related("requester", "assignee")
        u = self.request.user
        if u.role == "super_admin":
            return qs.order_by("-updated_at")
        if u.has_tenant_permission("support.supportticket.view"):
            return qs.order_by("-updated_at")
        return qs.filter(Q(requester=u) | Q(assignee=u)).order_by("-updated_at")


class SupportTicketCreateView(
    SupportDashboardAccessMixin,
    SupportPageContextMixin,
    CreateView,
):
    model = SupportTicket
    form_class = SupportTicketCreateForm
    template_name = "support/ticket_form.html"
    page_title = "New support ticket"

    def form_valid(self, form):
        t = self.request.hrm_tenant
        if t is None:
            messages.error(self.request, "No workspace tenant.")
            return redirect("dashboard")
        form.instance.tenant = t
        form.instance.requester = self.request.user
        response = super().form_valid(form)
        SupportTicketMessage.objects.create(
            ticket=self.object,
            author=self.request.user,
            body=form.cleaned_data["body"],
            is_internal=False,
        )
        messages.success(self.request, f"Ticket {self.object.reference} created.")
        return response

    def get_success_url(self):
        return reverse("support:ticket_detail", kwargs={"pk": self.object.pk})


class SupportTicketDetailView(SupportDashboardAccessMixin, SupportPageContextMixin, DetailView):
    model = SupportTicket
    template_name = "support/ticket_detail.html"
    context_object_name = "ticket"
    page_title = "Support ticket"

    def get_queryset(self):
        t = self.request.hrm_tenant
        if t is None:
            return SupportTicket.objects.none()
        return SupportTicket.objects.filter(tenant=t).select_related("requester", "assignee")

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not _user_can_see_ticket(self.request.user, obj):
            raise Http404()
        return obj

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not _user_can_see_ticket(request.user, self.object):
            raise Http404()

        if request.POST.get("action") == "agent" and _user_is_agent(request.user):
            agent_form = SupportTicketAgentForm(request.POST, instance=self.object, prefix="agent")
            agent_form.fields["assignee"].queryset = User.objects.filter(
                tenant=self.object.tenant,
                is_active=True,
            ).order_by("name")
            if agent_form.is_valid():
                agent_form.save()
                messages.success(request, "Ticket updated.")
                return redirect("support:ticket_detail", pk=self.object.pk)
            messages.error(request, "Could not update ticket.")
            return redirect("support:ticket_detail", pk=self.object.pk)

        reply_form = SupportReplyForm(request.POST)
        if reply_form.is_valid():
            internal = bool(reply_form.cleaned_data.get("is_internal")) and _user_is_agent(request.user)
            SupportTicketMessage.objects.create(
                ticket=self.object,
                author=request.user,
                body=reply_form.cleaned_data["body"],
                is_internal=internal,
            )
            self.object.save(update_fields=["updated_at"])
            messages.success(request, "Reply added.")
            return redirect("support:ticket_detail", pk=self.object.pk)
        messages.error(request, "Please enter a reply.")
        return redirect("support:ticket_detail", pk=self.object.pk)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["reply_form"] = SupportReplyForm()
        msgs = list(self.object.messages.select_related("author").order_by("created_at", "id"))
        if not _user_is_agent(self.request.user):
            msgs = [m for m in msgs if not m.is_internal]
        ctx["thread_messages"] = msgs
        ctx["is_agent"] = _user_is_agent(self.request.user)
        ctx["agent_form"] = None
        if _user_is_agent(self.request.user):
            af = SupportTicketAgentForm(instance=self.object, prefix="agent")
            af.fields["assignee"].queryset = User.objects.filter(
                tenant=self.object.tenant,
                is_active=True,
            ).order_by("name")
            ctx["agent_form"] = af
        return ctx
