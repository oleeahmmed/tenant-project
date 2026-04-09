"""Resolve which Tenant powers HRM / Foundation / workspace-scoped views."""

from auth_tenants.models import Tenant

SESSION_KEY_ACTIVE_TENANT = "hrm_active_tenant_id"


def _employee_for_user(user):
    """Linked HRM Employee row, if any (query avoids O2O RelatedObjectDoesNotExist)."""
    if not getattr(user, "pk", None):
        return None
    from hrm.models import Employee

    return Employee.objects.filter(user_id=user.pk).first()


def get_hrm_tenant(request):
    """
    Tenant for row-level scoping (single source of truth).

    Resolution order:

    - **tenant_admin / staff** with ``user.tenant_id`` → that tenant.
    - Same roles without ``user.tenant`` → ``Employee`` profile's tenant (portal users),
      else ``custom_role.tenant`` if the role is tenant-scoped.
    - **super_admin** with ``user.tenant`` → that tenant.
    - Else session ``hrm_active_tenant_id``, else if exactly one active tenant (dev),
      else **Employee** profile tenant (so linked accounts still get a workspace).

    Anonymous users always get ``None``.
    """
    u = getattr(request, "user", None)
    if not u or not u.is_authenticated:
        return None

    role = getattr(u, "role", None)

    if role in ("tenant_admin", "staff"):
        if getattr(u, "tenant_id", None):
            return u.tenant
        emp = _employee_for_user(u)
        if emp is not None:
            return emp.tenant
        if getattr(u, "custom_role_id", None):
            cr = u.custom_role
            if cr is not None and cr.tenant_id:
                return cr.tenant
        return None

    if role == "super_admin":
        if getattr(u, "tenant_id", None):
            return u.tenant
        sid = request.session.get(SESSION_KEY_ACTIVE_TENANT)
        if sid:
            try:
                return Tenant.objects.get(pk=sid, is_active=True)
            except Tenant.DoesNotExist:
                pass
        qs = Tenant.objects.filter(is_active=True)
        if qs.count() == 1:
            return qs.first()
        emp = _employee_for_user(u)
        if emp is not None:
            return emp.tenant
        return None

    return None


def user_belongs_to_workspace_tenant(user, tenant) -> bool:
    """
    Whether ``user`` may act inside the resolved workspace ``tenant``.

    - **super_admin**: always (scope is enforced by :func:`get_hrm_tenant`).
    - **tenant_admin**: must match ``user.tenant`` only (strict).
    - **staff**: ``user.tenant``, linked **Employee** on that tenant, or ``custom_role`` on that tenant.
    """
    if tenant is None:
        return False
    role = getattr(user, "role", None)
    if role == "super_admin":
        return True
    if role == "tenant_admin":
        return getattr(user, "tenant_id", None) == tenant.id
    if role == "staff":
        if getattr(user, "tenant_id", None) == tenant.id:
            return True
        emp = _employee_for_user(user)
        if emp is not None and emp.tenant_id == tenant.id:
            return True
        if getattr(user, "custom_role_id", None):
            cr = user.custom_role
            if cr is not None and cr.tenant_id == tenant.id:
                return True
        return False
    return False
