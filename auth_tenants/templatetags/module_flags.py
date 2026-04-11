from django import template

from hrm.tenant_scope import get_hrm_tenant

from auth_tenants.services.nav_visibility import workspace_nav_flags

register = template.Library()


@register.simple_tag(takes_context=True)
def workspace_nav(context):
    """
    Usage: {% workspace_nav as wnav %}
    Then: {% if wnav.chat %}, {% if wnav.any_workspace %}, {% if wnav.foundation %}, etc.
    """
    request = context["request"]
    tenant = get_hrm_tenant(request)
    return workspace_nav_flags(request.user, tenant)


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

