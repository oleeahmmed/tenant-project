from django.apps import AppConfig


class JiracloneConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "jiraclone"
    verbose_name = "Jira clone"

    def ready(self):
        from . import signals  # noqa: F401
