#!/usr/bin/env python3
"""
Apply database migration to add trial support columns.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.supabase import get_supabase_admin_client
import structlog

logger = structlog.get_logger(__name__)

def apply_migration():
    """Apply the trial columns migration."""
    try:
        # Get admin client
        client = get_supabase_admin_client()
        
        # Read migration SQL
        migration_path = Path(__file__).parent / "migrations" / "003_add_trial_columns.sql"
        with open(migration_path, 'r') as f:
            sql = f.read()
        
        # Execute migration
        # Note: Supabase Python client doesn't have direct SQL execution
        # We need to use the RPC function or apply via Supabase dashboard
        
        logger.info("Migration SQL ready to apply:")
        print("\n" + "="*60)
        print("Please apply this migration via Supabase SQL Editor:")
        print("="*60)
        print(sql)
        print("="*60)
        
        # Alternative: Try to check if columns exist
        result = client.table("analysis_tasks").select("*").limit(1).execute()
        
        if result.data:
            first_row = result.data[0] if result.data else {}
            has_is_trial = 'is_trial' in first_row
            has_trial_ip = 'trial_ip' in first_row
            
            if has_is_trial and has_trial_ip:
                logger.info("Trial columns already exist!")
            else:
                logger.warning("Trial columns missing. Please apply migration.")
        
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        print(f"\nError: {str(e)}")
        print("\nPlease apply the migration manually via Supabase dashboard")

if __name__ == "__main__":
    apply_migration()