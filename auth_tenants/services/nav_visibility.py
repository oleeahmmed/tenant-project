"""Sidebar: show a module only if the user may access at least one permission in that module."""

from django.apps import apps

from auth_tenants.services.permission_catalog import (
    CRUD_ACTIONS,
    MODULE_BASE_ACTIONS,
    MODULE_TO_APP_LABELS,
)

# Modules that appear in the workspace sidebar (codenames match Permission.category / module codes).
WORKSPACE_MODULE_CODES = (
    "auth_tenants",
    "foundation",
    "inventory",
    "finance",
    "purchase",
    "sales",
    "production",
    "pos",
    "jiraclone",
    "recruitment",
    "hrm",
    "chat",
    "support",
    "screenhot",
)


def user_can_see_module_in_nav(user, tenant, module_code: str) -> bool:
    """
    True if the tenant has the module enabled and the user has at least one effective
    permission: coarse (e.g. inventory.view) or any model CRUD in that module's apps.
    """
    code = (module_code or "").strip().lower()
    if not code or not getattr(user, "is_authenticated", False):
        return False

    if getattr(user, "role", None) == "super_admin":
        # Super admin must always see all workspace menus, independent of tenant module toggles.
        return True

    if tenant is None:
        return False

    if not tenant.is_module_enabled(code):
        return False

    for action, _ in MODULE_BASE_ACTIONS:
        if user.has_tenant_permission(f"{code}.{action}"):
            return True

    for app_label in MODULE_TO_APP_LABELS.get(code, []):
        try:
            cfg = apps.get_app_config(app_label)
        except LookupError:
            continue
        for model in cfg.get_models():
            model_name = model._meta.model_name
            for action in CRUD_ACTIONS:
                codename = f"{app_label}.{model_name}.{action}"
                if user.has_tenant_permission(codename):
                    return True

    return False


def workspace_nav_flags(user, tenant) -> dict:
    """Precompute flags for base.html (one dict lookup per module)."""
    flags = {c: user_can_see_module_in_nav(user, tenant, c) for c in WORKSPACE_MODULE_CODES}
    workspace_codes = [c for c in WORKSPACE_MODULE_CODES if c != "chat"]
    flags["any_workspace"] = any(flags[c] for c in workspace_codes)
    return flags
