from decimal import Decimal

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def foundation_cell(obj, col):
    """Render one table cell from a column spec dict: field, label, bool, mono, money."""
    if not col:
        return "—"
    field = col.get("field") or ""
    if col.get("bool"):
        v = _resolve_attr(obj, field)
        if v is True:
            return mark_safe(
                '<span class="inline-flex rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs font-medium text-emerald-700 dark:text-emerald-400">Yes</span>'
            )
        if v is False:
            return mark_safe(
                '<span class="inline-flex rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">No</span>'
            )
        return "—"
    if col.get("money"):
        v = _resolve_attr(obj, field)
        if v is None:
            return "—"
        if isinstance(v, Decimal):
            return f"{v:,.4f}".rstrip("0").rstrip(".").rstrip(",")
        return escape(str(v))
    v = _resolve_attr(obj, field)
    if v is None:
        return "—"
    text = str(v)
    if col.get("mono"):
        return mark_safe(f'<span class="font-mono text-xs">{escape(text)}</span>')
    return escape(text)


def _resolve_attr(obj, path):
    if not path:
        return None
    cur = obj
    for part in path.split("__"):
        if cur is None:
            return None
        cur = getattr(cur, part, None)
    return cur
