"""Validate AP/AR invoice header vs line totals before save."""

from decimal import Decimal

from django.core.exceptions import ValidationError

_EPS = Decimal("0.02")


def _active_line_sum(formset) -> Decimal:
    total = Decimal("0")
    for f in formset.forms:
        if not f.cleaned_data:
            continue
        if getattr(formset, "can_delete", False) and f.cleaned_data.get("DELETE"):
            continue
        desc = (f.cleaned_data.get("description") or "").strip()
        lt = f.cleaned_data.get("line_total")
        if lt is None:
            lt = Decimal("0")
        if not desc and lt == Decimal("0"):
            continue
        total += lt
    return total


def validate_invoice_totals(*, form, formset, require_positive_lines: bool = True) -> None:
    """Subtotal must equal sum of line totals; total = subtotal + tax + shipping."""
    subtotal = form.cleaned_data["subtotal"]
    tax = form.cleaned_data.get("tax_amount") or Decimal("0")
    shipping = form.cleaned_data.get("shipping_charge") or Decimal("0")
    grand = form.cleaned_data["total_amount"]
    line_sum = _active_line_sum(formset)
    if require_positive_lines and line_sum <= Decimal("0"):
        raise ValidationError("Add at least one line item with a positive total.")
    if abs(line_sum - subtotal) > _EPS:
        raise ValidationError(
            f"Subtotal ({subtotal}) must match the sum of line totals ({line_sum}). "
            "Check each line or click Save after line amounts update."
        )
    if abs(subtotal + tax + shipping - grand) > _EPS:
        raise ValidationError(
            f"Total ({grand}) must equal subtotal + VAT + shipping ({subtotal + tax + shipping})."
        )
