"""
Authentication module for the AI Dev Team Platform
Simple invite-code based authentication with session cookies
"""
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import Request, HTTPException, Depends, Cookie
from fastapi.security import HTTPBearer
from config.settings import INVITE_CODES, SESSION_SECRET

security = HTTPBearer(auto_error=False)

# Session storage (in production, use Redis or database)
active_sessions = {}

class AuthManager:
    def __init__(self):
        self.invite_codes = INVITE_CODES
        self.session_secret = SESSION_SECRET
        
    def validate_invite_code(self, code: str) -> bool:
        """Validate an invite code"""
        return code.strip() in self.invite_codes
    
    def create_session(self, invite_code: str) -> str:
        """Create a new session for valid invite code"""
        if not self.validate_invite_code(invite_code):
            raise HTTPException(status_code=401, detail="Invalid invite code")
        
        # Generate session token
        session_token = secrets.token_urlsafe(32)
        
        # Store session
        active_sessions[session_token] = {
            "invite_code": invite_code,
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "user_agent": None  # Could be added for security
        }
        
        return session_token
    
    def validate_session(self, session_token: Optional[str]) -> bool:
        """Validate a session token"""
        if not session_token:
            return False
            
        session = active_sessions.get(session_token)
        if not session:
            return False
        
        # Check if session is expired (24 hours)
        if datetime.now() - session["created_at"] > timedelta(hours=24):
            del active_sessions[session_token]
            return False
        
        # Update last accessed
        session["last_accessed"] = datetime.now()
        return True
    
    def delete_session(self, session_token: str):
        """Delete a session (logout)"""
        if session_token in active_sessions:
            del active_sessions[session_token]
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        now = datetime.now()
        expired = []
        
        for token, session in active_sessions.items():
            if now - session["created_at"] > timedelta(hours=24):
                expired.append(token)
        
        for token in expired:
            del active_sessions[token]

# Global auth manager instance
auth_manager = AuthManager()

def get_session_token(session: Optional[str] = Cookie(None, alias="ai_dev_session")) -> Optional[str]:
    """Extract session token from cookie"""
    return session

def require_auth(session_token: Optional[str] = Depends(get_session_token)):
    """Dependency that requires authentication"""
    if not auth_manager.validate_session(session_token):
        raise HTTPException(
            status_code=401, 
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return session_token

def optional_auth(session_token: Optional[str] = Depends(get_session_token)):
    """Dependency for optional authentication"""
    return auth_manager.validate_session(session_token) if session_token else False

def is_authenticated(request: Request) -> bool:
    """Check if request is authenticated"""
    session_token = request.cookies.get("ai_dev_session")
    return auth_manager.validate_session(session_token)

# Middleware for protecting routes
async def auth_middleware(request: Request, call_next):
    """Authentication middleware"""
    # Public routes that don't require auth
    public_routes = [
        "/login",
        "/auth/login", 
        "/auth/logout",
        "/static"
    ]
    
    # Check if route should be public
    if any(request.url.path.startswith(route) for route in public_routes):
        response = await call_next(request)
        return response
    
    # Check authentication for protected routes
    session_token = request.cookies.get("ai_dev_session")
    
    if not auth_manager.validate_session(session_token):
        # Redirect to login for HTML requests
        if "text/html" in request.headers.get("accept", ""):
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/login", status_code=302)
        else:
            # Return 401 for API requests
            raise HTTPException(status_code=401, detail="Authentication required")
    
    response = await call_next(request)
    return response

# Utility functions for templates
def get_authenticated_user(request: Request) -> Optional[str]:
    """Get authenticated user info for templates"""
    session_token = request.cookies.get("ai_dev_session")
    if auth_manager.validate_session(session_token):
        session = active_sessions.get(session_token)
        return session.get("invite_code") if session else None
    return None