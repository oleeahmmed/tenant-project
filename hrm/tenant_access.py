"""
Workspace tenant resolution and membership (re-exports).

Use this module when you need a single, documented entry point for permissions
checks. The canonical implementation lives in :mod:`hrm.tenant_scope`.
"""

from .tenant_scope import (
    SESSION_KEY_ACTIVE_TENANT,
    get_hrm_tenant,
    user_belongs_to_workspace_tenant,
)

__all__ = [
    "SESSION_KEY_ACTIVE_TENANT",
    "get_hrm_tenant",
    "user_belongs_to_workspace_tenant",
]
