from django import forms

from auth_tenants.models import User


class GroupChatForm(forms.Form):
    title = forms.CharField(max_length=255, label="Group name")
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=True,
        widget=forms.SelectMultiple(attrs={"class": "wa-select", "size": "8"}),
    )

    def __init__(self, *args, tenant_users_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant_users_queryset is not None:
            self.fields["members"].queryset = tenant_users_queryset


class ChatMessageForm(forms.Form):
    body = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 1,
                "class": "inv-list-control wa-compose-input",
                "placeholder": "Type a message",
                "autocomplete": "off",
            }
        ),
    )
    # FileField: ImageField rejects many valid uploads; view assigns to model ImageField after checks
    image = forms.FileField(required=False)
    file = forms.FileField(required=False)
    voice = forms.FileField(required=False)
