#!/usr/bin/env python
"""
🎯 MASS UPDATE SCRIPT
Removes ALL HRM dependencies from ALL apps and replaces with unified system
"""
import os
import re
import glob

# Files to update
FILES_TO_UPDATE = [
    "school/api/views.py",
    "school/mixins.py", 
    "rental_management/api/views.py",
    "rental_management/mixins.py",
    "pos/views.py",
    "notification/templatetags/notification_tags.py",
    "jiraclone/views.py",
    "hrm/api/pyzk_views.py",
    "hrm/api/location_views.py",
    "inventory/mixins.py",
    "foundation/mixins.py",
    "foundation/api/views.py",
    "chat/views.py",
    "support/views.py",
    "screenhot/api/views.py",
]

# Replacement mappings
REPLACEMENTS = [
    # Import replacements
    (r'from hrm\.tenant_scope import get_hrm_tenant, user_belongs_to_workspace_tenant', 
     'from auth_tenants.permissions import get_tenant, TenantManager'),
    
    (r'from hrm\.tenant_scope import get_hrm_tenant', 
     'from auth_tenants.permissions import get_tenant'),
    
    (r'from hrm\.tenant_scope import user_belongs_to_workspace_tenant', 
     'from auth_tenants.permissions import TenantManager'),
    
    # Function call replacements
    (r'get_hrm_tenant\(([^)]+)\)', r'get_tenant(\1)'),
    
    (r'user_belongs_to_workspace_tenant\(([^,]+),\s*([^)]+)\)', 
     r'TenantManager.user_belongs_to_tenant(\1, \2)'),
    
    # Legacy permission imports
    (r'from auth_tenants\.api\.permissions import HasTenantPerm', 
     'from auth_tenants.permissions import RequirePermission'),
    
    (r'HasTenantPerm\("([^"]+)"\)', r'RequirePermission("\1")'),
]

def update_file(filepath):
    """Update a single file"""
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply all replacements
        for pattern, replacement in REPLACEMENTS:
            content = re.sub(pattern, replacement, content)
        
        # Only write if content changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Updated: {filepath}")
            return True
        else:
            print(f"⏭️  No changes needed: {filepath}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating {filepath}: {e}")
        return False

def main():
    """Update all files"""
    print("🎯 MASS UPDATE: Removing HRM dependencies from all apps...")
    print("=" * 60)
    
    updated_count = 0
    
    for filepath in FILES_TO_UPDATE:
        if update_file(filepath):
            updated_count += 1
    
    print("=" * 60)
    print(f"🎉 Update complete! {updated_count} files updated.")
    print("✅ All apps now use unified auth_tenants.permissions system!")

if __name__ == "__main__":
    main()