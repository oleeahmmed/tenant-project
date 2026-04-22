from django import forms

from .models import Payment, Property, RentalAgreement, RentalTenant

# Match ``inventory.forms`` control styling (Tailwind).
_CTRL = (
    "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm "
    "focus:outline-none focus:ring-2 focus:ring-ring"
)
_SEL = _CTRL + " text-xs inv-ts-local"
_CHK = "h-4 w-4 rounded border-border text-primary focus:ring-2 focus:ring-ring"
_FILE = _CTRL + " text-xs file:mr-3 file:rounded-md file:border-0 file:bg-muted file:px-3 file:py-1.5 file:text-xs file:font-medium"


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            "property_type",
            "property_number",
            "floor_number",
            "size_sqft",
            "bedrooms",
            "bathrooms",
            "monthly_rent",
            "status",
            "description",
        ]
        widgets = {
            "property_type": forms.Select(attrs={"class": _SEL}),
            "property_number": forms.TextInput(attrs={"class": _CTRL + " text-xs", "autocomplete": "off"}),
            "floor_number": forms.TextInput(attrs={"class": _CTRL + " text-xs", "autocomplete": "off"}),
            "size_sqft": forms.NumberInput(attrs={"class": _CTRL + " text-xs", "step": "any"}),
            "bedrooms": forms.NumberInput(attrs={"class": _CTRL + " text-xs", "min": "0"}),
            "bathrooms": forms.NumberInput(attrs={"class": _CTRL + " text-xs", "min": "0"}),
            "monthly_rent": forms.NumberInput(attrs={"class": _CTRL + " text-xs", "step": "any"}),
            "status": forms.Select(attrs={"class": _SEL}),
            "description": forms.Textarea(attrs={"rows": 3, "class": _CTRL + " text-xs"}),
        }


class RentalTenantForm(forms.ModelForm):
    class Meta:
        model = RentalTenant
        fields = [
            "name",
            "mobile_number",
            "email",
            "nid_number",
            "permanent_address",
            "emergency_contact_name",
            "emergency_contact_number",
            "occupation",
            "family_members_count",
            "profile_photo",
            "nid_photo_front",
            "nid_photo_back",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": _CTRL + " text-xs", "autocomplete": "name"}),
            "mobile_number": forms.TextInput(attrs={"class": _CTRL + " text-xs", "autocomplete": "tel"}),
            "email": forms.EmailInput(attrs={"class": _CTRL + " text-xs", "autocomplete": "email"}),
            "nid_number": forms.TextInput(attrs={"class": _CTRL + " text-xs", "autocomplete": "off"}),
            "permanent_address": forms.Textarea(attrs={"rows": 3, "class": _CTRL + " text-xs"}),
            "emergency_contact_name": forms.TextInput(attrs={"class": _CTRL + " text-xs"}),
            "emergency_contact_number": forms.TextInput(attrs={"class": _CTRL + " text-xs", "autocomplete": "tel"}),
            "occupation": forms.TextInput(attrs={"class": _CTRL + " text-xs"}),
            "family_members_count": forms.NumberInput(attrs={"class": _CTRL + " text-xs", "min": "1"}),
            "profile_photo": forms.ClearableFileInput(attrs={"class": _FILE}),
            "nid_photo_front": forms.ClearableFileInput(attrs={"class": _FILE}),
            "nid_photo_back": forms.ClearableFileInput(attrs={"class": _FILE}),
            "is_active": forms.CheckboxInput(attrs={"class": _CHK}),
        }


class RentalAgreementForm(forms.ModelForm):
    class Meta:
        model = RentalAgreement
        fields = [
            "property",
            "rental_tenant",
            "start_date",
            "end_date",
            "monthly_rent",
            "advance_amount",
            "advance_months",
            "service_charge",
            "rent_due_date",
            "agreement_document",
            "status",
            "notes",
        ]
        widgets = {
            "property": forms.Select(attrs={"class": _SEL}),
            "rental_tenant": forms.Select(attrs={"class": _SEL}),
            "start_date": forms.DateInput(attrs={"type": "date", "class": _CTRL + " text-xs"}),
            "end_date": forms.DateInput(attrs={"type": "date", "class": _CTRL + " text-xs"}),
            "monthly_rent": forms.NumberInput(attrs={"class": _CTRL + " text-xs", "step": "any"}),
            "advance_amount": forms.NumberInput(attrs={"class": _CTRL + " text-xs", "step": "any"}),
            "advance_months": forms.NumberInput(attrs={"class": _CTRL + " text-xs", "min": "0"}),
            "service_charge": forms.NumberInput(attrs={"class": _CTRL + " text-xs", "step": "any"}),
            "rent_due_date": forms.NumberInput(attrs={"class": _CTRL + " text-xs", "min": "1", "max": "31"}),
            "agreement_document": forms.ClearableFileInput(attrs={"class": _FILE}),
            "status": forms.Select(attrs={"class": _SEL}),
            "notes": forms.Textarea(attrs={"rows": 3, "class": _CTRL + " text-xs"}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant is not None:
            self.fields["property"].queryset = Property.objects.filter(tenant=tenant).order_by("property_number")
            self.fields["rental_tenant"].queryset = RentalTenant.objects.filter(tenant=tenant, is_active=True).order_by("name")


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = [
            "agreement",
            "payment_type",
            "payment_month",
            "amount",
            "payment_date",
            "payment_method",
            "transaction_reference",
            "notes",
        ]
        widgets = {
            "agreement": forms.Select(attrs={"class": _SEL}),
            "payment_type": forms.Select(attrs={"class": _SEL}),
            "payment_month": forms.DateInput(attrs={"type": "date", "class": _CTRL + " text-xs"}),
            "amount": forms.NumberInput(attrs={"class": _CTRL + " text-xs", "step": "any"}),
            "payment_date": forms.DateInput(attrs={"type": "date", "class": _CTRL + " text-xs"}),
            "payment_method": forms.Select(attrs={"class": _SEL}),
            "transaction_reference": forms.TextInput(attrs={"class": _CTRL + " text-xs", "autocomplete": "off"}),
            "notes": forms.Textarea(attrs={"rows": 3, "class": _CTRL + " text-xs"}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant is not None:
            self.fields["agreement"].queryset = RentalAgreement.objects.filter(tenant=tenant).order_by("-start_date")
