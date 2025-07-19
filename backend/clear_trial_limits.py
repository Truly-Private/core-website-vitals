#!/usr/bin/env python3
"""
Clear trial rate limits for development.
"""

import redis
from app.core.config import settings

def clear_trial_limits(ip_address: str = None):
    """Clear trial rate limits for an IP or all IPs."""
    
    # Connect to Redis
    redis_client = redis.from_url(settings.REDIS_URL)
    
    if ip_address:
        # Clear specific IP
        keys_to_delete = [
            f"trial_rate_limit:{ip_address}",
            f"trial_used:{ip_address}"
        ]
        
        for key in keys_to_delete:
            result = redis_client.delete(key)
            if result:
                print(f"Cleared: {key}")
            else:
                print(f"Not found: {key}")
    else:
        # Clear all trial keys
        pattern = "trial_*"
        keys = redis_client.keys(pattern)
        
        if keys:
            deleted = redis_client.delete(*keys)
            print(f"Cleared {deleted} trial-related keys")
        else:
            print("No trial keys found")
    
    print("\nCurrent trial keys:")
    remaining_keys = redis_client.keys("trial_*")
    if remaining_keys:
        for key in remaining_keys:
            print(f"  - {key.decode('utf-8')}")
    else:
        print("  None")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Clear specific IP
        ip = sys.argv[1]
        print(f"Clearing trial limits for IP: {ip}")
        clear_trial_limits(ip)
    else:
        # Clear all
        print("Clearing all trial limits...")
        clear_trial_limits()