"""Kanban column ordering for top-level issues."""

from django.db import transaction
from django.utils import timezone

from ..models import Issue


def _top_level_board_qs(project, status_id):
    return Issue.objects.filter(
        project=project,
        status_id=status_id,
        parent__isnull=True,
    ).order_by("board_order", "number", "id")


@transaction.atomic
def move_board_issue(issue: Issue, new_status_id: int, new_index: int) -> None:
    """
    Move a top-level issue to another column and/or position.
    new_index is the final 0-based index within the target column.
    """
    if issue.parent_id:
        return
    project = issue.project
    if not project.issue_statuses.filter(pk=new_status_id).exists():
        return

    old_status_id = issue.status_id
    issue.status_id = new_status_id
    issue.updated_at = timezone.now()
    issue.save(update_fields=["status", "updated_at"])

    column = list(_top_level_board_qs(project, new_status_id))
    # Ensure issue is in the list once
    column = [i for i in column if i.pk != issue.pk]
    new_index = max(0, min(int(new_index), len(column)))
    column.insert(new_index, issue)

    for i, inst in enumerate(column):
        if inst.board_order != i:
            Issue.objects.filter(pk=inst.pk).update(board_order=i)

    # Renumber old column if status changed
    if old_status_id != new_status_id:
        for i, inst in enumerate(_top_level_board_qs(project, old_status_id)):
            Issue.objects.filter(pk=inst.pk).update(board_order=i)
