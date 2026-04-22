#!/usr/bin/env python
"""Test script to check if all imports work correctly"""

import os
import sys
import django

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

try:
    print("Testing imports...")
    
    # Test auth_tenants imports
    from auth_tenants.permissions import TenantManager, ModuleManager, PermissionManager
    print("✅ auth_tenants.permissions - OK")
    
    from auth_tenants.mixins import TenantMixin, DashboardMixin
    print("✅ auth_tenants.mixins - OK")
    
    from auth_tenants.models import Tenant, User
    print("✅ auth_tenants.models - OK")
    
    from auth_tenants.views import dashboard_view
    print("✅ auth_tenants.views - OK")
    
    # Test app imports
    from rental_management.models import Property
    print("✅ rental_management.models - OK")
    
    from school.models import Student
    print("✅ school.models - OK")
    
    from inventory.mixins import InventoryAdminMixin
    print("✅ inventory.mixins - OK")
    
    print("\n🎉 All imports successful!")
    print("✅ Server should start without import errors")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)