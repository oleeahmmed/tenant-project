from django.conf import settings
from django.db import models
User = settings.AUTH_USER_MODEL


class TenantScopedModel(models.Model):
    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_rows",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SupportTicket(TenantScopedModel):
    """
    Tenant-scoped helpdesk ticket (requester ↔ agent), distinct from Jira issues (delivery work).
    """

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        PENDING = "pending", "In progress"
        WAITING_CUSTOMER = "waiting_customer", "Waiting on customer"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    class ProductArea(models.TextChoices):
        GENERAL = "general", "General / other"
        FOUNDATION = "foundation", "Foundation"
        INVENTORY = "inventory", "Inventory"
        FINANCE = "finance", "Finance"
        PURCHASE = "purchase", "Purchase"
        SALES = "sales", "Sales"
        PRODUCTION = "production", "Production"
        HRM = "hrm", "HRM"
        JIRACLONE = "jiraclone", "Jira / projects"
        CHAT = "chat", "Chat"
        POS = "pos", "POS"
        AUTH = "auth_tenants", "Users & access"

    reference = models.CharField(max_length=40, blank=True)
    subject = models.CharField(max_length=255)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True,
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL,
        db_index=True,
    )
    product_area = models.CharField(
        max_length=40,
        choices=ProductArea.choices,
        default=ProductArea.GENERAL,
        db_index=True,
    )
    requester = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="support_tickets_submitted",
    )
    assignee = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="support_tickets_assigned",
    )

    class Meta:
        ordering = ["-updated_at", "-id"]
        unique_together = [("tenant", "reference")]
        indexes = [
            models.Index(fields=["tenant", "status", "-updated_at"]),
        ]

    def __str__(self):
        return f"{self.reference} — {self.subject}"

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("support:ticket_detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        first = self.pk is None
        super().save(*args, **kwargs)
        if first or not self.reference:
            self.reference = f"TKT-{self.tenant_id}-{self.pk:05d}"
            super().save(update_fields=["reference"])


class SupportTicketMessage(models.Model):
    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="support_ticket_messages",
    )
    body = models.TextField()
    is_internal = models.BooleanField(
        default=False,
        help_text="If true, only agents with support permissions see this note.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.ticket.reference} @ {self.created_at}"


class SupportAttachment(models.Model):
    message = models.ForeignKey(
        SupportTicketMessage,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file = models.FileField(upload_to="support_attachments/%Y/%m/")
    name = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or self.file.name
