from django import forms

from hrm.models import Department, Employee

from .models import Application, JobPosting

_ctrl = "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"


class JobPostingForm(forms.ModelForm):
    class Meta:
        model = JobPosting
        fields = [
            "title",
            "department",
            "location",
            "employment_type",
            "openings",
            "description",
            "requirements",
            "status",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": _ctrl}),
            "department": forms.Select(attrs={"class": _ctrl}),
            "location": forms.TextInput(attrs={"class": _ctrl}),
            "employment_type": forms.Select(attrs={"class": _ctrl}),
            "openings": forms.NumberInput(attrs={"class": _ctrl, "min": "1"}),
            "description": forms.Textarea(attrs={"rows": 5, "class": _ctrl}),
            "requirements": forms.Textarea(attrs={"rows": 4, "class": _ctrl}),
            "status": forms.Select(attrs={"class": _ctrl}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["department"].queryset = Department.objects.filter(tenant=tenant)
        self.fields["department"].required = False
        self.fields["department"].empty_label = "— Any / not set —"


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = [
            "full_name",
            "email",
            "phone",
            "cover_letter",
            "resume",
            "stage",
            "internal_notes",
            "hired_employee",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": _ctrl}),
            "email": forms.EmailInput(attrs={"class": _ctrl}),
            "phone": forms.TextInput(attrs={"class": _ctrl}),
            "cover_letter": forms.Textarea(attrs={"rows": 4, "class": _ctrl}),
            "resume": forms.ClearableFileInput(
                attrs={"class": _ctrl + " file:mr-2 file:rounded file:border-0 file:bg-muted file:px-2 file:py-1"}
            ),
            "stage": forms.Select(attrs={"class": _ctrl}),
            "internal_notes": forms.Textarea(attrs={"rows": 4, "class": _ctrl}),
            "hired_employee": forms.Select(attrs={"class": _ctrl}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["hired_employee"].queryset = Employee.objects.filter(
                tenant=tenant
            ).order_by("full_name")
        self.fields["hired_employee"].required = False
        self.fields["hired_employee"].empty_label = "— Not linked yet —"


class ApplicationQuickCreateForm(forms.ModelForm):
    """Add candidate from list / job page (no internal notes)."""

    class Meta:
        model = Application
        fields = ["full_name", "email", "phone", "cover_letter", "resume"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": _ctrl}),
            "email": forms.EmailInput(attrs={"class": _ctrl}),
            "phone": forms.TextInput(attrs={"class": _ctrl}),
            "cover_letter": forms.Textarea(attrs={"rows": 3, "class": _ctrl}),
            "resume": forms.ClearableFileInput(attrs={"class": _ctrl}),
        }
