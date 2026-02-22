"""
Safety Confirmation Module
Version: 2.0.0 - February 2026

Manages confirmation requests for dangerous actions.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from dataclasses import dataclass
import threading


@dataclass
class ConfirmationRequest:
    """A request for user confirmation."""
    token: str
    action: str
    reason: str
    details: Dict[str, Any]
    created_at: datetime
    expires_at: datetime
    status: str = "pending"  # pending, approved, rejected, expired
    responded_at: datetime = None
    responded_by: str = None
    
    def is_expired(self) -> bool:
        """Check if the request has expired."""
        return datetime.now() > self.expires_at
    
    def is_pending(self) -> bool:
        """Check if the request is still pending."""
        return self.status == "pending" and not self.is_expired()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "token": self.token,
            "action": self.action,
            "reason": self.reason,
            "details": self.details,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "status": self.status,
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
            "responded_by": self.responded_by
        }


class ConfirmationManager:
    """
    Manages confirmation requests for dangerous actions.
    
    Thread-safe singleton that tracks pending confirmations.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.pending: Dict[str, ConfirmationRequest] = {}
        self.history: list = []
        self.max_history = 100
        self.default_timeout = timedelta(minutes=5)
        
        self._initialized = True
    
    def create_request(self, action: str, reason: str, 
                       details: Dict[str, Any] = None,
                       timeout_minutes: int = 5) -> ConfirmationRequest:
        """
        Create a new confirmation request.
        
        Args:
            action: The action requiring confirmation
            reason: Why confirmation is needed
            details: Additional details about the action
            timeout_minutes: Minutes until the request expires
            
        Returns:
            The created confirmation request
        """
        token = str(uuid.uuid4())
        now = datetime.now()
        
        request = ConfirmationRequest(
            token=token,
            action=action,
            reason=reason,
            details=details or {},
            created_at=now,
            expires_at=now + timedelta(minutes=timeout_minutes)
        )
        
        self.pending[token] = request
        return request
    
    def get_request(self, token: str) -> Optional[ConfirmationRequest]:
        """
        Get a confirmation request by token.
        
        Args:
            token: The confirmation token
            
        Returns:
            The request if found, None otherwise
        """
        request = self.pending.get(token)
        
        if request and request.is_expired():
            request.status = "expired"
            self._move_to_history(request)
            return None
        
        return request
    
    def approve(self, token: str, responded_by: str = None) -> Optional[ConfirmationRequest]:
        """
        Approve a confirmation request.
        
        Args:
            token: The confirmation token
            responded_by: Who approved the request
            
        Returns:
            The approved request if found, None otherwise
        """
        request = self.get_request(token)
        
        if not request:
            return None
        
        request.status = "approved"
        request.responded_at = datetime.now()
        request.responded_by = responded_by
        
        self._move_to_history(request)
        return request
    
    def reject(self, token: str, responded_by: str = None) -> Optional[ConfirmationRequest]:
        """
        Reject a confirmation request.
        
        Args:
            token: The confirmation token
            responded_by: Who rejected the request
            
        Returns:
            The rejected request if found, None otherwise
        """
        request = self.get_request(token)
        
        if not request:
            return None
        
        request.status = "rejected"
        request.responded_at = datetime.now()
        request.responded_by = responded_by
        
        self._move_to_history(request)
        return request
    
    def respond(self, token: str, approved: bool, 
                responded_by: str = None) -> Optional[ConfirmationRequest]:
        """
        Respond to a confirmation request.
        
        Args:
            token: The confirmation token
            approved: Whether to approve
            responded_by: Who responded
            
        Returns:
            The request if found, None otherwise
        """
        if approved:
            return self.approve(token, responded_by)
        else:
            return self.reject(token, responded_by)
    
    def cancel(self, token: str) -> bool:
        """
        Cancel a pending confirmation request.
        
        Args:
            token: The confirmation token
            
        Returns:
            True if cancelled, False if not found
        """
        request = self.pending.get(token)
        
        if request:
            request.status = "cancelled"
            self._move_to_history(request)
            return True
        
        return False
    
    def cleanup_expired(self) -> int:
        """
        Remove expired requests.
        
        Returns:
            Number of expired requests removed
        """
        expired = []
        
        for token, request in self.pending.items():
            if request.is_expired():
                request.status = "expired"
                expired.append(token)
        
        for token in expired:
            self._move_to_history(self.pending[token])
        
        return len(expired)
    
    def _move_to_history(self, request: ConfirmationRequest):
        """Move a request to history."""
        if request.token in self.pending:
            del self.pending[request.token]
        
        self.history.append(request)
        
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def get_pending_count(self) -> int:
        """Get number of pending requests."""
        return len([r for r in self.pending.values() if r.is_pending()])
    
    def get_all_pending(self) -> list:
        """Get all pending requests."""
        return [r.to_dict() for r in self.pending.values() if r.is_pending()]
    
    def get_history(self, limit: int = 50) -> list:
        """Get confirmation history."""
        return [r.to_dict() for r in self.history[-limit:]]


# Global manager instance
_manager: Optional[ConfirmationManager] = None


def get_manager() -> ConfirmationManager:
    """Get the global confirmation manager."""
    global _manager
    if _manager is None:
        _manager = ConfirmationManager()
    return _manager


def create_confirmation_request(action: str, reason: str,
                                details: Dict[str, Any] = None,
                                timeout_minutes: int = 5) -> ConfirmationRequest:
    """
    Create a new confirmation request.
    
    Args:
        action: The action requiring confirmation
        reason: Why confirmation is needed
        details: Additional details about the action
        timeout_minutes: Minutes until the request expires
        
    Returns:
        The created confirmation request
    """
    return get_manager().create_request(action, reason, details, timeout_minutes)


def validate_confirmation(token: str, approved: bool,
                         responded_by: str = None) -> Optional[ConfirmationRequest]:
    """
    Validate and respond to a confirmation request.
    
    Args:
        token: The confirmation token
        approved: Whether to approve
        responded_by: Who responded
        
    Returns:
        The request if valid, None otherwise
    """
    return get_manager().respond(token, approved, responded_by)