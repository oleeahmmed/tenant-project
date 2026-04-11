from django.contrib import messages
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from hrm.tenant_scope import get_hrm_tenant

from .forms import IssueCommentForm, IssueForm, ProjectForm
from .mixins import JiraCloneAdminMixin, JiraCloneDashboardAccessMixin, JiraClonePageContextMixin
from .models import Issue, JiraProject


def ensure_request_tenant(request):
    """Foundation mixins set this in dispatch; IssueCreateView called get_project before super()."""
    t = getattr(request, "hrm_tenant", None)
    if t is None:
        t = get_hrm_tenant(request)
        request.hrm_tenant = t
    return t


def get_project_or_404(request, key: str) -> JiraProject:
    tenant = ensure_request_tenant(request)
    if tenant is None:
        raise Http404("No workspace tenant")
    key = (key or "").strip().upper()
    return get_object_or_404(JiraProject, tenant=tenant, key=key)


class ProjectByKeyMixin:
    """Resolve project by URL kwarg `project_key` (case-insensitive)."""

    slug_url_kwarg = "project_key"
    slug_field = "key"

    def get_object(self, queryset=None):
        qs = self.get_queryset() if queryset is None else queryset
        key = (self.kwargs.get("project_key") or "").strip().upper()
        return get_object_or_404(qs, key=key)


class JiraDashboardView(JiraCloneDashboardAccessMixin, JiraClonePageContextMixin, TemplateView):
    template_name = "jiraclone/dashboard.html"
    page_title = "Jira clone"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        t = self.request.hrm_tenant
        qs = JiraProject.objects.filter(tenant=t, is_active=True)
        ctx["projects"] = qs.order_by("key")
        ctx["project_count"] = qs.count()
        ctx["issue_open_count"] = Issue.objects.filter(project__tenant=t).exclude(
            status__category="done"
        ).count()
        return ctx


class ProjectListView(JiraCloneDashboardAccessMixin, JiraClonePageContextMixin, ListView):
    model = JiraProject
    template_name = "jiraclone/project_list.html"
    context_object_name = "projects"
    page_title = "Projects"

    def get_queryset(self):
        return JiraProject.objects.filter(tenant=self.request.hrm_tenant).order_by("key")


class ProjectCreateView(JiraCloneAdminMixin, JiraClonePageContextMixin, CreateView):
    model = JiraProject
    form_class = ProjectForm
    template_name = "jiraclone/project_form.html"
    success_url = reverse_lazy("jiraclone:project_list")
    page_title = "Create project"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, f"Project {self.object.key} created.")
        return redirect("jiraclone:project_detail", project_key=self.object.key)


class ProjectUpdateView(JiraCloneAdminMixin, JiraClonePageContextMixin, ProjectByKeyMixin, UpdateView):
    model = JiraProject
    form_class = ProjectForm
    template_name = "jiraclone/project_form.html"
    context_object_name = "project"
    page_title = "Edit project"

    def get_queryset(self):
        return JiraProject.objects.filter(tenant=self.request.hrm_tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Project updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("jiraclone:project_detail", kwargs={"project_key": self.object.key})


class ProjectDetailView(
    JiraCloneDashboardAccessMixin, JiraClonePageContextMixin, ProjectByKeyMixin, DetailView
):
    model = JiraProject
    template_name = "jiraclone/project_detail.html"
    context_object_name = "project"

    def get_queryset(self):
        return JiraProject.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        project = self.object
        q = (self.request.GET.get("q") or "").strip()
        status_id = (self.request.GET.get("status") or "").strip()
        assignee_id = (self.request.GET.get("assignee") or "").strip()
        qs = (
            Issue.objects.filter(project=project)
            .select_related("issue_type", "status", "reporter")
            .prefetch_related("assignees")
        )
        if q:
            iq = Q(summary__icontains=q) | Q(description__icontains=q)
            if q.isdigit():
                iq |= Q(number=int(q))
            qs = qs.filter(iq)
        if status_id.isdigit():
            qs = qs.filter(status_id=int(status_id))
        if assignee_id.isdigit():
            qs = qs.filter(assignees__id=int(assignee_id)).distinct()
        ctx["issues"] = qs.order_by("-number")
        ctx["statuses_filter"] = project.issue_statuses.order_by("order")
        from auth_tenants.models import User

        ctx["tenant_users"] = User.objects.filter(tenant=self.request.hrm_tenant).order_by("name")
        ctx["selected"] = {"q": q, "status": status_id, "assignee": assignee_id}
        return ctx


class BoardView(
    JiraCloneDashboardAccessMixin, JiraClonePageContextMixin, ProjectByKeyMixin, DetailView
):
    """Kanban-style board: columns = workflow statuses."""

    model = JiraProject
    template_name = "jiraclone/board.html"
    context_object_name = "project"

    def get_queryset(self):
        return JiraProject.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        project = self.object
        statuses = list(project.issue_statuses.order_by("order"))
        ctx["statuses"] = statuses
        issues = (
            Issue.objects.filter(project=project)
            .select_related("issue_type", "status")
            .prefetch_related("assignees")
            .order_by("-number")
        )
        by_status = {s.id: [] for s in statuses}
        for issue in issues:
            if issue.status_id in by_status:
                by_status[issue.status_id].append(issue)
        ctx["issues_by_status"] = by_status
        ctx["board_columns"] = [
            {"status": s, "issues": by_status.get(s.id, [])} for s in statuses
        ]
        return ctx


class IssueDetailView(JiraCloneDashboardAccessMixin, JiraClonePageContextMixin, DetailView):
    model = Issue
    template_name = "jiraclone/issue_detail.html"
    context_object_name = "issue"

    def get_queryset(self):
        return (
            Issue.objects.filter(project__tenant=self.request.hrm_tenant)
            .select_related("project", "issue_type", "status", "reporter", "parent", "epic")
            .prefetch_related("assignees")
        )

    def get_object(self, queryset=None):
        qs = self.get_queryset()
        pk = self.kwargs.get("pk")
        key = (self.kwargs.get("project_key") or "").strip().upper()
        return get_object_or_404(qs, pk=pk, project__key=key)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        issue = self.object
        ctx["comment_form"] = IssueCommentForm()
        ctx["comments"] = issue.comments.select_related("author").order_by("created_at")
        ctx["subtasks"] = (
            issue.subtasks.select_related("issue_type", "status")
            .prefetch_related("assignees")
            .order_by("number")
        )
        return ctx


class IssueCreateView(JiraCloneAdminMixin, JiraClonePageContextMixin, CreateView):
    model = Issue
    form_class = IssueForm
    template_name = "jiraclone/issue_form.html"
    page_title = "Create issue"

    def dispatch(self, request, *args, **kwargs):
        self.jira_project = get_project_or_404(request, kwargs["project_key"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        p = self.jira_project
        req = self.request.GET

        status_id = (req.get("status_id") or "").strip()
        if status_id.isdigit():
            st = p.issue_statuses.filter(pk=int(status_id)).first()
            if st:
                initial["status"] = st.pk
        else:
            d = p.issue_statuses.filter(is_default=True).first() or p.issue_statuses.order_by("order").first()
            if d:
                initial["status"] = d.pk

        parent_id = (req.get("parent") or "").strip()
        if parent_id.isdigit():
            par = Issue.objects.filter(project=p, pk=int(parent_id)).first()
            if par:
                initial["parent"] = par.pk
                st = p.issue_types.filter(name="Sub-task").first()
                if st:
                    initial["issue_type"] = st.pk
        elif "issue_type" not in initial:
            t = p.issue_types.filter(is_subtask=False).order_by("order").first()
            if t:
                initial["issue_type"] = t.pk

        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.jira_project
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.project = self.jira_project
        self.object.reporter = self.request.user
        self.object.save()
        form.save_m2m()
        messages.success(self.request, f"Issue {self.object.issue_key} created.")
        return redirect(
            "jiraclone:issue_detail",
            project_key=self.jira_project.key,
            pk=self.object.pk,
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["project"] = self.jira_project
        if self.request.GET.get("parent"):
            ctx["page_title"] = "Create subtask"
        elif self.request.GET.get("status_id"):
            ctx["page_title"] = "Create issue in column"
        return ctx


class IssueUpdateView(JiraCloneAdminMixin, JiraClonePageContextMixin, UpdateView):
    model = Issue
    form_class = IssueForm
    template_name = "jiraclone/issue_form.html"
    context_object_name = "issue"
    page_title = "Edit issue"
    pk_url_kwarg = "pk"

    def get_queryset(self):
        return Issue.objects.filter(project__tenant=self.request.hrm_tenant).prefetch_related("assignees")

    def get_object(self, queryset=None):
        qs = self.get_queryset()
        pk = self.kwargs.get("pk")
        key = (self.kwargs.get("project_key") or "").strip().upper()
        return get_object_or_404(qs, pk=pk, project__key=key)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.object.project
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Issue updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "jiraclone:issue_detail",
            kwargs={"project_key": self.object.project.key, "pk": self.object.pk},
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["project"] = self.object.project
        return ctx


class IssueCommentPostView(JiraCloneDashboardAccessMixin, JiraClonePageContextMixin, View):
    """POST-only: add comment to issue."""

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        ensure_request_tenant(request)
        issue = get_object_or_404(
            Issue.objects.filter(project__tenant=request.hrm_tenant),
            pk=kwargs["pk"],
        )
        form = IssueCommentForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.issue = issue
            c.author = request.user
            c.save()
            messages.success(request, "Comment added.")
        else:
            messages.error(request, "Could not add comment.")
        return redirect(
            "jiraclone:issue_detail",
            project_key=issue.project.key,
            pk=issue.pk,
        )


class IssueStatusQuickUpdateView(JiraCloneAdminMixin, JiraClonePageContextMixin, View):
    """POST: move issue to another status (from board)."""

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        ensure_request_tenant(request)
        issue = get_object_or_404(
            Issue.objects.filter(project__tenant=request.hrm_tenant),
            pk=kwargs["pk"],
        )
        new_status_id = request.POST.get("status_id")
        if new_status_id and new_status_id.isdigit():
            st = issue.project.issue_statuses.filter(pk=int(new_status_id)).first()
            if st:
                Issue.objects.filter(pk=issue.pk).update(status=st, updated_at=timezone.now())
                messages.success(request, f"Moved to {st.name}.")
        return redirect(
            "jiraclone:project_board",
            project_key=issue.project.key,
        )
