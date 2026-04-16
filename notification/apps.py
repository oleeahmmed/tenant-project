from django.apps import AppConfig


class NotificationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notification"
    verbose_name = "Notifications"

    def ready(self):
        # Optional integrations (chat / jiraclone) register signals only if those apps exist.
        from . import signals  # noqa: F401
