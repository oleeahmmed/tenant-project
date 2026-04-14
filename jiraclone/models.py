from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Max

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


class JiraProject(TenantScopedModel):
    """A Jira-style project (scoped per tenant)."""

    key = models.CharField(max_length=10, help_text="Short key shown as PROJ-123, e.g. ACME")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    customer = models.ForeignKey(
        "foundation.Customer",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="jira_projects",
    )
    lead = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="led_jira_projects",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["key"]
        unique_together = [("tenant", "key")]

    def save(self, *args, **kwargs):
        self.key = (self.key or "").strip().upper()
        if not self.key:
            raise ValidationError({"key": "Project key is required."})
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.key} — {self.name}"


class ProjectDepartmentAssignment(models.Model):
    """Department mapping for onboarding execution inside a project."""

    project = models.ForeignKey(
        JiraProject,
        on_delete=models.CASCADE,
        related_name="department_assignments",
    )
    department = models.ForeignKey(
        "hrm.Department",
        on_delete=models.CASCADE,
        related_name="jira_project_assignments",
    )
    employees = models.ManyToManyField(
        "hrm.Employee",
        blank=True,
        related_name="jira_department_assignments",
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        unique_together = [("project", "department")]

    def __str__(self):
        return f"{self.project.key}: {self.department.name}"


class ProjectTeam(models.Model):
    """Board team: members are the only users offered as assignees when teams exist."""

    project = models.ForeignKey(JiraProject, on_delete=models.CASCADE, related_name="teams")
    name = models.CharField(max_length=120)
    order = models.PositiveSmallIntegerField(default=0)
    members = models.ManyToManyField(
        User,
        blank=True,
        related_name="jira_project_teams",
        help_text="People who can be assigned issues on this project board.",
    )

    class Meta:
        ordering = ["order", "id"]
        unique_together = [("project", "name")]

    def __str__(self):
        return f"{self.project.key}: {self.name}"


class IssueType(models.Model):
    project = models.ForeignKey(JiraProject, on_delete=models.CASCADE, related_name="issue_types")
    name = models.CharField(max_length=50)
    order = models.PositiveSmallIntegerField(default=0)
    is_subtask = models.BooleanField(default=False)

    class Meta:
        ordering = ["order", "id"]
        unique_together = [("project", "name")]

    def __str__(self):
        return f"{self.project.key}: {self.name}"


class IssueStatus(models.Model):
    class Category(models.TextChoices):
        TODO = "todo", "To do"
        IN_PROGRESS = "in_progress", "In progress"
        DONE = "done", "Done"

    project = models.ForeignKey(JiraProject, on_delete=models.CASCADE, related_name="issue_statuses")
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=80)
    order = models.PositiveSmallIntegerField(default=0)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.TODO)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["order", "id"]
        unique_together = [("project", "slug")]

    def __str__(self):
        return f"{self.project.key}: {self.name}"


class TenantLabel(models.Model):
    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="jira_labels")
    name = models.CharField(max_length=64)
    color = models.CharField(max_length=7, default="#64748B")

    class Meta:
        unique_together = [("tenant", "name")]

    def __str__(self):
        return self.name


class Issue(models.Model):
    class Priority(models.TextChoices):
        HIGHEST = "highest", "Highest"
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"
        LOWEST = "lowest", "Lowest"

    project = models.ForeignKey(JiraProject, on_delete=models.CASCADE, related_name="issues")
    number = models.PositiveIntegerField(default=0, editable=False)
    issue_type = models.ForeignKey(IssueType, on_delete=models.PROTECT, related_name="issues")
    status = models.ForeignKey(IssueStatus, on_delete=models.PROTECT, related_name="issues")
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    summary = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    assignees = models.ManyToManyField(
        User,
        blank=True,
        related_name="jira_issues_assigned",
        help_text="One or more people (like shared ownership).",
    )
    reporter = models.ForeignKey(User, on_delete=models.PROTECT, related_name="reported_jira_issues")
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="subtasks")
    epic = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children_in_epic")
    labels = models.ManyToManyField(TenantLabel, blank=True, related_name="issues")
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Due date (shown on board card like Jira).",
    )
    board_order = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Order within a status column on the board (top-level issues only).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("project", "number")]

    @property
    def issue_key(self):
        return f"{self.project.key}-{self.number}"

    def __str__(self):
        return f"{self.issue_key} {self.summary[:40]}"

    def clean(self):
        if self.parent_id and self.parent.project_id != self.project_id:
            raise ValidationError({"parent": "Parent issue must belong to the same project."})
        if self.epic_id:
            if self.epic.project_id != self.project_id:
                raise ValidationError({"epic": "Epic must belong to the same project."})
            if self.epic.issue_type.name != "Epic":
                raise ValidationError({"epic": "Linked epic must be an issue of type Epic."})

    def save(self, *args, **kwargs):
        if self.pk is None:
            with transaction.atomic():
                agg = Issue.objects.filter(project=self.project).aggregate(Max("number"))
                self.number = (agg["number__max"] or 0) + 1
                if not self.parent_id:
                    bo = (
                        Issue.objects.filter(
                            project=self.project,
                            status_id=self.status_id,
                            parent__isnull=True,
                        ).aggregate(Max("board_order"))["board_order__max"]
                    )
                    self.board_order = (bo if bo is not None else -1) + 1
        self.full_clean()
        super().save(*args, **kwargs)


class IssueComment(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
