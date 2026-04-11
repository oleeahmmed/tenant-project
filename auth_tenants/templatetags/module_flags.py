from django import template

register = template.Library()


@register.filter
def module_enabled(tenant, module_code: str):
    """
    Template-safe module feature check.
    """
    if tenant is None:
        return False
    code = (module_code or "").strip().lower()
    if not code:
        return False
    if code in ("auth_tenants", "foundation"):
        return True
    row = tenant.module_subscriptions.filter(module_code=code).only("is_enabled").first()
    return True if row is None else bool(row.is_enabled)

