#!/usr/bin/env python3
"""
Check Supabase configuration and connectivity.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.core.supabase import test_supabase_connection
import structlog

logger = structlog.get_logger(__name__)

def check_config():
    """Check and display Supabase configuration."""
    print("="*60)
    print("SUPABASE CONFIGURATION CHECK")
    print("="*60)
    
    print(f"\nEnvironment Settings:")
    print(f"  DEBUG: {settings.DEBUG}")
    print(f"  Environment: {'Development' if settings.is_development else 'Production'}")
    
    print(f"\nActive Configuration:")
    print(f"  URL: {settings.supabase_url}")
    print(f"  Anon Key: {settings.supabase_anon_key[:20]}...")
    print(f"  Service Role Key: {settings.supabase_service_role_key[:20]}...")
    
    if settings.DEBUG and settings.LOCAL_SUPABASE_URL:
        print(f"\n✓ Using LOCAL Supabase configuration")
    else:
        print(f"\n⚠ Using PRODUCTION Supabase configuration")
        if "supabase-demo" in settings.SUPABASE_SERVICE_ROLE_KEY:
            print("\n❌ ERROR: Service role key is still using demo key!")
            print("   You need to get the real service role key from:")
            print("   https://supabase.com/dashboard/project/kermpzcdqlgltgwicspi/settings/api")
            print("   Look for 'service_role' under 'Project API keys'")
    
    print(f"\nTesting connection...")
    if test_supabase_connection():
        print("✓ Connection successful!")
    else:
        print("❌ Connection failed!")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    check_config()