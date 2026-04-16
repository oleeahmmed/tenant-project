import json

from django.contrib import messages
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from foundation.models import Customer
from hrm.tenant_scope import get_hrm_tenant

from .forms import (
    IssueCommentForm,
    IssueForm,
    ProjectDepartmentAssignmentForm,
    ProjectForm,
    ProjectTeamForm,
)
from .mixins import JiraCloneAdminMixin, JiraCloneDashboardAccessMixin, JiraClonePageContextMixin
from .models import Issue, JiraProject, ProjectDepartmentAssignment, ProjectTeam
from .services.assignees import assignable_users_for_project


def build_project_onboarding_progress(project):
    assignments = list(project.department_assignments.prefetch_related("employees").all())
    department_total = len(assignments)
    department_with_employees = sum(1 for row in assignments if row.employees.exists())
    employee_total = sum(row.employees.count() for row in assignments)
    percent = int((department_with_employees / department_total) * 100) if department_total else 0
    return {
        "department_total": department_total,
        "department_with_employees": department_with_employees,
        "employee_total": employee_total,
        "percent": percent,
    }


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


class CustomerOnboardListView(JiraCloneDashboardAccessMixin, JiraClonePageContextMixin, TemplateView):
    template_name = "jiraclone/customer_onboard_list.html"
    page_title = "Customer onboarding"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        q = (self.request.GET.get("q") or "").strip()
        show_all = (self.request.GET.get("show_all") or "").strip() == "1"
        ctx["selected"] = {"q": q, "show_all": show_all}
        return ctx


class CustomerOnboardDetailView(JiraCloneDashboardAccessMixin, JiraClonePageContextMixin, DetailView):
    template_name = "jiraclone/customer_onboard_detail.html"
    context_object_name = "customer"
    page_title = "Customer details"

    def get_queryset(self):
        return Customer.objects.filter(tenant=self.request.hrm_tenant, is_active=True)

    def get_object(self, queryset=None):
        qs = self.get_queryset() if queryset is None else queryset
        return get_object_or_404(qs, pk=self.kwargs["customer_id"])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        customer = self.object
        q = (self.request.GET.get("q") or "").strip()
        projects = list(
            JiraProject.objects.filter(
            tenant=self.request.hrm_tenant, customer=customer
            ).order_by("key")
        )
        if q:
            ql = q.lower()
            projects = [p for p in projects if ql in (p.key or "").lower() or ql in (p.name or "").lower()]
        project_rows = []
        for project in projects:
            project_rows.append({"project": project, "progress": build_project_onboarding_progress(project)})
        ctx["project_rows"] = project_rows
        ctx["selected"] = {"q": q}
        return ctx


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
        customer_id = (self.request.GET.get("customer_id") or "").strip()
        if customer_id.isdigit():
            customer = Customer.objects.filter(
                tenant=self.request.hrm_tenant,
                pk=int(customer_id),
                is_active=True,
            ).first()
            if customer and not self.object.customer_id:
                self.object.customer = customer
        self.object.save()
        messages.success(self.request, f"Project {self.object.key} created.")
        return redirect("jiraclone:project_board", project_key=self.object.key)

    def get_initial(self):
        initial = super().get_initial()
        customer_id = (self.request.GET.get("customer_id") or "").strip()
        if customer_id.isdigit():
            customer = Customer.objects.filter(
                tenant=self.request.hrm_tenant,
                pk=int(customer_id),
                is_active=True,
            ).first()
            if customer:
                initial["customer"] = customer.pk
        return initial


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
        return reverse_lazy("jiraclone:project_board", kwargs={"project_key": self.object.key})


class ProjectDetailView(
    JiraCloneDashboardAccessMixin, JiraClonePageContextMixin, ProjectByKeyMixin, DetailView
):
    def get(self, request, *args, **kwargs):
        return redirect("jiraclone:project_board", project_key=(kwargs.get("project_key") or "").strip().upper())


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
        # Board swimlanes: top-level issues only (subtasks open in the drawer).
        issues = (
            Issue.objects.filter(project=project, parent__isnull=True)
            .select_related("issue_type", "status")
            .prefetch_related("assignees")
            .order_by("board_order", "number")
        )
        by_status = {s.id: [] for s in statuses}
        for issue in issues:
            if issue.status_id in by_status:
                by_status[issue.status_id].append(issue)
        ctx["issues_by_status"] = by_status
        ctx["board_columns"] = [
            {"status": s, "issues": by_status.get(s.id, [])} for s in statuses
        ]
        ctx["can_manage_board"] = self.request.user.has_tenant_permission("jiraclone.manage")
        ctx["statuses_json"] = json.dumps([{"id": s.id, "name": s.name} for s in statuses])
        ctx["department_count"] = project.department_assignments.count()
        ctx["assignable_users"] = list(assignable_users_for_project(project).values("id", "name"))
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
        can_manage_issue = self.request.user.has_tenant_permission("jiraclone.manage")
        ctx["comment_form"] = IssueCommentForm()
        ctx["comments"] = issue.comments.select_related("author").order_by("created_at")
        ctx["can_manage_issue"] = can_manage_issue
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


class ProjectTeamListView(JiraCloneAdminMixin, JiraClonePageContextMixin, ProjectByKeyMixin, DetailView):
    """Teams under a project: members drive assignee options on the board."""

    model = JiraProject
    template_name = "jiraclone/team_list.html"
    context_object_name = "project"
    page_title = "Teams"

    def get_queryset(self):
        return JiraProject.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["teams"] = self.object.teams.prefetch_related("members").order_by("order", "name")
        return ctx


class ProjectTeamCreateView(JiraCloneAdminMixin, JiraClonePageContextMixin, CreateView):
    model = ProjectTeam
    form_class = ProjectTeamForm
    template_name = "jiraclone/team_form.html"
    page_title = "Add team"

    def dispatch(self, request, *args, **kwargs):
        self.jira_project = get_project_or_404(request, kwargs["project_key"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.jira_project
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.project = self.jira_project
        self.object.save()
        form.save_m2m()
        messages.success(self.request, "Team saved.")
        return redirect("jiraclone:project_teams", project_key=self.jira_project.key)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["project"] = self.jira_project
        return ctx


class ProjectTeamUpdateView(JiraCloneAdminMixin, JiraClonePageContextMixin, UpdateView):
    model = ProjectTeam
    form_class = ProjectTeamForm
    template_name = "jiraclone/team_form.html"
    context_object_name = "team"
    page_title = "Edit team"
    pk_url_kwarg = "pk"

    def get_queryset(self):
        return ProjectTeam.objects.filter(project__tenant=self.request.hrm_tenant)

    def get_object(self, queryset=None):
        qs = self.get_queryset()
        key = (self.kwargs.get("project_key") or "").strip().upper()
        return get_object_or_404(qs, pk=self.kwargs["pk"], project__key=key)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.object.project
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Team updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("jiraclone:project_teams", kwargs={"project_key": self.object.project.key})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["project"] = self.object.project
        return ctx


class ProjectTeamDeleteView(JiraCloneAdminMixin, JiraClonePageContextMixin, DeleteView):
    model = ProjectTeam
    template_name = "jiraclone/team_confirm_delete.html"
    context_object_name = "team"
    page_title = "Delete team"

    def get_queryset(self):
        return ProjectTeam.objects.filter(project__tenant=self.request.hrm_tenant)

    def get_object(self, queryset=None):
        qs = self.get_queryset()
        key = (self.kwargs.get("project_key") or "").strip().upper()
        return get_object_or_404(qs, pk=self.kwargs["pk"], project__key=key)

    def get_success_url(self):
        return reverse_lazy("jiraclone:project_teams", kwargs={"project_key": self.object.project.key})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["project"] = self.object.project
        return ctx


class ProjectDepartmentListView(
    JiraCloneAdminMixin, JiraClonePageContextMixin, ProjectByKeyMixin, DetailView
):
    model = JiraProject
    template_name = "jiraclone/department_list.html"
    context_object_name = "project"
    page_title = "Departments"

    def get_queryset(self):
        return JiraProject.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["assignments"] = self.object.department_assignments.select_related("department").prefetch_related(
            "employees"
        )
        ctx["onboarding_progress"] = build_project_onboarding_progress(self.object)
        return ctx


class ProjectDepartmentCreateView(JiraCloneAdminMixin, JiraClonePageContextMixin, CreateView):
    model = ProjectDepartmentAssignment
    form_class = ProjectDepartmentAssignmentForm
    template_name = "jiraclone/department_form.html"
    page_title = "Add department"

    def dispatch(self, request, *args, **kwargs):
        self.jira_project = get_project_or_404(request, kwargs["project_key"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.jira_project
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.project = self.jira_project
        self.object.save()
        form.save_m2m()
        messages.success(self.request, "Department assignment saved.")
        return redirect("jiraclone:project_departments", project_key=self.jira_project.key)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["project"] = self.jira_project
        return ctx


class ProjectDepartmentUpdateView(JiraCloneAdminMixin, JiraClonePageContextMixin, UpdateView):
    model = ProjectDepartmentAssignment
    form_class = ProjectDepartmentAssignmentForm
    template_name = "jiraclone/department_form.html"
    context_object_name = "assignment"
    page_title = "Edit department"
    pk_url_kwarg = "pk"

    def get_queryset(self):
        return ProjectDepartmentAssignment.objects.filter(project__tenant=self.request.hrm_tenant)

    def get_object(self, queryset=None):
        qs = self.get_queryset() if queryset is None else queryset
        key = (self.kwargs.get("project_key") or "").strip().upper()
        return get_object_or_404(qs, pk=self.kwargs["pk"], project__key=key)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.object.project
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Department assignment updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("jiraclone:project_departments", kwargs={"project_key": self.object.project.key})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["project"] = self.object.project
        return ctx


class ProjectDepartmentDeleteView(JiraCloneAdminMixin, JiraClonePageContextMixin, DeleteView):
    model = ProjectDepartmentAssignment
    template_name = "jiraclone/department_confirm_delete.html"
    context_object_name = "assignment"
    page_title = "Delete department"

    def get_queryset(self):
        return ProjectDepartmentAssignment.objects.filter(project__tenant=self.request.hrm_tenant)

    def get_object(self, queryset=None):
        qs = self.get_queryset() if queryset is None else queryset
        key = (self.kwargs.get("project_key") or "").strip().upper()
        return get_object_or_404(qs, pk=self.kwargs["pk"], project__key=key)

    def get_success_url(self):
        return reverse_lazy("jiraclone:project_departments", kwargs={"project_key": self.object.project.key})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["project"] = self.object.project
        return ctx
