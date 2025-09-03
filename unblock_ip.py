#!/usr/bin/env python3
"""
Admin utility to unblock IP addresses from rate limiting
Usage: python unblock_ip.py [ip_address]
"""

import sys
from modules.database import get_db_connection

def unblock_ip(ip_address=None):
    """Unblock an IP address or all blocked IPs"""
    conn = get_db_connection()
    try:
        if ip_address:
            # Unblock specific IP
            cursor = conn.execute("""
                UPDATE rate_limits 
                SET attempts = 0, blocked_until = NULL
                WHERE identifier = ?
            """, (ip_address,))
            
            if cursor.rowcount > 0:
                print(f"✅ Unblocked IP address: {ip_address}")
            else:
                print(f"❌ No rate limit found for IP: {ip_address}")
        else:
            # Show all blocked IPs and unblock all
            blocked = conn.execute("""
                SELECT identifier, attempts, blocked_until
                FROM rate_limits
                WHERE blocked_until > datetime('now')
            """).fetchall()
            
            if blocked:
                print("🔒 Currently blocked IP addresses:")
                for ip, attempts, blocked_until in blocked:
                    print(f"  - {ip} ({attempts} attempts, blocked until {blocked_until})")
                
                # Unblock all
                conn.execute("""
                    UPDATE rate_limits 
                    SET attempts = 0, blocked_until = NULL
                    WHERE blocked_until > datetime('now')
                """)
                print(f"\n✅ Unblocked {len(blocked)} IP address(es)")
            else:
                print("✅ No IP addresses are currently blocked")
        
        conn.commit()
        
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        ip = sys.argv[1]
        unblock_ip(ip)
    else:
        unblock_ip()