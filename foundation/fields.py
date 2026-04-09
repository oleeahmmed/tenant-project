"""Form fields that validate FK by tenant without loading full querysets (for autocomplete UIs)."""

from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError


class TenantScopedModelChoiceField(forms.ModelChoiceField):
    """
    Validates selected pk against ``tenant_id`` only; queryset stays empty for fast loads.
    Pair with Tom Select / remote autocomplete on the widget.
    """

    def __init__(self, *args, tenant=None, queryset=None, **kwargs):
        self._tenant = tenant
        if queryset is None:
            model = kwargs.pop("model", None)
            if model is None:
                raise ValueError("TenantScopedModelChoiceField requires queryset or model=")
            queryset = model.objects.none()
        # Django 5+ ModelChoiceField defaults empty_label to "---------" even when required=True
        # and initial is None — that forces a dash-only <option>. We want a truly blank control.
        required = kwargs.get("required", True)
        if required:
            kwargs["empty_label"] = None
        elif "empty_label" not in kwargs:
            kwargs["empty_label"] = ""
        super().__init__(*args, queryset=queryset, **kwargs)

    def to_python(self, value):
        if value in self.empty_values:
            return None
        try:
            key = int(value)
        except (ValueError, TypeError):
            raise ValidationError(self.error_messages["invalid_choice"], code="invalid_choice")
        if self._tenant is None:
            raise ValidationError(self.error_messages["invalid_choice"], code="invalid_choice")
        Model = self.queryset.model
        try:
            return Model.objects.get(pk=key, tenant_id=self._tenant.pk)
        except Model.DoesNotExist:
            raise ValidationError(self.error_messages["invalid_choice"], code="invalid_choice")

    def validate(self, value):
        if value in self.empty_values and self.required:
            raise ValidationError(self.error_messages["required"], code="required")
