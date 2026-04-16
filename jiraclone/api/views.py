"""AJAX-first API for Jira single-board workflow."""

import json
from datetime import datetime

from django.http import JsonResponse
from django.utils import timezone
from django.views import View

from auth_tenants.models import User
from hrm.models import Department
from jiraclone.api.serializers import BoardIssueSerializer, ProjectDepartmentAssignmentSerializer
from jiraclone.mixins import JiraCloneAdminMixin, JiraCloneDashboardAccessMixin
from jiraclone.models import Issue, IssueComment, IssueType, ProjectDepartmentAssignment
from jiraclone.services.assignees import assignable_users_for_project
from jiraclone.services.board import move_board_issue
from jiraclone.views import ensure_request_tenant, get_project_or_404


def _json_error(msg, status=400):
    return JsonResponse({"ok": False, "error": msg}, status=status)


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
