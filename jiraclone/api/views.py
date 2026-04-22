"""AJAX-first API for Jira single-board workflow."""

import json
from datetime import datetime

from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from django.views import View
from rest_framework import status
from rest_framework.response import Response

from auth_tenants.permissions import TenantAPIView
from auth_tenants.models import User
from foundation.models import Customer
from hrm.models import Department
from jiraclone.api.serializers import (
    BoardIssueSerializer,
    JiraIssueCreateSerializer,
    JiraOnboardingCustomerSerializer,
    JiraProjectSerializer,
    ProjectDepartmentAssignmentSerializer,
)
from jiraclone.mixins import JiraCloneAdminMixin, JiraCloneDashboardAccessMixin
from jiraclone.models import Issue, IssueComment, IssueType, JiraProject, ProjectDepartmentAssignment
from jiraclone.services.assignees import assignable_users_for_project
from jiraclone.services.board import move_board_issue
from jiraclone.views import ensure_request_tenant, get_project_or_404


def _json_error(msg, status=400):
    return JsonResponse({"ok": False, "error": msg}, status=status)


def _project_open_issue_count(project):
    return (
        Issue.objects.filter(project=project, parent__isnull=True)
        .exclude(status__category="done")
        .count()
    )


def _project_membership_q(user):
    return (
        Q(lead=user)
        | Q(teams__members=user)
        | Q(department_assignments__users=user)
        | Q(issues__assignees=user)
        | Q(issues__reporter=user)
    )


def _user_project_queryset(tenant, user):
    return JiraProject.objects.filter(tenant=tenant, is_active=True).filter(_project_membership_q(user)).distinct()


class BoardMoveApiView(JiraCloneAdminMixin, View):
    http_method_names = ["post"]

    def post(self, request, project_key, *args, **kwargs):
        project = get_project_or_404(request, project_key)
        try:
            data = json.loads(request.body.decode("utf-8"))
            issue_id = int(data.get("issue_id"))
            status_id = int(data.get("status_id"))
            position = int(data.get("position", 0))
        except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
            return _json_error("issue_id, status_id, position required")
        issue = Issue.objects.filter(pk=issue_id, project=project, parent__isnull=True).first()
        if not issue:
            return _json_error("Issue not found", 404)
        move_board_issue(issue, status_id, position)
        return JsonResponse({"ok": True})


class IssueDetailApiView(JiraCloneDashboardAccessMixin, View):
    http_method_names = ["get"]

    def get(self, request, project_key, pk, *args, **kwargs):
        ensure_request_tenant(request)
        issue = (
            Issue.objects.filter(pk=int(pk), project__key=project_key.strip().upper(), project__tenant=request.hrm_tenant)
            .select_related("project", "issue_type", "status", "reporter", "parent", "epic")
            .prefetch_related("assignees", "labels")
            .first()
        )
        if not issue:
            return _json_error("Not found", 404)
        data = BoardIssueSerializer(issue).data
        data["comments"] = [
            {
                "id": c.id,
                "body": c.body,
                "author": c.author.name,
                "created_at": c.created_at.isoformat(),
            }
            for c in issue.comments.select_related("author").order_by("created_at")
        ]
        data["subtasks"] = [
            {
                "id": st.pk,
                "issue_key": st.issue_key,
                "summary": st.summary,
                "status": st.status.name,
                "assignees": ", ".join(a.name for a in st.assignees.all()),
            }
            for st in issue.subtasks.select_related("status").prefetch_related("assignees").order_by("number")
        ]
        data["can_manage"] = request.user.has_tenant_permission("jiraclone.manage")
        data["assignable_users"] = [{"id": u.id, "name": u.name} for u in assignable_users_for_project(issue.project)]
        data["departments_configured"] = issue.project.department_assignments.exists()
        return JsonResponse({"ok": True, "issue": data})


class IssueInlineUpdateApiView(JiraCloneAdminMixin, View):
    http_method_names = ["post"]

    def post(self, request, project_key, pk, *args, **kwargs):
        project = get_project_or_404(request, project_key)
        try:
            data = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return _json_error("Invalid JSON")
        issue = Issue.objects.filter(pk=int(pk), project=project).first()
        if not issue:
            return _json_error("Not found", 404)
        summary = (data.get("summary") or "").strip()
        if summary:
            issue.summary = summary[:500]
        issue.description = (data.get("description") or "").strip()
        if "priority" in data and data.get("priority") in dict(Issue.Priority.choices):
            issue.priority = data.get("priority")
        if "due_date" in data:
            raw = data.get("due_date")
            if raw in (None, "", "null"):
                issue.due_date = None
            else:
                try:
                    issue.due_date = datetime.strptime(str(raw)[:10], "%Y-%m-%d").date()
                except ValueError:
                    return _json_error("Invalid due_date")
        issue.updated_at = timezone.now()
        issue.save()
        return JsonResponse({"ok": True, "issue": BoardIssueSerializer(issue).data})


class IssueCommentApiView(JiraCloneDashboardAccessMixin, View):
    http_method_names = ["post"]

    def post(self, request, project_key, pk, *args, **kwargs):
        ensure_request_tenant(request)
        try:
            data = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return _json_error("Invalid JSON")
        body = (data.get("body") or "").strip()
        if not body:
            return _json_error("body required")
        issue = Issue.objects.filter(pk=int(pk), project__key=project_key.strip().upper(), project__tenant=request.hrm_tenant).first()
        if not issue:
            return _json_error("Not found", 404)
        IssueComment.objects.create(issue=issue, author=request.user, body=body)
        return JsonResponse({"ok": True})


class SubtaskCreateApiView(JiraCloneAdminMixin, View):
    http_method_names = ["post"]

    def post(self, request, project_key, *args, **kwargs):
        project = get_project_or_404(request, project_key)
        try:
            data = json.loads(request.body.decode("utf-8"))
            parent_id = int(data.get("parent_id"))
        except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
            return _json_error("parent_id required")
        summary = (data.get("summary") or "").strip()
        if not summary:
            return _json_error("summary required")
        parent = Issue.objects.filter(pk=parent_id, project=project).first()
        if not parent:
            return _json_error("Parent not found", 404)
        st_type = IssueType.objects.filter(project=project, name="Sub-task").first()
        default_status = project.issue_statuses.filter(is_default=True).first() or project.issue_statuses.order_by("order").first()
        if not st_type or not default_status:
            return _json_error("Sub-task setup missing", 400)
        issue = Issue(project=project, issue_type=st_type, status=default_status, summary=summary[:500], reporter=request.user, parent=parent)
        issue.save()
        raw_ids = data.get("assignee_ids") or []
        if isinstance(raw_ids, list):
            allowed_ids = set(assignable_users_for_project(project).values_list("pk", flat=True))
            use_ids = []
            for x in raw_ids:
                try:
                    uid = int(x)
                except (TypeError, ValueError):
                    continue
                if uid in allowed_ids:
                    use_ids.append(uid)
            if use_ids:
                issue.assignees.set(use_ids)
        return JsonResponse({"ok": True, "issue": BoardIssueSerializer(issue).data})


class QuickIssueCreateApiView(JiraCloneAdminMixin, View):
    http_method_names = ["post"]

    def post(self, request, project_key, *args, **kwargs):
        project = get_project_or_404(request, project_key)
        try:
            data = json.loads(request.body.decode("utf-8"))
            status_id = int(data.get("status_id"))
        except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
            return _json_error("status_id required")
        summary = (data.get("summary") or "").strip()
        if not summary:
            return _json_error("summary required")
        status = project.issue_statuses.filter(pk=status_id).first()
        itype = project.issue_types.filter(is_subtask=False).exclude(name="Epic").order_by("order").first() or project.issue_types.filter(is_subtask=False).first()
        if not status or not itype:
            return _json_error("Invalid setup", 400)
        issue = Issue(project=project, issue_type=itype, status=status, summary=summary[:500], reporter=request.user)
        issue.save()
        return JsonResponse({"ok": True, "issue": BoardIssueSerializer(issue).data})


class IssueFieldsUpdateApiView(JiraCloneAdminMixin, View):
    http_method_names = ["post"]

    def post(self, request, project_key, pk, *args, **kwargs):
        project = get_project_or_404(request, project_key)
        try:
            data = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return _json_error("Invalid JSON")
        issue = Issue.objects.filter(pk=int(pk), project=project).first()
        if not issue:
            return _json_error("Not found", 404)
        allowed_ids = set(assignable_users_for_project(project).values_list("pk", flat=True))
        if "assignee_ids" in data:
            raw = data.get("assignee_ids") or []
            if not isinstance(raw, list):
                return _json_error("assignee_ids must be list")
            ids = []
            for x in raw:
                try:
                    uid = int(x)
                except (TypeError, ValueError):
                    return _json_error("Invalid assignee")
                if uid not in allowed_ids:
                    return _json_error("Assignee not allowed")
                ids.append(uid)
            issue.assignees.set(ids)
        if "due_date" in data:
            raw = data.get("due_date")
            if raw in (None, "", "null"):
                issue.due_date = None
            else:
                issue.due_date = datetime.strptime(str(raw)[:10], "%Y-%m-%d").date()
        issue.updated_at = timezone.now()
        issue.save()
        return JsonResponse({"ok": True, "issue": BoardIssueSerializer(issue).data})


class StatusesListApiView(JiraCloneDashboardAccessMixin, View):
    http_method_names = ["get"]

    def get(self, request, project_key, *args, **kwargs):
        project = get_project_or_404(request, project_key)
        return JsonResponse({"ok": True, "statuses": [{"id": s.id, "name": s.name} for s in project.issue_statuses.order_by("order")]})


class IssueStatusUpdateApiView(JiraCloneAdminMixin, View):
    http_method_names = ["post"]

    def post(self, request, project_key, pk, *args, **kwargs):
        project = get_project_or_404(request, project_key)
        try:
            data = json.loads(request.body.decode("utf-8"))
            status_id = int(data.get("status_id"))
        except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
            return _json_error("status_id required")
        issue = Issue.objects.filter(pk=int(pk), project=project).first()
        st = project.issue_statuses.filter(pk=status_id).first()
        if not issue or not st:
            return _json_error("Invalid issue/status", 404)
        if issue.parent_id:
            issue.status = st
            issue.updated_at = timezone.now()
            issue.save(update_fields=["status", "updated_at"])
        else:
            move_board_issue(issue, status_id, 9999)
        return JsonResponse({"ok": True, "issue": BoardIssueSerializer(issue).data})


class DepartmentEmployeeOptionsApiView(JiraCloneAdminMixin, View):
    http_method_names = ["get"]

    def get(self, request, project_key, *args, **kwargs):
        project = get_project_or_404(request, project_key)
        mapped_rows = (
            project.department_assignments.select_related("department").prefetch_related("employees").order_by("order", "department__name")
        )
        mapped_department_ids = [row.department_id for row in mapped_rows]
        mapped_departments = [
            {"id": row.department_id, "name": row.department.name, "code": row.department.code}
            for row in mapped_rows
        ]
        available_departments = list(
            Department.objects.filter(tenant=project.tenant)
            .exclude(id__in=mapped_department_ids)
            .order_by("name")
            .values("id", "name", "code")
        )
        employees = list(
            User.objects.filter(tenant=project.tenant, is_active=True)
            .order_by("name")
            .values("id", "name", "email")
        )
        employees = [
            {
                "id": row["id"],
                "full_name": row["name"] or row["email"] or f"User {row['id']}",
                "employee_code": row["email"] or "",
                "department_id": None,
                "user_id": row["id"],
            }
            for row in employees
        ]
        return JsonResponse(
            {
                "ok": True,
                "departments": mapped_departments,
                "available_departments": available_departments,
                "employees": employees,
            }
        )


class DepartmentCreateApiView(JiraCloneAdminMixin, View):
    http_method_names = ["post"]

    def post(self, request, project_key, *args, **kwargs):
        project = get_project_or_404(request, project_key)
        try:
            data = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return _json_error("Invalid JSON")
        name = (data.get("name") or "").strip()
        if not name:
            return _json_error("Department name required")
        if len(name) > 200:
            return _json_error("Department name too long")
        dept, created = Department.objects.get_or_create(
            tenant=project.tenant,
            name=name,
            defaults={"code": (data.get("code") or "").strip()[:50]},
        )
        return JsonResponse(
            {
                "ok": True,
                "department": {"id": dept.id, "name": dept.name, "code": dept.code},
                "created": created,
            }
        )


class DepartmentDeleteApiView(JiraCloneAdminMixin, View):
    http_method_names = ["delete"]

    def delete(self, request, project_key, pk, *args, **kwargs):
        project = get_project_or_404(request, project_key)
        dept = Department.objects.filter(tenant=project.tenant, pk=pk).first()
        if not dept:
            return _json_error("Department not found", 404)
        dept.delete()
        return JsonResponse({"ok": True})


class DepartmentAssignmentListCreateApiView(JiraCloneAdminMixin, View):
    http_method_names = ["get", "post"]

    def get(self, request, project_key, *args, **kwargs):
        project = get_project_or_404(request, project_key)
        rows = project.department_assignments.select_related("department").prefetch_related("users").order_by(
            "order", "department__name"
        )
        return JsonResponse({"ok": True, "results": ProjectDepartmentAssignmentSerializer(rows, many=True).data})

    def post(self, request, project_key, *args, **kwargs):
        project = get_project_or_404(request, project_key)
        try:
            data = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return _json_error("Invalid JSON")
        dept_id = data.get("department_id")
        try:
            dept_id = int(dept_id)
        except (TypeError, ValueError):
            return _json_error("department_id required")
        dept = Department.objects.filter(tenant=project.tenant, id=dept_id).first()
        if not dept:
            return _json_error("Department not found", 404)
        row, _ = ProjectDepartmentAssignment.objects.get_or_create(
            project=project,
            department=dept,
            defaults={"order": int(data.get("order") or 0)},
        )
        row.order = int(data.get("order") or row.order or 0)
        row.save(update_fields=["order"])
        employee_ids = [int(x) for x in (data.get("employee_ids") or []) if str(x).isdigit()]
        row.users.set(User.objects.filter(tenant=project.tenant, is_active=True, id__in=employee_ids))
        return JsonResponse({"ok": True, "assignment": ProjectDepartmentAssignmentSerializer(row).data})


class DepartmentAssignmentDetailApiView(JiraCloneAdminMixin, View):
    http_method_names = ["post", "delete"]

    def post(self, request, project_key, pk, *args, **kwargs):
        project = get_project_or_404(request, project_key)
        row = ProjectDepartmentAssignment.objects.filter(project=project, pk=pk).first()
        if not row:
            return _json_error("Department assignment not found", 404)
        try:
            data = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return _json_error("Invalid JSON")
        row.order = int(data.get("order") or row.order or 0)
        row.save(update_fields=["order"])
        employee_ids = [int(x) for x in (data.get("employee_ids") or []) if str(x).isdigit()]
        row.users.set(User.objects.filter(tenant=project.tenant, is_active=True, id__in=employee_ids))
        return JsonResponse({"ok": True, "assignment": ProjectDepartmentAssignmentSerializer(row).data})

    def delete(self, request, project_key, pk, *args, **kwargs):
        project = get_project_or_404(request, project_key)
        row = ProjectDepartmentAssignment.objects.filter(project=project, pk=pk).first()
        if not row:
            return _json_error("Department assignment not found", 404)
        row.delete()
        return JsonResponse({"ok": True})


class JiraApiBase(TenantAPIView):
    module_code = "jiraclone"
    required_permission = "jiraclone.view"


class JiraProjectListApiView(JiraApiBase):
    def get(self, request):
        tenant = self.get_tenant()
        qs = (
            _user_project_queryset(tenant, request.user)
            .annotate(
                open_issue_count=Count(
                    "issues",
                    filter=Q(issues__parent__isnull=True) & ~Q(issues__status__category="done"),
                    distinct=True,
                )
            )
            .order_by("key")
        )
        data = []
        for p in qs:
            row = JiraProjectSerializer(p).data
            row["open_issue_count"] = int(getattr(p, "open_issue_count", 0) or 0)
            row["is_closed"] = row["open_issue_count"] == 0
            data.append(row)
        data.sort(key=lambda x: (x["is_closed"], x["key"]))
        return self.success_response(data)


class JiraOnboardingCustomerListApiView(JiraApiBase):
    def get(self, request):
        tenant = self.get_tenant()
        q = (request.GET.get("q") or "").strip()
        projects = _user_project_queryset(tenant, request.user).exclude(customer__isnull=True).select_related("customer").order_by("key")
        if q:
            projects = projects.filter(
                Q(customer__name__icontains=q)
                | Q(customer__customer_code__icontains=q)
                | Q(customer__email__icontains=q)
                | Q(customer__phone__icontains=q)
            )
        by_customer = {}
        for p in projects:
            if not p.customer_id:
                continue
            row = by_customer.setdefault(
                p.customer_id,
                {
                    "customer": p.customer,
                    "projects": [],
                },
            )
            open_count = _project_open_issue_count(p)
            row["projects"].append(
                {
                    "key": p.key,
                    "name": p.name,
                    "open_issue_count": open_count,
                    "is_closed": open_count == 0,
                }
            )
        results = []
        for payload in by_customer.values():
            customer = payload["customer"]
            customer_data = JiraOnboardingCustomerSerializer(customer).data
            projects_data = sorted(payload["projects"], key=lambda x: (x["is_closed"], x["key"]))
            customer_data["projects"] = projects_data
            customer_data["project_count"] = len(projects_data)
            customer_data["first_project_key"] = projects_data[0]["key"] if projects_data else ""
            customer_data["open_project_count"] = sum(1 for p in projects_data if not p["is_closed"])
            results.append(customer_data)
        results.sort(key=lambda x: ((x.get("open_project_count", 0) == 0), x.get("name", "").lower()))
        return self.success_response(results)


class JiraOnboardingCustomerDetailApiView(JiraApiBase):
    def get(self, request, customer_id):
        tenant = self.get_tenant()
        customer = Customer.objects.filter(tenant=tenant, is_active=True, pk=customer_id).first()
        if not customer:
            return self.error_response("Customer not found.", status.HTTP_404_NOT_FOUND)
        # Match web CustomerOnboardDetailView: all Jira projects for this customer (not membership-filtered).
        projects = JiraProject.objects.filter(tenant=tenant, customer=customer).order_by("key")
        q = (request.GET.get("q") or "").strip()
        if q:
            projects = projects.filter(Q(key__icontains=q) | Q(name__icontains=q))
        rows = []
        for p in projects:
            assignments = p.department_assignments.prefetch_related("employees")
            department_total = assignments.count()
            department_with_employees = sum(1 for row in assignments if row.employees.exists())
            employee_total = sum(row.employees.count() for row in assignments)
            percent = int((department_with_employees / department_total) * 100) if department_total else 0
            open_count = _project_open_issue_count(p)
            rows.append(
                {
                    "project": JiraProjectSerializer(p).data,
                    "progress": {
                        "department_total": department_total,
                        "department_with_employees": department_with_employees,
                        "employee_total": employee_total,
                        "percent": percent,
                    },
                    "open_issue_count": open_count,
                    "is_closed": open_count == 0,
                }
            )
        rows.sort(key=lambda x: (x["is_closed"], x["project"]["key"]))
        return self.success_response(
            {
                "customer": JiraOnboardingCustomerSerializer(customer).data,
                "project_rows": rows,
            }
        )


class JiraFoundationCustomerListApiView(JiraApiBase):
    """
    Same behaviour as GET /api/foundation/customers/ (CustomerListView) for mobile JWT clients.
    Web uses session + Foundation permission; this uses jiraclone.view.
    """

    def get(self, request):
        tenant = self.get_tenant()
        q = request.GET.get("q", "").strip()
        show_all = (request.GET.get("show_all") or "").strip() == "1"
        try:
            limit = min(max(int(request.GET.get("limit", 40)), 1), 200)
        except (TypeError, ValueError):
            limit = 40
        qs = Customer.objects.filter(tenant=tenant, is_active=True).only(
            "id",
            "customer_code",
            "name",
            "email",
            "phone",
            "city",
            "country",
        )
        if q:
            qs = qs.filter(name__icontains=q)
        elif not show_all:
            qs = qs.none()
        qs = qs.order_by("name")[:limit]
        customer_ids = [c.id for c in qs]
        first_project_by_customer = {}
        if customer_ids:
            project_rows = (
                JiraProject.objects.filter(tenant=tenant, customer_id__in=customer_ids, is_active=True)
                .only("key", "customer_id")
                .order_by("customer_id", "key")
            )
            for p in project_rows:
                if p.customer_id not in first_project_by_customer:
                    first_project_by_customer[p.customer_id] = p.key
        results = [
            {
                "id": c.id,
                "label": f"{c.customer_code} — {c.name}",
                "code": c.customer_code,
                "name": c.name,
                "email": c.email or "",
                "phone": c.phone or "",
                "city": c.city or "",
                "country": c.country or "",
                "first_project_key": first_project_by_customer.get(c.id) or "",
            }
            for c in qs
        ]
        return self.success_response({"results": results})


class JiraProjectDetailApiView(JiraApiBase):
    def get(self, request, project_key):
        tenant = self.get_tenant()
        project = JiraProject.objects.filter(tenant=tenant, key=project_key.strip().upper()).first()
        if not project:
            return self.error_response("Project not found.", status.HTTP_404_NOT_FOUND)
        return self.success_response(JiraProjectSerializer(project).data)


class JiraProjectBoardApiView(JiraApiBase):
    def get(self, request, project_key):
        tenant = self.get_tenant()
        project = JiraProject.objects.filter(tenant=tenant, key=project_key.strip().upper()).first()
        if not project:
            return self.error_response("Project not found.", status.HTTP_404_NOT_FOUND)
        statuses = list(project.issue_statuses.order_by("order"))
        issues = (
            Issue.objects.filter(project=project, parent__isnull=True)
            .select_related("issue_type", "status")
            .prefetch_related("assignees")
            .order_by("board_order", "number")
        )
        by_status = {s.id: [] for s in statuses}
        for issue in issues:
            if issue.status_id in by_status:
                by_status[issue.status_id].append(BoardIssueSerializer(issue).data)
        payload = {
            "project": JiraProjectSerializer(project).data,
            "statuses": [{"id": s.id, "name": s.name, "category": s.category} for s in statuses],
            "columns": [{"status_id": s.id, "status_name": s.name, "issues": by_status.get(s.id, [])} for s in statuses],
        }
        return self.success_response(payload)


class JiraIssueListCreateApiView(JiraApiBase):
    def get(self, request, project_key):
        tenant = self.get_tenant()
        project = JiraProject.objects.filter(tenant=tenant, key=project_key.strip().upper()).first()
        if not project:
            return self.error_response("Project not found.", status.HTTP_404_NOT_FOUND)
        qs = (
            Issue.objects.filter(project=project)
            .select_related("issue_type", "status")
            .prefetch_related("assignees")
            .order_by("-created_at")
        )
        limit = min(max(int(request.GET.get("limit", 100)), 1), 300)
        return self.success_response(BoardIssueSerializer(qs[:limit], many=True).data)

    def post(self, request, project_key):
        self.required_permission = "jiraclone.manage"
        tenant = self.get_tenant()
        project = JiraProject.objects.filter(tenant=tenant, key=project_key.strip().upper()).first()
        if not project:
            return self.error_response("Project not found.", status.HTTP_404_NOT_FOUND)
        serializer = JiraIssueCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        issue = Issue.objects.create(
            project=project,
            issue_type=data["issue_type"],
            status=data["status"],
            priority=data.get("priority", Issue.Priority.MEDIUM),
            summary=data["summary"],
            description=data.get("description", ""),
            reporter=request.user,
            due_date=data.get("due_date"),
            parent=data.get("parent"),
        )
        issue.assignees.set(User.objects.filter(id__in=data.get("assignee_ids", []), tenant=tenant, is_active=True))
        return self.success_response(BoardIssueSerializer(issue).data, code=status.HTTP_201_CREATED)
