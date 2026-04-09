from rest_framework.permissions import BasePermission

from hrm.tenant_scope import get_hrm_tenant


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "super_admin"


class IsTenantAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ("super_admin", "tenant_admin")


class IsSameTenant(BasePermission):
    """Object level — নিজের tenant এর data ছাড়া access নেই"""
    def has_object_permission(self, request, view, obj):
        t = get_hrm_tenant(request)
        return t is not None and getattr(obj, "tenant", None) == t


def HasTenantPerm(perm: str):
    """
    Dynamic permission class factory।
    ব্যবহার: permission_classes = [HasTenantPerm("contacts.view")]
    """
    class _Permission(BasePermission):
        def has_permission(self, request, view):
            if not request.user.is_authenticated:
                return False
            t = get_hrm_tenant(request)
            return t is not None and request.user.has_tenant_permission(perm)
    _Permission.__name__ = f"HasPerm_{perm}"
    return _Permission
