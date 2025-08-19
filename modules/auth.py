"""
Authentication and user management module for HadadaHealth
"""
import json
import sqlite3
import bcrypt
from typing import List, Optional
from fastapi import Request, HTTPException, Depends, Body, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import FileResponse
import os

from .database import get_db_connection

# Security setup
security = HTTPBasic()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_user(
    username: str,
    password: str,
    role: str,
    permissions: List[str] = None,
    linked_therapist_id: Optional[int] = None
):
    """Create a new user in the database"""
    if permissions is None:
        permissions = []
    
    password_hash = hash_password(password)
    
    with get_db_connection() as conn:
        try:
            conn.execute(
                """
                INSERT INTO users (username, password_hash, role, permissions, linked_therapist_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (username, password_hash, role, json.dumps(permissions), linked_therapist_id)
            )
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Username already exists")
    
    return {"detail": "User created successfully"}


def authenticate_user(username: str, password: str):
    """Authenticate a user and return user data"""
    with get_db_connection() as conn:
        user = conn.execute(
            "SELECT id, username, password_hash, role, permissions, linked_therapist_id FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        
        if not user:
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        
        if not verify_password(password, user[2]):
            raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    return {
        'id': user[0],
        'username': user[1],
        'role': user[3],
        'permissions': json.loads(user[4] or "[]"),
        'linked_therapist_id': user[5]
    }


def login_user(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    """Login endpoint"""
    user = authenticate_user(credentials.username, credentials.password)
    
    # Set session data
    request.session['user_id'] = user['id']
    request.session['username'] = user['username']
    request.session['role'] = user['role']
    request.session['permissions'] = user['permissions']
    request.session['linked_therapist_id'] = user['linked_therapist_id']
    
    return {
        "detail": "Login successful",
        "user_id": user['id'],
        "username": user['username'],
        "role": user['role'],
        "linked_therapist_id": user['linked_therapist_id']
    }


def logout_user(request: Request, response: Response):
    """Logout endpoint"""
    request.session.clear()
    response.delete_cookie("session")
    return {"detail": "Logged out successfully"}


def check_login_status(request: Request):
    """Check if user is logged in"""
    if request.session.get("user_id"):
        return {
            "logged_in": True,
            "username": request.session.get("username"),
            "role": request.session.get("role"),
            "linked_therapist_id": request.session.get("linked_therapist_id"),
        }
    return {"logged_in": False}


def require_authentication(request: Request):
    """Middleware to require authentication for protected routes"""
    if not request.session.get("user_id"):
        return FileResponse(os.path.join("templates", "login.html"))
    return None


def get_users():
    """Get all users"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        users = cursor.execute("""
            SELECT u.id, u.username, u.role, u.permissions, u.linked_therapist_id,
                   t.name as therapist_name
            FROM users u
            LEFT JOIN therapists t ON u.linked_therapist_id = t.id
        """).fetchall()
        
        return [
            {
                "id": user[0],
                "username": user[1],
                "role": user[2],
                "permissions": json.loads(user[3] or "[]"),
                "linked_therapist_id": user[4],
                "therapist_name": user[5]
            }
            for user in users
        ]


def update_user(
    user_id: int,
    username: str = None,
    password: str = None,
    role: str = None,
    permissions: List[str] = None,
    linked_therapist_id: Optional[int] = None
):
    """Update a user"""
    with get_db_connection() as conn:
        # Build dynamic update query
        update_fields = []
        params = []
        
        if username is not None:
            update_fields.append("username = ?")
            params.append(username)
        
        if password is not None:
            update_fields.append("password_hash = ?")
            params.append(hash_password(password))
        
        if role is not None:
            update_fields.append("role = ?")
            params.append(role)
        
        if permissions is not None:
            update_fields.append("permissions = ?")
            params.append(json.dumps(permissions))
        
        if linked_therapist_id is not None:
            update_fields.append("linked_therapist_id = ?")
            params.append(linked_therapist_id)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.append(user_id)
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
        
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
    
    return {"detail": "User updated successfully"}


def delete_user(user_id: int):
    """Delete a user"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
    
    return {"detail": "User deleted successfully"}