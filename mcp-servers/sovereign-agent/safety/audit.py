"""
Safety Audit Module
Version: 2.0.0 - February 2026

Provides audit logging for all agent actions.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import threading


@dataclass
class AuditEntry:
    """Single audit log entry."""
    timestamp: str
    action: str
    details: Dict[str, Any]
    success: bool
    tier: str = None
    user: str = None
    session_id: str = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "details": self.details,
            "success": self.success,
            "tier": self.tier,
            "user": self.user,
            "session_id": self.session_id
        }
    
    def to_jsonl(self) -> str:
        """Convert to JSONL format."""
        return json.dumps(self.to_dict())


class AuditLogger:
    """
    Thread-safe audit logger for agent actions.
    
    Logs all actions to a JSONL file for audit purposes.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, log_dir: str = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, log_dir: str = None):
        if self._initialized:
            return
            
        self.log_dir = log_dir or os.environ.get("LOG_DIR", "/app/logs")
        self.log_file = os.path.join(self.log_dir, "agent-audit.jsonl")
        self.entries: List[AuditEntry] = []
        self.max_memory_entries = 1000
        self._file_lock = threading.Lock()
        
        # Ensure log directory exists
        os.makedirs(self.log_dir, exist_ok=True)
        
        self._initialized = True
    
    def log(self, action: str, details: Dict[str, Any], success: bool,
            tier: str = None, user: str = None, session_id: str = None) -> AuditEntry:
        """
        Log an action.
        
        Args:
            action: The action performed
            details: Details about the action
            success: Whether the action succeeded
            tier: Safety tier (if applicable)
            user: User who initiated the action
            session_id: Session identifier
            
        Returns:
            The created audit entry
        """
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            action=action,
            details=details,
            success=success,
            tier=tier,
            user=user,
            session_id=session_id
        )
        
        # Add to memory
        self.entries.append(entry)
        if len(self.entries) > self.max_memory_entries:
            self.entries = self.entries[-self.max_memory_entries:]
        
        # Write to file
        self._write_entry(entry)
        
        return entry
    
    def _write_entry(self, entry: AuditEntry):
        """Write entry to log file."""
        with self._file_lock:
            try:
                with open(self.log_file, "a") as f:
                    f.write(entry.to_jsonl() + "\n")
            except Exception as e:
                print(f"Failed to write audit log: {e}")
    
    def get_entries(self, limit: int = 100, action_filter: str = None,
                    success_only: bool = None) -> List[AuditEntry]:
        """
        Get recent entries.
        
        Args:
            limit: Maximum number of entries to return
            action_filter: Filter by action type
            success_only: Filter by success status
            
        Returns:
            List of matching entries
        """
        entries = self.entries
        
        if action_filter:
            entries = [e for e in entries if action_filter in e.action]
        
        if success_only is not None:
            entries = [e for e in entries if e.success == success_only]
        
        return entries[-limit:]
    
    def get_stats(self) -> Dict:
        """Get statistics about logged actions."""
        if not self.entries:
            return {"total": 0}
        
        total = len(self.entries)
        successful = sum(1 for e in self.entries if e.success)
        failed = total - successful
        
        # Count by action type
        action_counts = {}
        for entry in self.entries:
            action = entry.action
            action_counts[action] = action_counts.get(action, 0) + 1
        
        # Count by tier
        tier_counts = {}
        for entry in self.entries:
            if entry.tier:
                tier_counts[entry.tier] = tier_counts.get(entry.tier, 0) + 1
        
        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "success_rate": round(successful / total * 100, 1) if total > 0 else 0,
            "action_counts": action_counts,
            "tier_counts": tier_counts
        }
    
    def clear_memory(self):
        """Clear in-memory entries (keeps file logs)."""
        self.entries = []
    
    def read_file_entries(self, limit: int = 100) -> List[Dict]:
        """Read entries from the log file."""
        entries = []
        try:
            with open(self.log_file, "r") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    if line.strip():
                        entries.append(json.loads(line))
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error reading audit log: {e}")
        
        return entries


# Global logger instance
_logger: Optional[AuditLogger] = None


def get_logger(log_dir: str = None) -> AuditLogger:
    """Get the global audit logger."""
    global _logger
    if _logger is None:
        _logger = AuditLogger(log_dir)
    return _logger


def log_action(action: str, details: Dict[str, Any], success: bool,
               tier: str = None, user: str = None, session_id: str = None) -> AuditEntry:
    """
    Convenience function to log an action.
    
    Args:
        action: The action performed
        details: Details about the action
        success: Whether the action succeeded
        tier: Safety tier (if applicable)
        user: User who initiated the action
        session_id: Session identifier
        
    Returns:
        The created audit entry
    """
    return get_logger().log(action, details, success, tier, user, session_id)


def get_audit_log(limit: int = 100) -> List[Dict]:
    """
    Get recent audit log entries.
    
    Args:
        limit: Maximum number of entries
        
    Returns:
        List of audit entries
    """
    return [e.to_dict() for e in get_logger().get_entries(limit)]