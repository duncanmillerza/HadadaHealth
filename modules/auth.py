"""
Authentication and user management for HadadaHealth
"""
import bcrypt
from fastapi import HTTPException, Request, Response, Depends, Body
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import FileResponse
from pydantic import BaseModel
from .database import get_db_connection, execute_query
import os
import json
import sqlite3
from typing import Dict, Any, Optional, List


# Initialize security
security = HTTPBasic()


class User(BaseModel):
    """User model"""
    username: str
    password: str
    role: str
    permissions: Optional[List[str]] = []
    linked_therapist_id: Optional[int] = None


class UserUpdate(BaseModel):
    """User update model"""
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    permissions: Optional[List[str]] = None
    linked_therapist_id: Optional[int] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a hashed password
    
    Args:
        plain_password: The plaintext password to verify
        hashed_password: The stored hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def hash_password(password: str) -> str:
    """
    Hash a plaintext password
    
    Args:
        password: The plaintext password to hash
        
    Returns:
        The hashed password as a string
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate a user by username and password
    
    Args:
        username: The username to authenticate
        password: The plaintext password
        
    Returns:
        User data dict if authentication successful, None otherwise
    """
    conn = get_db_connection()
    try:
        user = conn.execute(
            "SELECT id, username, password_hash, role, permissions, linked_therapist_id FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        
        if not user:
            return None
            
        if not verify_password(password, user[2]):
            return None
            
        return {
            "id": user[0],
            "username": user[1],
            "role": user[3],
            "permissions": user[4],
            "linked_therapist_id": user[5]
        }
    finally:
        conn.close()


def login_user(request: Request, credentials: HTTPBasicCredentials) -> Dict[str, Any]:
    """
    Login endpoint handler
    
    Args:
        request: FastAPI request object
        credentials: HTTP Basic credentials
        
    Returns:
        Login success response
        
    Raises:
        HTTPException: If authentication fails
    """
    user = authenticate_user(credentials.username, credentials.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    # Parse permissions if they exist
    permissions = user.get("permissions", [])
    if isinstance(permissions, str):
        try:
            permissions = json.loads(permissions)
        except (json.JSONDecodeError, TypeError):
            permissions = []
    
    # Set session data
    request.session["user_id"] = user["id"]
    request.session["username"] = user["username"]
    request.session["role"] = user["role"]
    request.session["permissions"] = permissions
    request.session["linked_therapist_id"] = user["linked_therapist_id"]
    
    return {
        "detail": "Login successful",
        "user_id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "permissions": permissions,
        "linked_therapist_id": user["linked_therapist_id"]
    }


def logout_user(request: Request, response: Response) -> Dict[str, str]:
    """
    Logout endpoint handler
    
    Args:
        request: FastAPI request object
        response: FastAPI response object
        
    Returns:
        Logout success response
    """
    request.session.clear()
    response.delete_cookie("session")
    return {"detail": "Logged out successfully"}


def check_login_status(request: Request) -> Dict[str, Any]:
    """
    Check if user is logged in
    
    Args:
        request: FastAPI request object
        
    Returns:
        Login status and user info
    """
    if request.session.get("user_id"):
        return {
            "logged_in": True,
            "username": request.session.get("username"),
            "role": request.session.get("role"),
            "linked_therapist_id": request.session.get("linked_therapist_id"),
        }
    return {"logged_in": False}


def serve_login_page():
    """
    Serve the login page HTML
    
    Returns:
        FileResponse with login.html
    """
    return FileResponse(os.path.join("templates", "login.html"))


def require_auth(request: Request) -> Dict[str, Any]:
    """
    Dependency to require authentication
    
    Args:
        request: FastAPI request object
        
    Returns:
        User session data
        
    Raises:
        HTTPException: If user not authenticated
    """
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return {
        "user_id": request.session.get("user_id"),
        "username": request.session.get("username"),
        "role": request.session.get("role"),
        "linked_therapist_id": request.session.get("linked_therapist_id")
    }


def require_admin(request: Request) -> Dict[str, Any]:
    """
    Dependency to require admin role
    
    Args:
        request: FastAPI request object
        
    Returns:
        User session data
        
    Raises:
        HTTPException: If user not authenticated or not admin
    """
    user = require_auth(request)
    if user.get("role") != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ===== USER MANAGEMENT FUNCTIONS =====

def get_all_users(request: Request) -> List[Dict[str, Any]]:
    """
    Get all users (Admin-only)
    
    Args:
        request: FastAPI request object for authentication
        
    Returns:
        List of user dictionaries
        
    Raises:
        HTTPException: If user not admin
    """
    require_admin(request)
    
    query = """
        SELECT id, username, role, permissions, linked_therapist_id
        FROM users
        ORDER BY username
    """
    results = execute_query(query, fetch='all')
    
    users = []
    for row in results:
        user = dict(row)
        # Parse permissions JSON if it exists
        if user.get('permissions'):
            try:
                user['permissions'] = json.loads(user['permissions'])
            except (json.JSONDecodeError, TypeError):
                user['permissions'] = []
        else:
            user['permissions'] = []
        users.append(user)
    
    return users


def create_user(user_data: Dict[str, Any], request: Request = None) -> Dict[str, str]:
    """
    Create a new user
    
    Args:
        user_data: Dictionary containing user information
        request: FastAPI request object for authentication (optional for internal use)
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If user already exists or creation fails
    """
    if request:
        require_admin(request)
    
    # Hash the password
    password_hash = hash_password(user_data['password'])
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, permissions, linked_therapist_id)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_data['username'],
            password_hash,
            user_data['role'],
            json.dumps(user_data.get('permissions', [])),
            user_data.get('linked_therapist_id')
        ))
        conn.commit()
        return {"detail": "User created successfully"}
        
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")
    finally:
        conn.close()


def signup_user(user_data: Dict[str, Any]) -> Dict[str, str]:
    """
    User signup endpoint (currently admin-only)
    
    Args:
        user_data: Dictionary containing user signup information
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If user already exists or creation fails
    """
    return create_user(user_data)


def update_user(user_id: int, user_data: Dict[str, Any], request: Request) -> Dict[str, str]:
    """
    Update an existing user (Admin-only)
    
    Args:
        user_id: The user ID to update
        user_data: Dictionary containing updated user information
        request: FastAPI request object for authentication
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If user not found or update fails
    """
    require_admin(request)
    
    # Check if user exists
    existing_user = get_user_by_id(user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Build update query
    valid_fields = ['username', 'password', 'role', 'permissions', 'linked_therapist_id']
    update_fields = [field for field in valid_fields if field in user_data]
    
    if not update_fields:
        return {"detail": "No fields to update"}
    
    conn = get_db_connection()
    try:
        # Prepare values for update
        values = []
        set_clauses = []
        
        for field in update_fields:
            if field == 'password':
                # Hash password if being updated
                values.append(hash_password(user_data[field]))
                set_clauses.append(f"password_hash = ?")
            elif field == 'permissions':
                # Handle permissions as JSON
                permissions = user_data[field]
                if isinstance(permissions, list):
                    values.append(json.dumps(permissions))
                else:
                    values.append(permissions)
                set_clauses.append(f"permissions = ?")
            else:
                values.append(user_data[field])
                set_clauses.append(f"{field} = ?")
        
        values.append(user_id)
        
        query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ?"
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        
        return {"detail": "User updated successfully"}
        
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")
    finally:
        conn.close()


def delete_user(user_id: int, request: Request) -> Dict[str, str]:
    """
    Delete a user (Admin-only)
    
    Args:
        user_id: The user ID to delete
        request: FastAPI request object for authentication
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If user not found or deletion fails
    """
    require_admin(request)
    
    # Check if user exists
    existing_user = get_user_by_id(user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
            
        return {"detail": "User deleted successfully"}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a user by ID
    
    Args:
        user_id: The user ID
        
    Returns:
        User dictionary or None if not found
    """
    query = """
        SELECT id, username, role, permissions, linked_therapist_id
        FROM users WHERE id = ?
    """
    result = execute_query(query, (user_id,), fetch='one')
    
    if result:
        user = dict(result)
        # Parse permissions JSON if it exists
        if user.get('permissions'):
            try:
                user['permissions'] = json.loads(user['permissions'])
            except (json.JSONDecodeError, TypeError):
                user['permissions'] = []
        else:
            user['permissions'] = []
        return user
    
    return None


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """
    Get a user by username
    
    Args:
        username: The username
        
    Returns:
        User dictionary or None if not found
    """
    query = """
        SELECT id, username, role, permissions, linked_therapist_id
        FROM users WHERE username = ?
    """
    result = execute_query(query, (username,), fetch='one')
    
    if result:
        user = dict(result)
        # Parse permissions JSON if it exists
        if user.get('permissions'):
            try:
                user['permissions'] = json.loads(user['permissions'])
            except (json.JSONDecodeError, TypeError):
                user['permissions'] = []
        else:
            user['permissions'] = []
        return user
    
    return None


def search_users(search_term: str, request: Request) -> List[Dict[str, Any]]:
    """
    Search users by username or role (Admin-only)
    
    Args:
        search_term: The search term
        request: FastAPI request object for authentication
        
    Returns:
        List of matching user dictionaries
    """
    require_admin(request)
    
    search_pattern = f"%{search_term}%"
    query = """
        SELECT id, username, role, permissions, linked_therapist_id
        FROM users
        WHERE username LIKE ? OR role LIKE ?
        ORDER BY username
    """
    
    results = execute_query(query, (search_pattern, search_pattern), fetch='all')
    
    users = []
    for row in results:
        user = dict(row)
        # Parse permissions JSON if it exists
        if user.get('permissions'):
            try:
                user['permissions'] = json.loads(user['permissions'])
            except (json.JSONDecodeError, TypeError):
                user['permissions'] = []
        else:
            user['permissions'] = []
        users.append(user)
    
    return users


def get_users_by_role(role: str, request: Request) -> List[Dict[str, Any]]:
    """
    Get users by role (Admin-only)
    
    Args:
        role: The role to filter by
        request: FastAPI request object for authentication
        
    Returns:
        List of user dictionaries
    """
    require_admin(request)
    
    query = """
        SELECT id, username, role, permissions, linked_therapist_id
        FROM users
        WHERE role = ?
        ORDER BY username
    """
    
    results = execute_query(query, (role,), fetch='all')
    
    users = []
    for row in results:
        user = dict(row)
        # Parse permissions JSON if it exists
        if user.get('permissions'):
            try:
                user['permissions'] = json.loads(user['permissions'])
            except (json.JSONDecodeError, TypeError):
                user['permissions'] = []
        else:
            user['permissions'] = []
        users.append(user)
    
    return users


def get_user_statistics(request: Request) -> Dict[str, Any]:
    """
    Get user statistics (Admin-only)
    
    Args:
        request: FastAPI request object for authentication
        
    Returns:
        Statistics dictionary
    """
    require_admin(request)
    
    conn = get_db_connection()
    try:
        stats = {}
        
        # Total users
        total_result = conn.execute("SELECT COUNT(*) FROM users").fetchone()
        stats['total_users'] = total_result[0] if total_result else 0
        
        # Users by role
        role_results = conn.execute("""
            SELECT role, COUNT(*) 
            FROM users 
            GROUP BY role
        """).fetchall()
        
        stats['users_by_role'] = {}
        for role, count in role_results:
            stats['users_by_role'][role] = count
        
        # Users with linked therapists
        linked_result = conn.execute(
            "SELECT COUNT(*) FROM users WHERE linked_therapist_id IS NOT NULL"
        ).fetchone()
        stats['users_with_linked_therapists'] = linked_result[0] if linked_result else 0
        
        return stats
        
    finally:
        conn.close()