from django import forms

from .models import SchoolClass, Section, Staff, Student

_CTRL = (
    "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm "
    "focus:outline-none focus:ring-2 focus:ring-ring"
)
_SEL = _CTRL + " text-xs inv-ts-local"
_CHK = "h-4 w-4 rounded border-border text-primary focus:ring-2 focus:ring-ring"
_FILE = _CTRL + " text-xs file:mr-3 file:rounded-md file:border-0 file:bg-muted file:px-3 file:py-1.5 file:text-xs file:font-medium"


class StudentForm(forms.ModelForm):
    registration_number = forms.CharField(
        required=False,
        help_text="Optional — leave blank to auto-generate.",
        widget=forms.TextInput(attrs={"class": _CTRL + " text-xs", "autocomplete": "off"}),
    )

    class Meta:
        model = Student
        exclude = ("tenant", "created_by", "created_at", "updated_at")
        widgets = {
            "roll_number": forms.TextInput(attrs={"class": _CTRL + " text-xs", "autocomplete": "off"}),
            "name": forms.TextInput(attrs={"class": _CTRL + " text-xs", "autocomplete": "name"}),
            "date_of_birth": forms.DateInput(attrs={"type": "date", "class": _CTRL + " text-xs"}),
            "gender": forms.Select(attrs={"class": _SEL}),
            "blood_group": forms.TextInput(attrs={"class": _CTRL + " text-xs"}),
            "religion": forms.TextInput(attrs={"class": _CTRL + " text-xs"}),
            "nationality": forms.TextInput(attrs={"class": _CTRL + " text-xs"}),
            "current_class": forms.Select(attrs={"class": _SEL}),
            "current_section": forms.Select(attrs={"class": _SEL}),
            "admission_date": forms.DateInput(attrs={"type": "date", "class": _CTRL + " text-xs"}),
            "father_name": forms.TextInput(attrs={"class": _CTRL + " text-xs"}),
            "father_mobile": forms.TextInput(attrs={"class": _CTRL + " text-xs", "autocomplete": "tel"}),
            "father_occupation": forms.TextInput(attrs={"class": _CTRL + " text-xs"}),
            "mother_name": forms.TextInput(attrs={"class": _CTRL + " text-xs"}),
            "mother_mobile": forms.TextInput(attrs={"class": _CTRL + " text-xs", "autocomplete": "tel"}),
            "guardian_name": forms.TextInput(attrs={"class": _CTRL + " text-xs"}),
            "guardian_mobile": forms.TextInput(attrs={"class": _CTRL + " text-xs", "autocomplete": "tel"}),
            "guardian_relation": forms.TextInput(attrs={"class": _CTRL + " text-xs"}),
            "permanent_address": forms.Textarea(attrs={"rows": 2, "class": _CTRL + " text-xs"}),
            "present_address": forms.Textarea(attrs={"rows": 2, "class": _CTRL + " text-xs"}),
            "previous_school": forms.TextInput(attrs={"class": _CTRL + " text-xs"}),
            "transfer_certificate_number": forms.TextInput(attrs={"class": _CTRL + " text-xs"}),
            "profile_photo": forms.ClearableFileInput(attrs={"class": _FILE}),
            "birth_certificate_photo": forms.ClearableFileInput(attrs={"class": _FILE}),
            "status": forms.Select(attrs={"class": _SEL}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        self.tenant = tenant
        super().__init__(*args, **kwargs)
        if tenant is not None:
            self.fields["current_class"].queryset = (
                SchoolClass.objects.filter(tenant=tenant).select_related("academic_year").order_by("numeric_level", "name")
            )
            self.fields["current_section"].queryset = (
                Section.objects.filter(tenant=tenant).select_related("class_level").order_by("class_level__numeric_level", "name")
            )

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.tenant is not None:
            obj.tenant = self.tenant
        if commit:
            obj.save()
        return obj


class StaffForm(forms.ModelForm):
    employee_id = forms.CharField(
        required=False,
        help_text="Optional — leave blank to auto-generate.",
        widget=forms.TextInput(attrs={"class": _CTRL + " text-xs", "autocomplete": "off"}),
    )

    class Meta:
        model = Staff
        exclude = ("tenant", "user", "created_by", "created_at", "updated_at")
        widgets = {
            "name": forms.TextInput(attrs={"class": _CTRL + " text-xs", "autocomplete": "name"}),
            "mobile_number": forms.TextInput(attrs={"class": _CTRL + " text-xs", "autocomplete": "tel"}),
            "email": forms.EmailInput(attrs={"class": _CTRL + " text-xs", "autocomplete": "email"}),
            "nid_number": forms.TextInput(attrs={"class": _CTRL + " text-xs"}),
            "date_of_birth": forms.DateInput(attrs={"type": "date", "class": _CTRL + " text-xs"}),
            "gender": forms.Select(attrs={"class": _SEL}),
            "blood_group": forms.TextInput(attrs={"class": _CTRL + " text-xs"}),
            "designation": forms.Select(attrs={"class": _SEL}),
            "department": forms.TextInput(attrs={"class": _CTRL + " text-xs"}),
            "joining_date": forms.DateInput(attrs={"type": "date", "class": _CTRL + " text-xs"}),
            "qualification": forms.Textarea(attrs={"rows": 2, "class": _CTRL + " text-xs"}),
            "experience_years": forms.NumberInput(attrs={"class": _CTRL + " text-xs", "min": "0"}),
            "salary": forms.NumberInput(attrs={"class": _CTRL + " text-xs", "step": "any"}),
            "permanent_address": forms.Textarea(attrs={"rows": 2, "class": _CTRL + " text-xs"}),
            "present_address": forms.Textarea(attrs={"rows": 2, "class": _CTRL + " text-xs"}),
            "emergency_contact_name": forms.TextInput(attrs={"class": _CTRL + " text-xs"}),
            "emergency_contact_number": forms.TextInput(attrs={"class": _CTRL + " text-xs"}),
            "profile_photo": forms.ClearableFileInput(attrs={"class": _FILE}),
            "nid_photo_front": forms.ClearableFileInput(attrs={"class": _FILE}),
            "nid_photo_back": forms.ClearableFileInput(attrs={"class": _FILE}),
            "status": forms.Select(attrs={"class": _SEL}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        self.tenant = tenant
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.tenant is not None:
            obj.tenant = self.tenant
        if commit:
            obj.save()
        return obj
