"""JSON API for single-page board (drag-drop, drawer, subtasks)."""

import json

from django.http import JsonResponse
from django.utils import timezone
from django.views import View

from .models import Issue, IssueComment, IssueType
from .services.assignees import assignable_users_for_project
from .services.board import move_board_issue
from .views import ensure_request_tenant, get_project_or_404
from .mixins import JiraCloneAdminMixin, JiraCloneDashboardAccessMixin


def _json_error(msg, status=400):
    return JsonResponse({"ok": False, "error": msg}, status=status)


def _issue_json(issue: Issue):
    assignees = [{"id": u.id, "name": u.name} for u in issue.assignees.all()]
    return {
        "id": issue.pk,
        "issue_key": issue.issue_key,
        "summary": issue.summary,
        "description": issue.description or "",
        "priority": issue.priority,
        "priority_display": issue.get_priority_display(),
        "due_date": issue.due_date.isoformat() if issue.due_date else None,
        "status": {"id": issue.status_id, "name": issue.status.name},
        "issue_type": {"id": issue.issue_type_id, "name": issue.issue_type.name},
        "assignees": assignees,
        "reporter": {"id": issue.reporter_id, "name": issue.reporter.name},
        "parent_id": issue.parent_id,
        "project_key": issue.project.key,
        "updated_at": issue.updated_at.isoformat(),
    }


class BoardMoveApiView(JiraCloneAdminMixin, View):
    http_method_names = ["post"]

    def post(self, request, project_key, *args, **kwargs):
        project = get_project_or_404(request, project_key)
        try:
            data = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return _json_error("Invalid JSON")
        try:
            issue_id = int(data.get("issue_id"))
            status_id = int(data.get("status_id"))
            position = int(data.get("position", 0))
        except (TypeError, ValueError):
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
        pk = int(pk)
        issue = (
            Issue.objects.filter(pk=pk, project__key=project_key.strip().upper(), project__tenant=request.hrm_tenant)
            .select_related("project", "issue_type", "status", "reporter", "parent", "epic")
            .prefetch_related("assignees", "labels")
            .first()
        )
        if not issue:
            return _json_error("Not found", 404)

        comments = [
            {
                "id": c.id,
                "body": c.body,
                "author": c.author.name,
                "created_at": c.created_at.isoformat(),
            }
            for c in issue.comments.select_related("author").order_by("created_at")
        ]
        subtasks = []
        for st in issue.subtasks.select_related("status", "issue_type").prefetch_related("assignees").order_by(
            "number"
        ):
            subtasks.append(
                {
                    "id": st.pk,
                    "issue_key": st.issue_key,
                    "summary": st.summary,
                    "status": st.status.name,
                    "assignees": ", ".join(a.name for a in st.assignees.all()),
                }
            )

        data = _issue_json(issue)
        data["comments"] = comments
        data["subtasks"] = subtasks
        data["labels"] = [{"name": lb.name, "color": lb.color} for lb in issue.labels.all()]
        data["epic"] = (
            {"id": issue.epic_id, "issue_key": issue.epic.issue_key, "summary": issue.epic.summary}
            if issue.epic_id
            else None
        )
        data["can_manage"] = request.user.has_tenant_permission("jiraclone.manage")
        assignable = assignable_users_for_project(issue.project)
        data["assignable_users"] = [{"id": u.id, "name": u.name} for u in assignable]
        data["teams_configured"] = issue.project.teams.exists()
        return JsonResponse({"ok": True, "issue": data})


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

        issue = Issue.objects.filter(
            pk=int(pk), project__key=project_key.strip().upper(), project__tenant=request.hrm_tenant
        ).first()
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
        except (json.JSONDecodeError, UnicodeDecodeError):
            return _json_error("Invalid JSON")
        parent_id = data.get("parent_id")
        summary = (data.get("summary") or "").strip()
        if not summary:
            return _json_error("summary required")
        try:
            parent_id = int(parent_id)
        except (TypeError, ValueError):
            return _json_error("parent_id required")

        parent = Issue.objects.filter(pk=parent_id, project=project).first()
        if not parent:
            return _json_error("Parent not found", 404)

        st_type = IssueType.objects.filter(project=project, name="Sub-task").first()
        if not st_type:
            return _json_error("Sub-task issue type missing", 400)
        default_status = project.issue_statuses.filter(is_default=True).first() or project.issue_statuses.order_by(
            "order"
        ).first()
        if not default_status:
            return _json_error("No status", 400)

        issue = Issue(
            project=project,
            issue_type=st_type,
            status=default_status,
            summary=summary[:500],
            reporter=request.user,
            parent=parent,
        )
        issue.save()
        return JsonResponse({"ok": True, "issue": _issue_json(issue)})


class QuickIssueCreateApiView(JiraCloneAdminMixin, View):
    """Create a top-level issue in a column from the board."""

    http_method_names = ["post"]

    def post(self, request, project_key, *args, **kwargs):
        project = get_project_or_404(request, project_key)
        try:
            data = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return _json_error("Invalid JSON")
        summary = (data.get("summary") or "").strip()
        status_id = data.get("status_id")
        if not summary:
            return _json_error("summary required")
        try:
            status_id = int(status_id)
        except (TypeError, ValueError):
            return _json_error("status_id required")

        status = project.issue_statuses.filter(pk=status_id).first()
        if not status:
            return _json_error("Invalid status", 400)

        itype = (
            project.issue_types.filter(is_subtask=False).exclude(name="Epic").order_by("order").first()
            or project.issue_types.filter(is_subtask=False).first()
        )
        if not itype:
            return _json_error("No issue type", 400)

        issue = Issue(
            project=project,
            issue_type=itype,
            status=status,
            summary=summary[:500],
            reporter=request.user,
        )
        issue.save()
        issue.refresh_from_db()
        return JsonResponse({"ok": True, "issue": _issue_json(issue)})


class IssueFieldsUpdateApiView(JiraCloneAdminMixin, View):
    """Update due date and assignees from board drawer (Jira-like)."""

    http_method_names = ["post"]

    def post(self, request, project_key, pk, *args, **kwargs):
        from datetime import datetime

        project = get_project_or_404(request, project_key)
        try:
            data = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return _json_error("Invalid JSON")

        issue = Issue.objects.filter(pk=int(pk), project=project).first()
        if not issue:
            return _json_error("Not found", 404)

        allowed = assignable_users_for_project(project)
        allowed_ids = set(allowed.values_list("pk", flat=True))

        if "assignee_ids" in data:
            raw = data.get("assignee_ids")
            if raw is None:
                issue.assignees.clear()
            else:
                if not isinstance(raw, list):
                    return _json_error("assignee_ids must be a list")
                ids = []
                for x in raw:
                    try:
                        ids.append(int(x))
                    except (TypeError, ValueError):
                        return _json_error("Invalid assignee id")
                for aid in ids:
                    if aid not in allowed_ids:
                        return _json_error("Assignee must be a project team member.")
                issue.assignees.set(ids)

        update_fields = ["updated_at"]
        if "due_date" in data:
            raw = data.get("due_date")
            if raw in (None, "", "null"):
                issue.due_date = None
            else:
                try:
                    issue.due_date = datetime.strptime(str(raw)[:10], "%Y-%m-%d").date()
                except ValueError:
                    return _json_error("Invalid due_date (use YYYY-MM-DD)")
            update_fields.append("due_date")

        issue.updated_at = timezone.now()
        issue.save(update_fields=update_fields)

        issue.refresh_from_db()
        return JsonResponse({"ok": True, "issue": _issue_json(issue)})


class StatusesListApiView(JiraCloneDashboardAccessMixin, View):
    """For drawer status dropdown."""

    http_method_names = ["get"]

    def get(self, request, project_key, *args, **kwargs):
        project = get_project_or_404(request, project_key)
        rows = [{"id": s.id, "name": s.name} for s in project.issue_statuses.order_by("order")]
        return JsonResponse({"ok": True, "statuses": rows})


class IssueStatusUpdateApiView(JiraCloneAdminMixin, View):
    http_method_names = ["post"]

    def post(self, request, project_key, pk, *args, **kwargs):
        project = get_project_or_404(request, project_key)
        try:
            data = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return _json_error("Invalid JSON")
        try:
            status_id = int(data.get("status_id"))
        except (TypeError, ValueError):
            return _json_error("status_id required")

        issue = Issue.objects.filter(pk=int(pk), project=project).first()
        if not issue:
            return _json_error("Not found", 404)
        st = project.issue_statuses.filter(pk=status_id).first()
        if not st:
            return _json_error("Invalid status", 400)

        if issue.parent_id:
            issue.status = st
            issue.updated_at = timezone.now()
            issue.save(update_fields=["status", "updated_at"])
        else:
            move_board_issue(issue, status_id, 9999)

        issue.refresh_from_db()
        return JsonResponse({"ok": True, "issue": _issue_json(issue)})
