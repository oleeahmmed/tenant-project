from rest_framework.permissions import BasePermission

from hrm.tenant_scope import get_hrm_tenant, user_belongs_to_workspace_tenant


class IsHrmTenantAdmin(BasePermission):
    """Matches HRM web: super_admin / tenant_admin / staff in the resolved workspace."""

    def has_permission(self, request, view):
        u = request.user
        if not u.is_authenticated:
            return False
        t = get_hrm_tenant(request)
        if t is None:
            return False
        role = getattr(u, "role", None)
        if role == "super_admin":
            return True
        if role not in ("tenant_admin", "staff"):
            return False
        return user_belongs_to_workspace_tenant(u, t)
