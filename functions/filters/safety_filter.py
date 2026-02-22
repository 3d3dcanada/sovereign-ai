"""
OpenWebUI Filter: Safety Filter
Version: 2.0.0
Description: Filter messages for safety and content policy compliance.

This filter checks incoming messages for potentially dangerous content
and adds safety warnings when appropriate.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
import re


class Filter:
    class Valves(BaseModel):
        enabled: bool = Field(default=True)
        warn_on_code: bool = Field(default=True)
        warn_on_system: bool = Field(default=True)
        log_filtered: bool = Field(default=True)
    
    def __init__(self):
        self.valves = self.Valves()
    
    def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Filter incoming messages."""
        if not self.valves.enabled:
            return body
        
        messages = body.get("messages", [])
        
        # Patterns to check
        dangerous_patterns = [
            r"rm\s+-rf",
            r"sudo\s+",
            r"chmod\s+777",
            r">\s*/dev/",
            r"mkfs",
            r"dd\s+if=",
            r":(){ :|:& };:",  # Fork bomb
        ]
        
        for message in messages:
            content = message.get("content", "")
            
            for pattern in dangerous_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    # Add warning to message
                    message["content"] = (
                        f"⚠️ **SAFETY WARNING**: This message contains potentially dangerous content.\n\n"
                        f"{content}\n\n"
                        f"*Please be cautious when executing any commands.*"
                    )
                    break
        
        return body
    
    def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Filter outgoing messages."""
        return body