from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class JobPosting(models.Model):
    """Tenant-scoped open role (linked to HRM department when applicable)."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        CLOSED = "closed", "Closed"
        FILLED = "filled", "Filled"

    class EmploymentType(models.TextChoices):
        FULL_TIME = "full_time", "Full-time"
        PART_TIME = "part_time", "Part-time"
        CONTRACT = "contract", "Contract"
        INTERNSHIP = "internship", "Internship"

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="recruitment_jobs",
    )
    title = models.CharField(max_length=255)
    department = models.ForeignKey(
        "hrm.Department",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="recruitment_jobs",
    )
    location = models.CharField(max_length=255, blank=True)
    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME,
    )
    openings = models.PositiveSmallIntegerField(default=1)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="recruitment_jobs_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        if self.department_id and self.tenant_id:
            if self.department.tenant_id != self.tenant_id:
                raise ValidationError(
                    {"department": "Department must belong to the same tenant."}
                )


class Application(models.Model):
    """Candidate application to a job posting."""

    class Stage(models.TextChoices):
        APPLIED = "applied", "Applied"
        SCREENING = "screening", "Screening"
        INTERVIEW = "interview", "Interview"
        OFFER = "offer", "Offer"
        HIRED = "hired", "Hired"
        REJECTED = "rejected", "Rejected"

    job = models.ForeignKey(
        JobPosting,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    cover_letter = models.TextField(blank=True)
    resume = models.FileField(
        upload_to="recruitment/resumes/%Y/%m/",
        blank=True,
        null=True,
    )
    stage = models.CharField(
        max_length=20,
        choices=Stage.choices,
        default=Stage.APPLIED,
    )
    internal_notes = models.TextField(blank=True)
    hired_employee = models.ForeignKey(
        "hrm.Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="recruitment_hires",
        help_text="Optional link after the person is added as an employee in HRM.",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="recruitment_applications_reviewed",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("job", "email")]

    def __str__(self):
        return f"{self.full_name} → {self.job.title}"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        if self.hired_employee_id and self.job.tenant_id:
            if self.hired_employee.tenant_id != self.job.tenant_id:
                raise ValidationError(
                    {"hired_employee": "Employee must belong to the same tenant as the job."}
                )
