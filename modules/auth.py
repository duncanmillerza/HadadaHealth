"""
Authentication and user management for HadadaHealth
"""
import bcrypt
from fastapi import HTTPException, Request, Response, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import FileResponse
from .database import get_db_connection
import os
from typing import Dict, Any, Optional


# Initialize security
security = HTTPBasic()


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


def login_user(request: Request, credentials: HTTPBasicCredentials = Depends(security)) -> Dict[str, Any]:
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
    
    # Set session data
    request.session["user_id"] = user["id"]
    request.session["username"] = user["username"]
    request.session["role"] = user["role"]
    request.session["linked_therapist_id"] = user["linked_therapist_id"]
    
    return {
        "message": "Login successful",
        "redirect": "/",
        "username": user["username"],
        "role": user["role"]
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
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user