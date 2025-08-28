"""
Rate Limiting Module for HadadaHealth
Prevents brute force attacks and API abuse
"""
import time
import json
import os
from typing import Dict, Optional
from fastapi import HTTPException, Request
from .database import get_db_connection


class RateLimiter:
    """Rate limiter for login attempts and API calls"""
    
    def __init__(self):
        self.max_attempts = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
        self.lockout_duration = int(os.getenv("LOGIN_LOCKOUT_DURATION", "900"))  # 15 minutes
        self.cleanup_interval = 3600  # Clean old records every hour
        self.last_cleanup = time.time()
        
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Create rate limiting table if it doesn't exist"""
        conn = get_db_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rate_limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    identifier TEXT NOT NULL,
                    attempt_type TEXT NOT NULL,
                    attempts INTEGER DEFAULT 0,
                    first_attempt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_attempt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    blocked_until TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(identifier, attempt_type)
                )
            """)
            
            # Create index for faster lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_rate_limits_lookup 
                ON rate_limits(identifier, attempt_type, blocked_until)
            """)
            
            conn.commit()
        finally:
            conn.close()
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get real IP from headers (for reverse proxy setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return str(request.client.host) if request.client else "unknown"
    
    def _cleanup_old_records(self):
        """Clean up old rate limiting records"""
        if time.time() - self.last_cleanup < self.cleanup_interval:
            return
        
        conn = get_db_connection()
        try:
            # Remove records older than 24 hours
            conn.execute("""
                DELETE FROM rate_limits 
                WHERE created_at < datetime('now', '-24 hours')
            """)
            conn.commit()
            self.last_cleanup = time.time()
        finally:
            conn.close()
    
    def check_rate_limit(self, request: Request, attempt_type: str = "login") -> bool:
        """
        Check if request should be rate limited
        
        Args:
            request: FastAPI request object
            attempt_type: Type of attempt (login, api, etc.)
            
        Returns:
            True if request is allowed, raises HTTPException if blocked
        """
        self._cleanup_old_records()
        
        identifier = self._get_client_identifier(request)
        current_time = time.time()
        
        conn = get_db_connection()
        try:
            # Check current rate limit status
            record = conn.execute("""
                SELECT attempts, blocked_until, last_attempt
                FROM rate_limits
                WHERE identifier = ? AND attempt_type = ?
            """, (identifier, attempt_type)).fetchone()
            
            if record:
                attempts, blocked_until, last_attempt = record
                
                # Check if currently blocked
                if blocked_until:
                    blocked_timestamp = time.mktime(time.strptime(blocked_until, "%Y-%m-%d %H:%M:%S"))
                    if current_time < blocked_timestamp:
                        remaining_time = int(blocked_timestamp - current_time)
                        raise HTTPException(
                            status_code=429,
                            detail=f"Too many failed attempts. Please try again in {remaining_time // 60} minutes."
                        )
                    else:
                        # Unblock - reset attempts
                        conn.execute("""
                            UPDATE rate_limits 
                            SET attempts = 0, blocked_until = NULL
                            WHERE identifier = ? AND attempt_type = ?
                        """, (identifier, attempt_type))
                        conn.commit()
                
                # Check if too many attempts
                if attempts >= self.max_attempts:
                    # Block the identifier
                    blocked_until = time.strftime(
                        "%Y-%m-%d %H:%M:%S",
                        time.localtime(current_time + self.lockout_duration)
                    )
                    
                    conn.execute("""
                        UPDATE rate_limits
                        SET blocked_until = ?, last_attempt = CURRENT_TIMESTAMP
                        WHERE identifier = ? AND attempt_type = ?
                    """, (blocked_until, identifier, attempt_type))
                    conn.commit()
                    
                    raise HTTPException(
                        status_code=429,
                        detail=f"Too many failed attempts. Account temporarily locked for {self.lockout_duration // 60} minutes."
                    )
            
            return True
            
        finally:
            conn.close()
    
    def record_failed_attempt(self, request: Request, attempt_type: str = "login"):
        """Record a failed attempt"""
        identifier = self._get_client_identifier(request)
        
        conn = get_db_connection()
        try:
            # Insert or update attempt record
            conn.execute("""
                INSERT INTO rate_limits (identifier, attempt_type, attempts, last_attempt)
                VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(identifier, attempt_type)
                DO UPDATE SET
                    attempts = attempts + 1,
                    last_attempt = CURRENT_TIMESTAMP
            """, (identifier, attempt_type))
            conn.commit()
        finally:
            conn.close()
    
    def record_successful_attempt(self, request: Request, attempt_type: str = "login"):
        """Record a successful attempt and reset counter"""
        identifier = self._get_client_identifier(request)
        
        conn = get_db_connection()
        try:
            # Reset attempts counter on success
            conn.execute("""
                UPDATE rate_limits 
                SET attempts = 0, blocked_until = NULL, last_attempt = CURRENT_TIMESTAMP
                WHERE identifier = ? AND attempt_type = ?
            """, (identifier, attempt_type))
            conn.commit()
        finally:
            conn.close()
    
    def get_attempt_info(self, request: Request, attempt_type: str = "login") -> Dict:
        """Get current attempt information for client"""
        identifier = self._get_client_identifier(request)
        
        conn = get_db_connection()
        try:
            record = conn.execute("""
                SELECT attempts, blocked_until, last_attempt, first_attempt
                FROM rate_limits
                WHERE identifier = ? AND attempt_type = ?
            """, (identifier, attempt_type)).fetchone()
            
            if not record:
                return {
                    "attempts": 0,
                    "max_attempts": self.max_attempts,
                    "remaining_attempts": self.max_attempts,
                    "blocked": False,
                    "blocked_until": None
                }
            
            attempts, blocked_until, last_attempt, first_attempt = record
            current_time = time.time()
            
            blocked = False
            if blocked_until:
                blocked_timestamp = time.mktime(time.strptime(blocked_until, "%Y-%m-%d %H:%M:%S"))
                blocked = current_time < blocked_timestamp
            
            return {
                "attempts": attempts,
                "max_attempts": self.max_attempts,
                "remaining_attempts": max(0, self.max_attempts - attempts),
                "blocked": blocked,
                "blocked_until": blocked_until,
                "last_attempt": last_attempt,
                "first_attempt": first_attempt
            }
            
        finally:
            conn.close()
    
    def unblock_identifier(self, identifier: str, attempt_type: str = "login") -> bool:
        """Manually unblock an identifier (admin function)"""
        conn = get_db_connection()
        try:
            conn.execute("""
                UPDATE rate_limits 
                SET attempts = 0, blocked_until = NULL
                WHERE identifier = ? AND attempt_type = ?
            """, (identifier, attempt_type))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()
    
    def get_blocked_identifiers(self) -> list:
        """Get list of currently blocked identifiers"""
        conn = get_db_connection()
        try:
            records = conn.execute("""
                SELECT identifier, attempt_type, attempts, blocked_until
                FROM rate_limits
                WHERE blocked_until > datetime('now')
                ORDER BY blocked_until DESC
            """).fetchall()
            
            return [
                {
                    "identifier": record[0],
                    "attempt_type": record[1],
                    "attempts": record[2],
                    "blocked_until": record[3]
                }
                for record in records
            ]
            
        finally:
            conn.close()


# Global rate limiter instance
rate_limiter = RateLimiter()


def check_login_rate_limit(request: Request):
    """FastAPI dependency to check login rate limits"""
    return rate_limiter.check_rate_limit(request, "login")


def check_api_rate_limit(request: Request):
    """FastAPI dependency to check API rate limits"""
    return rate_limiter.check_rate_limit(request, "api")