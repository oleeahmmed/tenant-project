from django import forms
from django.core.exceptions import ValidationError

from auth_tenants.models import User

from .models import Issue, IssueComment, IssueStatus, IssueType, JiraProject, ProjectTeam, TenantLabel
from .services.assignees import assignable_users_for_project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = JiraProject
        fields = ["key", "name", "description", "lead", "is_active"]
        widgets = {
            "key": forms.TextInput(attrs={"class": "inv-list-control", "placeholder": "e.g. ACME"}),
            "name": forms.TextInput(attrs={"class": "inv-list-control"}),
            "description": forms.Textarea(attrs={"class": "inv-list-control min-h-[100px]", "rows": 4}),
            "lead": forms.Select(attrs={"class": "inv-list-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "rounded border-border"}),
        }

    def __init__(self, *args, tenant, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lead"].queryset = User.objects.filter(tenant=tenant).order_by("name")
        self.fields["lead"].required = False


class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = [
            "summary",
            "description",
            "issue_type",
            "status",
            "priority",
            "due_date",
            "assignees",
            "parent",
            "epic",
            "labels",
        ]
        widgets = {
            "summary": forms.TextInput(attrs={"class": "inv-list-control"}),
            "description": forms.Textarea(attrs={"class": "inv-list-control min-h-[120px]", "rows": 6}),
            "issue_type": forms.Select(attrs={"class": "inv-list-control"}),
            "status": forms.Select(attrs={"class": "inv-list-control"}),
            "priority": forms.Select(attrs={"class": "inv-list-control"}),
            "due_date": forms.DateInput(attrs={"class": "inv-list-control", "type": "date"}),
            "assignees": forms.SelectMultiple(
                attrs={"class": "inv-list-control min-h-[100px]", "size": 6, "data-jira-assignees": "1"}
            ),
            "parent": forms.Select(attrs={"class": "inv-list-control"}),
            "epic": forms.Select(attrs={"class": "inv-list-control"}),
            "labels": forms.SelectMultiple(attrs={"class": "inv-list-control min-h-[80px]", "size": 4}),
        }

    def __init__(self, *args, project, tenant, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        self.fields["issue_type"].queryset = IssueType.objects.filter(project=project).order_by("order", "name")
        self.fields["status"].queryset = IssueStatus.objects.filter(project=project).order_by("order", "name")
        self.fields["assignees"].queryset = assignable_users_for_project(project)
        self.fields["assignees"].required = False
        self.fields["parent"].queryset = Issue.objects.filter(project=project).order_by("-number")
        self.fields["parent"].required = False
        self.fields["epic"].queryset = Issue.objects.filter(project=project, issue_type__name="Epic").order_by(
            "-number"
        )
        self.fields["epic"].required = False
        self.fields["labels"].queryset = TenantLabel.objects.filter(tenant=tenant).order_by("name")

    def clean(self):
        cleaned = super().clean()
        parent = cleaned.get("parent")
        itype = cleaned.get("issue_type")
        if parent and itype and itype.name != "Sub-task":
            raise ValidationError({"issue_type": "When a parent issue is set, use issue type Sub-task."})
        if parent and parent.project_id != self.project.id:
            raise ValidationError({"parent": "Parent must belong to this project."})
        assignees = cleaned.get("assignees")
        if assignees is not None:
            allowed = assignable_users_for_project(self.project)
            allowed_ids = set(allowed.values_list("pk", flat=True))
            for u in assignees:
                if u.pk not in allowed_ids:
                    raise ValidationError(
                        {"assignees": "Assignees must be members of a project team (or add teams under the project)."}
                    )
        return cleaned


class ProjectTeamForm(forms.ModelForm):
    class Meta:
        model = ProjectTeam
        fields = ["name", "order", "members"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "inv-list-control", "placeholder": "e.g. Backend"}),
            "order": forms.NumberInput(attrs={"class": "inv-list-control", "step": "1"}),
            "members": forms.SelectMultiple(attrs={"class": "inv-list-control min-h-[120px]", "size": 8}),
        }

    def __init__(self, *args, project, **kwargs):
        self.project = project
        super().__init__(*args, **kwargs)
        self.fields["members"].queryset = User.objects.filter(tenant=project.tenant, is_active=True).order_by("name")
        self.fields["members"].required = False
        self.fields["order"].required = False


class IssueCommentForm(forms.ModelForm):
    class Meta:
        model = IssueComment
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(
                attrs={
                    "class": "inv-list-control min-h-[80px]",
                    "rows": 3,
                    "placeholder": "Add a comment…",
                }
            ),
        }
