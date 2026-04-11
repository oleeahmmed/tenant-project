from django import forms

from .models import SupportTicket, SupportTicketMessage


class SupportTicketCreateForm(forms.ModelForm):
    body = forms.CharField(
        label="Describe the issue",
        widget=forms.Textarea(attrs={"rows": 6, "class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"}),
    )

    class Meta:
        model = SupportTicket
        fields = ("subject", "priority", "product_area")
        widgets = {
            "subject": forms.TextInput(
                attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"}
            ),
            "priority": forms.Select(attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"}),
            "product_area": forms.Select(attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"}),
        }


class SupportReplyForm(forms.Form):
    body = forms.CharField(
        label="Reply",
        widget=forms.Textarea(attrs={"rows": 4, "class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"}),
    )
    is_internal = forms.BooleanField(
        required=False,
        label="Internal note (agents only)",
    )


class SupportTicketAgentForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ("status", "priority", "assignee", "product_area")
        widgets = {
            "status": forms.Select(attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"}),
            "priority": forms.Select(attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"}),
            "assignee": forms.Select(attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"}),
            "product_area": forms.Select(attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"}),
        }
