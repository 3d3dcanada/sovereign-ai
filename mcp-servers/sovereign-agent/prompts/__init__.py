"""
Sovereign Agent Prompts Module
Version: 2.0.0 - February 2026

This module contains system prompts and prompt templates for the sovereign agent.
"""

from .system_prompts import (
    AGENT_SYSTEM_PROMPT,
    PLANNING_PROMPT,
    EXECUTION_PROMPT,
    REFLECTION_PROMPT,
    SAFETY_PROMPT,
    get_task_prompt
)

__all__ = [
    "AGENT_SYSTEM_PROMPT",
    "PLANNING_PROMPT",
    "EXECUTION_PROMPT",
    "REFLECTION_PROMPT",
    "SAFETY_PROMPT",
    "get_task_prompt"
]