from django import template

from hrm.tenant_scope import get_hrm_tenant

from notification.services import unread_count_for_user

register = template.Library()


@register.simple_tag(takes_context=True)
def notification_unread_count(context):
    request = context.get("request")
    if not request or not getattr(request.user, "is_authenticated", False):
        return 0
    tenant = getattr(request, "hrm_tenant", None)
    if tenant is None:
        tenant = get_hrm_tenant(request)
    tid = tenant.pk if tenant is not None else None
    return unread_count_for_user(tenant_id=tid, user_id=request.user.pk)
