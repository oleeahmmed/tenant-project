from django import forms

from foundation.models import Customer
from jiraclone.models import JiraProject

from .models import VaultCategory, VaultEntry, VaultFileAttachment, VaultSharedEntry


class VaultCategoryForm(forms.ModelForm):
    class Meta:
        model = VaultCategory
        fields = ["customer", "name", "description", "is_active"]
        widgets = {
            "customer": forms.Select(attrs={"class": "inv-list-control"}),
            "name": forms.TextInput(attrs={"class": "inv-list-control"}),
            "description": forms.Textarea(attrs={"class": "inv-list-control min-h-[90px]", "rows": 4}),
            "is_active": forms.CheckboxInput(attrs={"class": "rounded border-border"}),
        }

    def __init__(self, *args, tenant, **kwargs):
        selected_customer_id = kwargs.pop("selected_customer_id", None)
        super().__init__(*args, **kwargs)
        self.instance.tenant = tenant
        self.fields["customer"].queryset = Customer.objects.filter(tenant=tenant, is_active=True).order_by("name")
        self.fields["customer"].required = True

        if selected_customer_id and not self.instance.pk and "customer" not in self.initial:
            self.initial["customer"] = selected_customer_id


class VaultEntryForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "inv-list-control", "autocomplete": "off"}),
    )
    attachment_file = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={"class": "inv-list-control"}),
    )
    attachment_title = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "inv-list-control"}),
    )

    class Meta:
        model = VaultEntry
        fields = ["category", "project", "name", "url", "username", "password", "notes", "is_favorite"]
        widgets = {
            "category": forms.Select(attrs={"class": "inv-list-control"}),
            "project": forms.Select(attrs={"class": "inv-list-control"}),
            "name": forms.TextInput(attrs={"class": "inv-list-control"}),
            "url": forms.URLInput(attrs={"class": "inv-list-control"}),
            "username": forms.TextInput(attrs={"class": "inv-list-control"}),
            "notes": forms.Textarea(attrs={"class": "inv-list-control min-h-[110px]", "rows": 5}),
            "is_favorite": forms.CheckboxInput(attrs={"class": "rounded border-border"}),
        }

    def __init__(self, *args, tenant, **kwargs):
        selected_customer_id = kwargs.pop("selected_customer_id", None)
        super().__init__(*args, **kwargs)
        self.instance.tenant = tenant
        categories = VaultCategory.objects.filter(tenant=tenant, is_active=True).select_related("customer")
        projects = JiraProject.objects.filter(tenant=tenant, is_active=True).select_related("customer")
        if selected_customer_id and str(selected_customer_id).isdigit():
            categories = categories.filter(customer_id=int(selected_customer_id))
            projects = projects.filter(customer_id=int(selected_customer_id))
            if not self.instance.pk and "category" not in self.initial:
                first_category = categories.order_by("name").first()
                if first_category:
                    self.initial["category"] = first_category.pk
            if not self.instance.pk and "project" not in self.initial:
                first_project = projects.order_by("key").first()
                if first_project:
                    self.initial["project"] = first_project.pk
        elif self.instance.pk and self.instance.category_id:
            projects = projects.filter(customer_id=self.instance.category.customer_id)
        self.fields["project"].queryset = projects.order_by("key")
        self.fields["project"].required = True
        self.fields["category"].queryset = categories.order_by("customer__name", "name")
        self.fields["category"].label_from_instance = (
            lambda obj: f"{(obj.customer.name if obj.customer_id else 'Unknown customer')} / {obj.name}"
        )
        if self.instance.pk:
            self.fields["password"].help_text = "Leave blank to keep existing encrypted password."

    def clean(self):
        cleaned = super().clean()
        category = cleaned.get("category")
        project = cleaned.get("project")
        if category and project and project.customer_id != category.customer_id:
            self.add_error("project", "Project customer must match selected category customer.")
        return cleaned


class VaultFileAttachmentForm(forms.ModelForm):
    class Meta:
        model = VaultFileAttachment
        fields = ["file", "title"]
        widgets = {
            "file": forms.ClearableFileInput(attrs={"class": "inv-list-control"}),
            "title": forms.TextInput(attrs={"class": "inv-list-control"}),
        }


class VaultShareForm(forms.ModelForm):
    class Meta:
        model = VaultSharedEntry
        fields = ["shared_with_email", "permission", "expires_at", "is_active"]
        widgets = {
            "shared_with_email": forms.EmailInput(attrs={"class": "inv-list-control"}),
            "permission": forms.Select(attrs={"class": "inv-list-control"}),
            "expires_at": forms.DateTimeInput(attrs={"class": "inv-list-control", "type": "datetime-local"}),
            "is_active": forms.CheckboxInput(attrs={"class": "rounded border-border"}),
        }
