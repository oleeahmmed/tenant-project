from django import forms

from foundation.models import Warehouse

from .models import POSRegister


class POSRegisterForm(forms.ModelForm):
    class Meta:
        model = POSRegister
        fields = ["code", "name", "default_warehouse", "is_active"]
        widgets = {
            "code": forms.TextInput(attrs={"class": "inv-list-control"}),
            "name": forms.TextInput(attrs={"class": "inv-list-control"}),
            "default_warehouse": forms.Select(attrs={"class": "inv-list-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "rounded border-border"}),
        }

    def __init__(self, *args, tenant, **kwargs):
        self._tenant = tenant
        super().__init__(*args, **kwargs)
        # Set before validation so POSRegister.clean() can match warehouse.tenant to tenant.
        if tenant is not None:
            self.instance.tenant = tenant
        self.fields["default_warehouse"].queryset = Warehouse.objects.filter(tenant=tenant, is_active=True).order_by(
            "code"
        )

    def clean(self):
        cleaned = super().clean()
        wh = cleaned.get("default_warehouse")
        tid = self.instance.tenant_id or (self._tenant.pk if self._tenant else None)
        if wh and tid and wh.tenant_id != tid:
            self.add_error("default_warehouse", "Warehouse must belong to the same tenant.")
        return cleaned


class OpenSessionForm(forms.Form):
    register = forms.ModelChoiceField(
        queryset=POSRegister.objects.none(),
        widget=forms.Select(attrs={"class": "inv-list-control"}),
    )
    opening_cash = forms.DecimalField(
        max_digits=18,
        decimal_places=4,
        initial=0,
        widget=forms.NumberInput(attrs={"class": "inv-list-control", "step": "0.0001"}),
    )

    def __init__(self, *args, tenant, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["register"].queryset = POSRegister.objects.filter(tenant=tenant, is_active=True).order_by("code")


class CloseSessionForm(forms.Form):
    closing_cash = forms.DecimalField(
        max_digits=18,
        decimal_places=4,
        widget=forms.NumberInput(attrs={"class": "inv-list-control", "step": "0.0001"}),
    )
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "inv-list-control", "rows": 2}))
