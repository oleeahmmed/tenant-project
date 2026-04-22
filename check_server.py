#!/usr/bin/env python
"""Quick check if Django can start without import errors"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    django.setup()
    print("✅ Django setup successful!")
    print("✅ All imports working correctly!")
    print("🎉 Server should start without errors!")
    
    # Test key imports
    from auth_tenants.permissions import TenantAPIView, get_tenant
    from auth_tenants.mixins import TenantMixin
    print("✅ Core auth_tenants imports working!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)