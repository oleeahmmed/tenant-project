from django import template
from auth_tenants.permissions import get_tenant, get_navigation_flags

register = template.Library()


@register.simple_tag(takes_context=True)
def workspace_nav(context):
    """
    🎯 UNIFIED NAVIGATION FLAGS
    Usage: {% workspace_nav as nav %}
    Then: {% if nav.inventory %}, {% if nav.any_workspace %}, etc.
    """
    request = context["request"]
    return get_navigation_flags(request)


@register.filter
def module_enabled(tenant, module_code):
    """
    🎯 SUBSCRIPTION-AWARE MODULE CHECK
    Usage: {{ tenant|module_enabled:"inventory" }}
    """
    if not tenant:
        return False
    return tenant.can_access_module(module_code)


@register.simple_tag(takes_context=True)
def current_tenant(context):
    """
    🎯 GET CURRENT TENANT
    Usage: {% current_tenant as tenant %}
    """
    request = context["request"]
    return get_tenant(request)