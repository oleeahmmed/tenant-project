from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

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


class ScreenshotRecord(TenantScopedModel):
    class ActivityStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        IDLE = "idle", "Idle"
        AWAY = "away", "Away"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="screenhot_screenshots")
    image = models.ImageField(upload_to="screenhot/screenshots/%Y/%m/%d/")
    captured_at = models.DateTimeField(default=timezone.now, db_index=True)
    relative_path = models.CharField(max_length=512, blank=True, default="")
    activity_status = models.CharField(
        max_length=20,
        choices=ActivityStatus.choices,
        default=ActivityStatus.ACTIVE,
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-captured_at", "-id"]
        indexes = [
            models.Index(fields=["tenant", "user", "-captured_at"]),
        ]

    def __str__(self):
        return f"{self.user} @ {self.captured_at}"


class AttendanceRecord(TenantScopedModel):
    class ActivityStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        IDLE = "idle", "Idle"
        AWAY = "away", "Away"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="screenhot_attendance")
    check_in = models.DateTimeField(default=timezone.now, db_index=True)
    check_out = models.DateTimeField(null=True, blank=True, db_index=True)
    activity_status = models.CharField(
        max_length=20,
        choices=ActivityStatus.choices,
        default=ActivityStatus.ACTIVE,
    )
    last_activity = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-check_in", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "user"],
                condition=Q(check_out__isnull=True),
                name="screenhot_unique_open_attendance_per_tenant_user",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "user", "-check_in"]),
        ]

    @property
    def duration_seconds(self):
        end_time = self.check_out or timezone.now()
        return max(int((end_time - self.check_in).total_seconds()), 0)

    def __str__(self):
        return f"{self.user} in {self.check_in}"


class VideoJob(TenantScopedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="screenhot_requested_video_jobs")
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="screenhot_video_jobs")
    date_from = models.DateField()
    date_to = models.DateField()
    time_from = models.TimeField(null=True, blank=True)
    time_to = models.TimeField(null=True, blank=True)
    fps = models.PositiveIntegerField(default=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    output_file = models.FileField(upload_to="screenhot/videos/%Y/%m/%d/", null=True, blank=True)
    error_message = models.TextField(blank=True, default="")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["tenant", "status", "-created_at"]),
            models.Index(fields=["tenant", "target_user", "-created_at"]),
        ]

    def __str__(self):
        return f"VideoJob #{self.pk} ({self.status})"
