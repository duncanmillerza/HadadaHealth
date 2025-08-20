"""
Settings and configuration management functions for HadadaHealth
"""
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, Body
from pydantic import BaseModel
from .database import get_db_connection, execute_query
import sqlite3
import json
from datetime import datetime


class Settings(BaseModel):
    """Settings model"""
    start_time: str
    end_time: str
    slot_duration: int
    weekdays: List[str]
    dark_mode: bool
    billing_mode: Optional[str] = "therapist"


class SystemConfig(BaseModel):
    """System configuration model"""
    app_name: Optional[str] = "HadadaHealth"
    app_version: Optional[str] = "1.0.0"
    timezone: Optional[str] = "Africa/Johannesburg"
    currency: Optional[str] = "ZAR"
    date_format: Optional[str] = "YYYY-MM-DD"
    time_format: Optional[str] = "24"
    language: Optional[str] = "en"


class UserPreferences(BaseModel):
    """User preferences model"""
    user_id: int
    theme: Optional[str] = "light"
    notifications_enabled: bool = True
    email_notifications: bool = True
    dashboard_layout: Optional[str] = "default"
    timezone: Optional[str] = None
    language: Optional[str] = None


# ===== SYSTEM SETTINGS MANAGEMENT =====

def get_system_settings() -> Dict[str, Any]:
    """
    Get system settings from database
    
    Returns:
        Settings dictionary
        
    Raises:
        HTTPException: If settings not found
    """
    query = "SELECT start_time, end_time, slot_duration, weekdays, dark_mode, billing_mode FROM settings WHERE id = 1"
    result = execute_query(query, fetch='one')
    
    if result:
        return {
            "start_time": result[0],
            "end_time": result[1],
            "slot_duration": result[2],
            "weekdays": result[3].split(",") if result[3] else [],
            "dark_mode": bool(result[4]),
            "billing_mode": result[5] or "therapist"
        }
    
    raise HTTPException(status_code=404, detail="Settings not found")


def update_system_settings(settings: Dict[str, Any]) -> Dict[str, str]:
    """
    Update system settings
    
    Args:
        settings: Dictionary containing updated settings
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If update fails
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE settings
            SET start_time = ?, end_time = ?, slot_duration = ?, weekdays = ?, dark_mode = ?, billing_mode = ?
            WHERE id = 1
        """, (
            settings.get("start_time"),
            settings.get("end_time"),
            settings.get("slot_duration"),
            ",".join(settings.get("weekdays", [])),
            int(settings.get("dark_mode", False)),
            settings.get("billing_mode", "therapist")
        ))
        
        # If no row was updated, insert a new one
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO settings (id, start_time, end_time, slot_duration, weekdays, dark_mode, billing_mode)
                VALUES (1, ?, ?, ?, ?, ?, ?)
            """, (
                settings.get("start_time"),
                settings.get("end_time"),
                settings.get("slot_duration"),
                ",".join(settings.get("weekdays", [])),
                int(settings.get("dark_mode", False)),
                settings.get("billing_mode", "therapist")
            ))
        
        conn.commit()
        return {"detail": "Settings updated"}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")
    finally:
        conn.close()


def reset_system_settings() -> Dict[str, str]:
    """
    Reset system settings to defaults
    
    Returns:
        Success message dictionary
    """
    default_settings = {
        "start_time": "08:00",
        "end_time": "17:00",
        "slot_duration": 60,
        "weekdays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "dark_mode": False,
        "billing_mode": "therapist"
    }
    
    return update_system_settings(default_settings)


# ===== USER PREFERENCES MANAGEMENT =====

def get_user_preferences(user_id: int) -> Dict[str, Any]:
    """
    Get user preferences
    
    Args:
        user_id: User ID
        
    Returns:
        User preferences dictionary
    """
    # Check if user_preferences table exists, if not create it
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                theme TEXT DEFAULT 'light',
                notifications_enabled BOOLEAN DEFAULT 1,
                email_notifications BOOLEAN DEFAULT 1,
                dashboard_layout TEXT DEFAULT 'default',
                timezone TEXT,
                language TEXT DEFAULT 'en',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Get user preferences
        cursor.execute("""
            SELECT theme, notifications_enabled, email_notifications, dashboard_layout, timezone, language
            FROM user_preferences WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.commit()
        
        if result:
            return {
                "user_id": user_id,
                "theme": result[0],
                "notifications_enabled": bool(result[1]),
                "email_notifications": bool(result[2]),
                "dashboard_layout": result[3],
                "timezone": result[4],
                "language": result[5]
            }
        else:
            # Return defaults for new user
            return {
                "user_id": user_id,
                "theme": "light",
                "notifications_enabled": True,
                "email_notifications": True,
                "dashboard_layout": "default",
                "timezone": None,
                "language": "en"
            }
            
    finally:
        conn.close()


def update_user_preferences(user_id: int, preferences: Dict[str, Any]) -> Dict[str, str]:
    """
    Update user preferences
    
    Args:
        user_id: User ID
        preferences: Dictionary containing updated preferences
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If update fails
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                theme TEXT DEFAULT 'light',
                notifications_enabled BOOLEAN DEFAULT 1,
                email_notifications BOOLEAN DEFAULT 1,
                dashboard_layout TEXT DEFAULT 'default',
                timezone TEXT,
                language TEXT DEFAULT 'en',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Try to update existing preferences
        cursor.execute("""
            UPDATE user_preferences
            SET theme = ?, notifications_enabled = ?, email_notifications = ?, 
                dashboard_layout = ?, timezone = ?, language = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (
            preferences.get("theme", "light"),
            int(preferences.get("notifications_enabled", True)),
            int(preferences.get("email_notifications", True)),
            preferences.get("dashboard_layout", "default"),
            preferences.get("timezone"),
            preferences.get("language", "en"),
            user_id
        ))
        
        # If no row was updated, insert a new one
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO user_preferences 
                (user_id, theme, notifications_enabled, email_notifications, dashboard_layout, timezone, language)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                preferences.get("theme", "light"),
                int(preferences.get("notifications_enabled", True)),
                int(preferences.get("email_notifications", True)),
                preferences.get("dashboard_layout", "default"),
                preferences.get("timezone"),
                preferences.get("language", "en")
            ))
        
        conn.commit()
        return {"detail": "User preferences updated"}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update user preferences: {str(e)}")
    finally:
        conn.close()


# ===== SYSTEM CONFIGURATION MANAGEMENT =====

def get_system_configuration() -> Dict[str, Any]:
    """
    Get system configuration
    
    Returns:
        System configuration dictionary
    """
    # Check if system_config table exists
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY,
                app_name TEXT DEFAULT 'HadadaHealth',
                app_version TEXT DEFAULT '1.0.0',
                timezone TEXT DEFAULT 'Africa/Johannesburg',
                currency TEXT DEFAULT 'ZAR',
                date_format TEXT DEFAULT 'YYYY-MM-DD',
                time_format TEXT DEFAULT '24',
                language TEXT DEFAULT 'en',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Get system config
        cursor.execute("""
            SELECT app_name, app_version, timezone, currency, date_format, time_format, language
            FROM system_config WHERE id = 1
        """)
        
        result = cursor.fetchone()
        conn.commit()
        
        if result:
            return {
                "app_name": result[0],
                "app_version": result[1],
                "timezone": result[2],
                "currency": result[3],
                "date_format": result[4],
                "time_format": result[5],
                "language": result[6]
            }
        else:
            # Return defaults
            return {
                "app_name": "HadadaHealth",
                "app_version": "1.0.0",
                "timezone": "Africa/Johannesburg",
                "currency": "ZAR",
                "date_format": "YYYY-MM-DD",
                "time_format": "24",
                "language": "en"
            }
            
    finally:
        conn.close()


def update_system_configuration(config: Dict[str, Any]) -> Dict[str, str]:
    """
    Update system configuration
    
    Args:
        config: Dictionary containing updated configuration
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If update fails
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY,
                app_name TEXT DEFAULT 'HadadaHealth',
                app_version TEXT DEFAULT '1.0.0',
                timezone TEXT DEFAULT 'Africa/Johannesburg',
                currency TEXT DEFAULT 'ZAR',
                date_format TEXT DEFAULT 'YYYY-MM-DD',
                time_format TEXT DEFAULT '24',
                language TEXT DEFAULT 'en',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Try to update existing config
        cursor.execute("""
            UPDATE system_config
            SET app_name = ?, app_version = ?, timezone = ?, currency = ?, 
                date_format = ?, time_format = ?, language = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        """, (
            config.get("app_name", "HadadaHealth"),
            config.get("app_version", "1.0.0"),
            config.get("timezone", "Africa/Johannesburg"),
            config.get("currency", "ZAR"),
            config.get("date_format", "YYYY-MM-DD"),
            config.get("time_format", "24"),
            config.get("language", "en")
        ))
        
        # If no row was updated, insert a new one
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO system_config 
                (id, app_name, app_version, timezone, currency, date_format, time_format, language)
                VALUES (1, ?, ?, ?, ?, ?, ?, ?)
            """, (
                config.get("app_name", "HadadaHealth"),
                config.get("app_version", "1.0.0"),
                config.get("timezone", "Africa/Johannesburg"),
                config.get("currency", "ZAR"),
                config.get("date_format", "YYYY-MM-DD"),
                config.get("time_format", "24"),
                config.get("language", "en")
            ))
        
        conn.commit()
        return {"detail": "System configuration updated"}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update system configuration: {str(e)}")
    finally:
        conn.close()


# ===== BACKUP AND EXPORT FUNCTIONS =====

def create_system_backup() -> Dict[str, Any]:
    """
    Create a system backup containing all important data
    
    Returns:
        Backup data dictionary
    """
    backup_data = {
        "created_at": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "settings": {},
        "user_preferences": [],
        "system_config": {},
        "statistics": {}
    }
    
    try:
        # Export settings
        try:
            backup_data["settings"] = get_system_settings()
        except HTTPException:
            backup_data["settings"] = {}
        
        # Export system configuration
        backup_data["system_config"] = get_system_configuration()
        
        # Export all user preferences
        conn = get_db_connection()
        try:
            # Check if user_preferences table exists
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_preferences'")
            if cursor.fetchone():
                cursor.execute("""
                    SELECT user_id, theme, notifications_enabled, email_notifications, 
                           dashboard_layout, timezone, language
                    FROM user_preferences
                """)
                preferences = cursor.fetchall()
                
                for pref in preferences:
                    backup_data["user_preferences"].append({
                        "user_id": pref[0],
                        "theme": pref[1],
                        "notifications_enabled": bool(pref[2]),
                        "email_notifications": bool(pref[3]),
                        "dashboard_layout": pref[4],
                        "timezone": pref[5],
                        "language": pref[6]
                    })
        finally:
            conn.close()
        
        # Add basic statistics
        from .reports_analytics import get_system_overview_report
        try:
            backup_data["statistics"] = get_system_overview_report()
        except:
            backup_data["statistics"] = {}
        
        return backup_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create system backup: {str(e)}")


def restore_system_backup(backup_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Restore system from backup data
    
    Args:
        backup_data: Backup data dictionary
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If restore fails
    """
    try:
        # Restore settings
        if backup_data.get("settings"):
            update_system_settings(backup_data["settings"])
        
        # Restore system configuration
        if backup_data.get("system_config"):
            update_system_configuration(backup_data["system_config"])
        
        # Restore user preferences
        if backup_data.get("user_preferences"):
            for user_pref in backup_data["user_preferences"]:
                user_id = user_pref.pop("user_id")
                update_user_preferences(user_id, user_pref)
        
        return {"detail": "System restored from backup successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restore system backup: {str(e)}")


# ===== APPLICATION INITIALIZATION =====

def initialize_default_settings():
    """
    Initialize default system settings if they don't exist
    
    Returns:
        Success message dictionary
    """
    try:
        # Try to get existing settings
        get_system_settings()
        return {"detail": "Settings already exist"}
    except HTTPException:
        # Settings don't exist, create defaults
        return reset_system_settings()


def get_application_info() -> Dict[str, Any]:
    """
    Get application information and status
    
    Returns:
        Application info dictionary
    """
    try:
        system_config = get_system_configuration()
        system_settings = get_system_settings()
        
        # Get database info
        conn = get_db_connection()
        try:
            # Count main entities
            tables_info = {}
            
            # Check common tables
            common_tables = ['users', 'therapists', 'patients', 'bookings', 'treatment_notes', 
                           'medical_aids', 'professions', 'clinics', 'reminders', 'invoices']
            
            for table in common_tables:
                try:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()
                    tables_info[table] = count[0] if count else 0
                except:
                    tables_info[table] = 0
            
        finally:
            conn.close()
        
        return {
            "app_name": system_config.get("app_name", "HadadaHealth"),
            "app_version": system_config.get("app_version", "1.0.0"),
            "timezone": system_config.get("timezone", "Africa/Johannesburg"),
            "currency": system_config.get("currency", "ZAR"),
            "language": system_config.get("language", "en"),
            "settings_configured": True,
            "database_status": "connected",
            "table_counts": tables_info,
            "system_time": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "app_name": "HadadaHealth",
            "app_version": "1.0.0",
            "error": str(e),
            "database_status": "error",
            "system_time": datetime.utcnow().isoformat()
        }


def get_settings_summary() -> Dict[str, Any]:
    """
    Get a summary of all settings and configuration
    
    Returns:
        Settings summary dictionary
    """
    summary = {
        "generated_at": datetime.utcnow().isoformat(),
        "system_settings": {},
        "system_config": {},
        "application_info": {}
    }
    
    try:
        summary["system_settings"] = get_system_settings()
    except:
        summary["system_settings"] = {"error": "Settings not configured"}
    
    try:
        summary["system_config"] = get_system_configuration()
    except:
        summary["system_config"] = {"error": "Configuration not found"}
    
    try:
        summary["application_info"] = get_application_info()
    except:
        summary["application_info"] = {"error": "Unable to get application info"}
    
    return summary