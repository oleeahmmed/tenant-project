from django import forms
from django.forms import inlineformset_factory
from django.forms.models import BaseInlineFormSet

from foundation.fields import TenantScopedModelChoiceField
from foundation.models import Customer, Product, Warehouse

from .models import (
    GoodsIssue,
    GoodsIssueItem,
    InventoryTransfer,
    InventoryTransferItem,
    StockAdjustment,
    StockAdjustmentItem,
)

_ctrl = "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
# Dense inputs for SAP-style line table
_tbl = (
    "inv-line-input w-full min-w-[4.5rem] rounded border border-border bg-background px-2 py-1.5 "
    "text-xs focus:outline-none focus:ring-1 focus:ring-ring"
)
_tbl_sel = (
    "inv-line-select w-full min-w-[10rem] max-w-[20rem] rounded border border-border bg-background "
    "px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-ring"
)


# Same routes as ``foundation.api.urls`` under ``config.urls`` → ``api/foundation/``.
# Use literal paths here so importing this module never calls ``reverse()`` while URLconf
# is still loading (avoids circular import / ImproperlyConfigured on ``config.urls``).
_FOUNDATION_API = {
    "autocomplete_warehouses": "/api/foundation/autocomplete/warehouses/",
    "autocomplete_products": "/api/foundation/autocomplete/products/",
    "autocomplete_customers": "/api/foundation/autocomplete/customers/",
}


def _ac_url(name: str) -> str:
    return _FOUNDATION_API[name]


class StockAdjustmentForm(forms.ModelForm):
    """Code + name snapshot (no FK). Picker fills codes; server validates and syncs name from Warehouse."""

    # CharField + Select: Tom Select posts dynamic codes; ChoiceField rejects values not in ``choices``.
    warehouse_pick = forms.CharField(
        label="Warehouse",
        required=False,
        widget=forms.Select(
            attrs={
                "class": _ctrl + " text-xs inv-sa-warehouse-ts",
            }
        ),
    )

    class Meta:
        model = StockAdjustment
        fields = [
            "adjustment_date",
            "adjustment_type",
            "warehouse_code",
            "warehouse_name",
            "reason",
            "requested_by",
            "notes",
        ]
        widgets = {
            "adjustment_date": forms.DateInput(attrs={"type": "date", "class": _ctrl + " text-xs"}),
            "adjustment_type": forms.Select(attrs={"class": _ctrl + " text-xs"}),
            "warehouse_code": forms.HiddenInput(attrs={"id": "id_warehouse_code"}),
            "warehouse_name": forms.HiddenInput(attrs={"id": "id_warehouse_name"}),
            "reason": forms.Textarea(attrs={"rows": 2, "class": _ctrl + " text-xs"}),
            "requested_by": forms.TextInput(attrs={"class": _ctrl + " text-xs"}),
            "notes": forms.Textarea(attrs={"rows": 2, "class": _ctrl + " text-xs"}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        self.tenant = tenant
        super().__init__(*args, **kwargs)
        self.fields["warehouse_pick"].widget.attrs["data-autocomplete-url"] = _ac_url("autocomplete_warehouses")
        wh = self.fields["warehouse_pick"].widget
        wh.choices = [("", "")]
        if self.is_bound:
            code = (
                (self.data.get(self.add_prefix("warehouse_pick")) or "")
                or (self.data.get(self.add_prefix("warehouse_code")) or "")
            ).strip()
            if code:
                name = (self.data.get(self.add_prefix("warehouse_name")) or "").strip()
                if self.tenant and not name:
                    obj = Warehouse.objects.filter(tenant_id=self.tenant.pk, code=code).only("name").first()
                    name = obj.name if obj else ""
                label = f"{code} — {name}" if name else code
                wh.choices = [(code, label)]
                self.fields["warehouse_pick"].initial = code
        if self.instance.pk:
            c = (self.instance.warehouse_code or "").strip()
            if c:
                n = (self.instance.warehouse_name or "").strip()
                label = f"{c} — {n}" if n else c
                wh.choices = [(c, label)]
                self.fields["warehouse_pick"].initial = c

    def clean(self):
        data = super().clean()
        code = (data.get("warehouse_code") or data.get("warehouse_pick") or "").strip()
        data["warehouse_code"] = code
        if not code:
            raise forms.ValidationError({"warehouse_code": "Select a warehouse."})
        if self.tenant:
            wh = Warehouse.objects.filter(tenant_id=self.tenant.pk, code=code).first()
            if not wh:
                raise forms.ValidationError(
                    {"warehouse_code": "Unknown warehouse code for this workspace."}
                )
            data["warehouse_name"] = wh.name
        return data


class TenantInlineFormSet(BaseInlineFormSet):
    """Passes ``tenant`` into each line form for queryset scoping."""

    def __init__(self, *args, tenant=None, **kwargs):
        self.tenant = tenant
        super().__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        kwargs["tenant"] = self.tenant
        return super()._construct_form(i, **kwargs)


class StockAdjustmentItemForm(forms.ModelForm):
    # CharField + Select: Tom Select posts dynamic SKUs; ChoiceField rejects unknown values.
    product_pick = forms.CharField(
        label="Item",
        required=False,
        widget=forms.Select(
            attrs={
                "class": _tbl_sel + " inv-sa-product-ts",
            }
        ),
    )

    class Meta:
        model = StockAdjustmentItem
        fields = [
            "product_sku",
            "product_name",
            "counted_quantity",
            "unit_cost",
            "line_reason",
            "line_no",
        ]
        widgets = {
            "product_sku": forms.HiddenInput(attrs={"class": "inv-sa-product-sku"}),
            "product_name": forms.HiddenInput(attrs={"class": "inv-sa-product-name"}),
            "counted_quantity": forms.NumberInput(
                attrs={"class": _tbl + " inv-line-counted", "step": "any"}
            ),
            "unit_cost": forms.NumberInput(attrs={"class": _tbl + " inv-line-unit-cost", "step": "any"}),
            "line_reason": forms.TextInput(attrs={"class": _tbl}),
            "line_no": forms.HiddenInput(),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        self.tenant = tenant
        super().__init__(*args, **kwargs)
        self.fields["product_pick"].widget.attrs["data-autocomplete-url"] = _ac_url("autocomplete_products")
        pw = self.fields["product_pick"].widget
        pw.choices = [("", "")]
        if self.is_bound:
            sku = (
                (self.data.get(self.add_prefix("product_pick")) or "")
                or (self.data.get(self.add_prefix("product_sku")) or "")
            ).strip()
            if sku:
                name = (self.data.get(self.add_prefix("product_name")) or "").strip()
                if self.tenant and not name:
                    obj = Product.objects.filter(tenant_id=self.tenant.pk, sku=sku).only("name").first()
                    name = obj.name if obj else ""
                label = f"{sku} — {name}" if name else sku
                pw.choices = [(sku, label)]
                self.fields["product_pick"].initial = sku
        if self.instance.pk:
            sku = (self.instance.product_sku or "").strip()
            if sku:
                n = (self.instance.product_name or "").strip()
                label = f"{sku} — {n}" if n else sku
                pw.choices = [(sku, label)]
                self.fields["product_pick"].initial = sku

    def clean(self):
        data = super().clean()
        sku = (data.get("product_sku") or data.get("product_pick") or "").strip()
        data["product_sku"] = sku
        reason = (data.get("line_reason") or "").strip()
        raw = data.get("counted_quantity")
        s = str(raw).strip() if raw is not None else ""
        try:
            nz = float(s) if s else 0.0
        except ValueError:
            nz = None
        spare = not sku and not reason and (s == "" or nz == 0)
        if spare:
            return data
        if not sku:
            raise forms.ValidationError({"product_sku": "Select a product."})
        if self.tenant:
            prod = Product.objects.filter(tenant_id=self.tenant.pk, sku=sku).first()
            if not prod:
                raise forms.ValidationError(
                    {"product_sku": "Unknown product SKU for this workspace."}
                )
            data["product_name"] = prod.name
        return data


StockAdjustmentItemFormSet = inlineformset_factory(
    StockAdjustment,
    StockAdjustmentItem,
    form=StockAdjustmentItemForm,
    formset=TenantInlineFormSet,
    extra=1,
    can_delete=True,
)


class GoodsIssueForm(forms.ModelForm):
    class Meta:
        model = GoodsIssue
        fields = [
            "issue_date",
            "issue_type",
            "warehouse",
            "customer",
            "reference",
            "issued_to",
            "notes",
        ]
        widgets = {
            "issue_date": forms.DateInput(attrs={"type": "date", "class": _ctrl + " text-xs"}),
            "issue_type": forms.Select(attrs={"class": _ctrl + " text-xs"}),
            "warehouse": forms.Select(attrs={"class": _ctrl + " text-xs"}),
            "customer": forms.Select(attrs={"class": _ctrl + " text-xs"}),
            "reference": forms.TextInput(attrs={"class": _ctrl + " text-xs"}),
            "issued_to": forms.TextInput(attrs={"class": _ctrl + " text-xs"}),
            "notes": forms.Textarea(attrs={"rows": 2, "class": _ctrl + " text-xs"}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["warehouse"] = TenantScopedModelChoiceField(
                queryset=Warehouse.objects.none(),
                tenant=tenant,
                required=True,
                widget=forms.Select(
                    attrs={
                        "class": _ctrl + " text-xs inv-ts-autocomplete",
                        "data-autocomplete-url": _ac_url("autocomplete_warehouses"),
                    }
                ),
            )
            self.fields["customer"] = TenantScopedModelChoiceField(
                queryset=Customer.objects.none(),
                tenant=tenant,
                required=False,
                widget=forms.Select(
                    attrs={
                        "class": _ctrl + " text-xs inv-ts-autocomplete",
                        "data-autocomplete-url": _ac_url("autocomplete_customers"),
                    }
                ),
            )
            inst = self.instance
            if inst.pk and inst.warehouse_id:
                w = Warehouse.objects.only("pk", "code", "name").get(
                    pk=inst.warehouse_id, tenant_id=tenant.pk
                )
                self.fields["warehouse"].widget.choices = [(w.pk, f"{w.code} — {w.name}")]
            if inst.pk and inst.customer_id:
                c = Customer.objects.only("pk", "customer_code", "name").get(
                    pk=inst.customer_id, tenant_id=tenant.pk
                )
                self.fields["customer"].widget.choices = [(c.pk, f"{c.customer_code} — {c.name}")]


class GoodsIssueItemForm(forms.ModelForm):
    class Meta:
        model = GoodsIssueItem
        fields = ["product", "quantity", "unit_cost", "line_no"]
        widgets = {
            "quantity": forms.NumberInput(attrs={"class": _tbl + " inv-line-qty", "step": "any"}),
            "unit_cost": forms.NumberInput(
                attrs={"class": _tbl + " inv-line-unit-cost", "step": "any"}
            ),
            "line_no": forms.HiddenInput(),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["product"] = TenantScopedModelChoiceField(
                queryset=Product.objects.none(),
                tenant=tenant,
                required=True,
                widget=forms.Select(
                    attrs={
                        "class": _tbl_sel + " inv-ts-autocomplete inv-line-product",
                        "data-autocomplete-url": _ac_url("autocomplete_products"),
                    }
                ),
            )
            if self.instance.pk and self.instance.product_id:
                p = Product.objects.only("pk", "sku", "name").get(
                    pk=self.instance.product_id, tenant_id=tenant.pk
                )
                self.fields["product"].widget.choices = [(p.pk, f"{p.sku} — {p.name}")]


GoodsIssueItemFormSet = inlineformset_factory(
    GoodsIssue,
    GoodsIssueItem,
    form=GoodsIssueItemForm,
    formset=TenantInlineFormSet,
    extra=1,
    can_delete=True,
)


class InventoryTransferForm(forms.ModelForm):
    class Meta:
        model = InventoryTransfer
        fields = ["transfer_date", "from_warehouse", "to_warehouse", "reference", "notes"]
        widgets = {
            "transfer_date": forms.DateInput(attrs={"type": "date", "class": _ctrl + " text-xs"}),
            "from_warehouse": forms.Select(attrs={"class": _ctrl + " text-xs"}),
            "to_warehouse": forms.Select(attrs={"class": _ctrl + " text-xs"}),
            "reference": forms.TextInput(attrs={"class": _ctrl + " text-xs"}),
            "notes": forms.Textarea(attrs={"rows": 2, "class": _ctrl + " text-xs"}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            wh_attrs = {
                "class": _ctrl + " text-xs inv-ts-autocomplete",
                "data-autocomplete-url": _ac_url("autocomplete_warehouses"),
            }
            self.fields["from_warehouse"] = TenantScopedModelChoiceField(
                queryset=Warehouse.objects.none(),
                tenant=tenant,
                required=True,
                widget=forms.Select(attrs=wh_attrs),
            )
            self.fields["to_warehouse"] = TenantScopedModelChoiceField(
                queryset=Warehouse.objects.none(),
                tenant=tenant,
                required=True,
                widget=forms.Select(attrs=wh_attrs),
            )
            inst = self.instance
            if inst.pk and inst.from_warehouse_id:
                w = Warehouse.objects.only("pk", "code", "name").get(
                    pk=inst.from_warehouse_id, tenant_id=tenant.pk
                )
                self.fields["from_warehouse"].widget.choices = [(w.pk, f"{w.code} — {w.name}")]
            if inst.pk and inst.to_warehouse_id:
                w = Warehouse.objects.only("pk", "code", "name").get(
                    pk=inst.to_warehouse_id, tenant_id=tenant.pk
                )
                self.fields["to_warehouse"].widget.choices = [(w.pk, f"{w.code} — {w.name}")]

    def clean(self):
        data = super().clean()
        fw = data.get("from_warehouse")
        tw = data.get("to_warehouse")
        if fw and tw and fw.pk == tw.pk:
            raise forms.ValidationError("From warehouse and to warehouse must be different.")
        return data


class InventoryTransferItemForm(forms.ModelForm):
    class Meta:
        model = InventoryTransferItem
        fields = ["product", "quantity", "unit_cost", "line_no"]
        widgets = {
            "quantity": forms.NumberInput(attrs={"class": _tbl + " inv-line-qty", "step": "any"}),
            "unit_cost": forms.NumberInput(
                attrs={"class": _tbl + " inv-line-unit-cost", "step": "any"}
            ),
            "line_no": forms.HiddenInput(),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["product"] = TenantScopedModelChoiceField(
                queryset=Product.objects.none(),
                tenant=tenant,
                required=True,
                widget=forms.Select(
                    attrs={
                        "class": _tbl_sel + " inv-ts-autocomplete inv-line-product",
                        "data-autocomplete-url": _ac_url("autocomplete_products"),
                    }
                ),
            )
            if self.instance.pk and self.instance.product_id:
                p = Product.objects.only("pk", "sku", "name").get(
                    pk=self.instance.product_id, tenant_id=tenant.pk
                )
                self.fields["product"].widget.choices = [(p.pk, f"{p.sku} — {p.name}")]


InventoryTransferItemFormSet = inlineformset_factory(
    InventoryTransfer,
    InventoryTransferItem,
    form=InventoryTransferItemForm,
    formset=TenantInlineFormSet,
    extra=1,
    can_delete=True,
)
