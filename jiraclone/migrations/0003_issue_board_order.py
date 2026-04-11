# Generated manually for Kanban ordering

from django.db import migrations, models


def backfill_board_order(apps, schema_editor):
    Issue = apps.get_model("jiraclone", "Issue")
    JiraProject = apps.get_model("jiraclone", "JiraProject")
    IssueStatus = apps.get_model("jiraclone", "IssueStatus")
    for project in JiraProject.objects.all().iterator():
        for st in IssueStatus.objects.filter(project=project).order_by("order", "id"):
            issues = (
                Issue.objects.filter(project=project, status=st, parent__isnull=True)
                .order_by("number", "id")
            )
            for i, issue in enumerate(issues):
                if issue.board_order != i:
                    issue.board_order = i
                    issue.save(update_fields=["board_order"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("jiraclone", "0002_issue_assignees_m2m"),
    ]

    operations = [
        migrations.AddField(
            model_name="issue",
            name="board_order",
            field=models.PositiveIntegerField(
                db_index=True,
                default=0,
                help_text="Order within a status column on the board (top-level issues only).",
            ),
        ),
        migrations.RunPython(backfill_board_order, noop_reverse),
    ]
