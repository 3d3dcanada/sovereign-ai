"""
Sovereign Agent Safety Module
Version: 2.0.0 - February 2026

This module provides safety mechanisms for the sovereign agent including:
- Command classification
- Risk assessment
- Confirmation system
- Audit logging
"""

from .classifier import (
    SafetyTier,
    CommandRule,
    classify_command,
    get_all_rules,
    add_custom_rule
)

from .audit import (
    AuditLogger,
    log_action,
    get_audit_log
)

from .confirmation import (
    ConfirmationManager,
    ConfirmationRequest,
    create_confirmation_request,
    validate_confirmation
)

__all__ = [
    # Classifier
    "SafetyTier",
    "CommandRule",
    "classify_command",
    "get_all_rules",
    "add_custom_rule",
    # Audit
    "AuditLogger",
    "log_action",
    "get_audit_log",
    # Confirmation
    "ConfirmationManager",
    "ConfirmationRequest",
    "create_confirmation_request",
    "validate_confirmation"
]