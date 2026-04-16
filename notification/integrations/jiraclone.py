"""
Jira clone → notifications. Loaded only if ``jiraclone`` is installed.
"""

from django.db.models.signals import m2m_changed, post_save, pre_save
from django.urls import reverse


def connect() -> None:
    from jiraclone.models import Issue, IssueComment

    post_save.connect(
        _on_issue_saved,
        sender=Issue,
        dispatch_uid="notification_jira_issue_saved",
    )
    pre_save.connect(
        _on_issue_pre_save,
        sender=Issue,
        dispatch_uid="notification_jira_issue_pre_save",
    )
    post_save.connect(
        _on_issue_comment,
        sender=IssueComment,
        dispatch_uid="notification_jira_comment",
    )
    m2m_changed.connect(
        _on_issue_assignees_changed,
        sender=Issue.assignees.through,
        dispatch_uid="notification_jira_assignees",
    )


def _issue_detail_path(issue) -> str:
    return reverse(
        "jiraclone:issue_detail",
        kwargs={"project_key": issue.project.key, "pk": issue.pk},
    )


def _on_issue_comment(sender, instance, created, **kwargs):
    if not created:
        return

    from notification.services import notify_users

    issue = instance.issue
    tenant_id = issue.project.tenant_id
    author_id = instance.author_id

    recipient_ids = set(issue.assignees.values_list("pk", flat=True))
    if issue.reporter_id:
        recipient_ids.add(issue.reporter_id)
    recipient_ids.discard(author_id)
    if not recipient_ids:
        return

    snippet = (instance.body or "").strip()
    if len(snippet) > 280:
        snippet = snippet[:277] + "…"

    author_name = getattr(instance.author, "name", None) or getattr(instance.author, "email", "Someone")
    title = f"Comment on {issue.issue_key}"
    body = f"{author_name}: {snippet}" if snippet else f"{author_name} commented."

    notify_users(
        tenant_id=tenant_id,
        recipient_ids=recipient_ids,
        title=title,
        body=body,
        kind="jiraclone.issue_comment",
        link_url=_issue_detail_path(issue),
        metadata={
            "source": "jiraclone",
            "issue_id": issue.pk,
            "project_key": issue.project.key,
            "comment_id": instance.pk,
        },
        actor_id=author_id,
    )


def _on_issue_assignees_changed(sender, instance, action, pk_set, **kwargs):
    if action != "post_add" or not pk_set:
        return

    from jiraclone.models import Issue

    if not isinstance(instance, Issue):
        return

    from notification.services import notify_users

    issue = instance
    tenant_id = issue.project.tenant_id
    summary_short = (issue.summary or "")[:200]

    for uid in pk_set:
        title = f"Assigned to {issue.issue_key}"
        body = summary_short
        notify_users(
            tenant_id=tenant_id,
            recipient_ids=[uid],
            title=title,
            body=body,
            kind="jiraclone.issue_assigned",
            link_url=_issue_detail_path(issue),
            metadata={
                "source": "jiraclone",
                "issue_id": issue.pk,
                "project_key": issue.project.key,
            },
            actor_id=None,
        )


def _on_issue_saved(sender, instance, created, **kwargs):
    from notification.services import notify_users

    issue = instance
    tenant_id = issue.project.tenant_id
    issue_link = _issue_detail_path(issue)
    summary_short = (issue.summary or "")[:200]

    if created:
        recipient_ids = set(issue.assignees.values_list("pk", flat=True))
        if issue.reporter_id:
            recipient_ids.add(issue.reporter_id)
        if recipient_ids:
            notify_users(
                tenant_id=tenant_id,
                recipient_ids=recipient_ids,
                title=f"New issue {issue.issue_key}",
                body=summary_short,
                kind="jiraclone.issue_created",
                link_url=issue_link,
                metadata={
                    "source": "jiraclone",
                    "issue_id": issue.pk,
                    "project_key": issue.project.key,
                },
                actor_id=issue.reporter_id,
            )
        return

    old_status_id = getattr(issue, "_notification_old_status_id", None)
    if old_status_id is None or old_status_id == issue.status_id:
        return

    recipient_ids = set(issue.assignees.values_list("pk", flat=True))
    if issue.reporter_id:
        recipient_ids.add(issue.reporter_id)
    if not recipient_ids:
        return

    notify_users(
        tenant_id=tenant_id,
        recipient_ids=recipient_ids,
        title=f"Status updated: {issue.issue_key}",
        body=f"Now in {issue.status.name}",
        kind="jiraclone.issue_status_changed",
        link_url=issue_link,
        metadata={
            "source": "jiraclone",
            "issue_id": issue.pk,
            "project_key": issue.project.key,
            "status_id": issue.status_id,
        },
        actor_id=None,
    )


def _on_issue_pre_save(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old_status_id = sender.objects.filter(pk=instance.pk).values_list("status_id", flat=True).first()
    except Exception:
        old_status_id = None
    instance._notification_old_status_id = old_status_id
