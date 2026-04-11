from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import IssueStatus, IssueType, JiraProject


def seed_jira_project_defaults(project: JiraProject) -> None:
    """Jira-like issue types and workflow statuses for a new project."""
    types_data = [
        ("Epic", 0, False),
        ("Story", 1, False),
        ("Task", 2, False),
        ("Bug", 3, False),
        ("Sub-task", 4, True),
    ]
    for name, order, is_sub in types_data:
        IssueType.objects.get_or_create(
            project=project,
            name=name,
            defaults={"order": order, "is_subtask": is_sub},
        )

    statuses_data = [
        ("To Do", "todo", 0, IssueStatus.Category.TODO, True),
        ("In Progress", "in_progress", 1, IssueStatus.Category.IN_PROGRESS, False),
        ("In Review", "in_review", 2, IssueStatus.Category.IN_PROGRESS, False),
        ("Done", "done", 3, IssueStatus.Category.DONE, False),
    ]
    for name, slug, order, cat, is_def in statuses_data:
        IssueStatus.objects.get_or_create(
            project=project,
            slug=slug,
            defaults={
                "name": name,
                "order": order,
                "category": cat,
                "is_default": is_def,
            },
        )


@receiver(post_save, sender=JiraProject)
def on_jira_project_created(sender, instance, created, **kwargs):
    if created:
        seed_jira_project_defaults(instance)
