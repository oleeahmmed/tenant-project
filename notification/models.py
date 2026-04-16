from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class Notification(models.Model):
    """
    Tenant-scoped inbox row for a single user. No FK to chat/jira models — metadata holds loose references.
    """

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications_received",
    )
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications_sent",
    )
    kind = models.CharField(
        max_length=64,
        db_index=True,
        help_text="e.g. system.*, chat.message, jiraclone.issue_assigned",
    )
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    link_url = models.CharField(
        max_length=1024,
        blank=True,
        help_text="Relative URL (e.g. /dashboard/chat/?room=1) or absolute path.",
    )
    metadata = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "recipient", "-created_at"]),
            models.Index(fields=["recipient", "read_at"]),
        ]

    def __str__(self):
        return f"{self.title} → {self.recipient_id}"
