# Generated manually

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("jiraclone", "0003_issue_board_order"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProjectTeam",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("order", models.PositiveSmallIntegerField(default=0)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="teams",
                        to="jiraclone.jiraproject",
                    ),
                ),
                (
                    "members",
                    models.ManyToManyField(
                        blank=True,
                        help_text="People who can be assigned issues on this project board.",
                        related_name="jira_project_teams",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["order", "id"],
                "unique_together": {("project", "name")},
            },
        ),
        migrations.AddField(
            model_name="issue",
            name="due_date",
            field=models.DateField(
                blank=True,
                help_text="Due date (shown on board card like Jira).",
                null=True,
            ),
        ),
    ]
