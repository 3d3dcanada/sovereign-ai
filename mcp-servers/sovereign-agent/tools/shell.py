"""
Shell Tool Module
Version: 2.0.0 - February 2026

Provides shell command execution with safety checks.
"""

import subprocess
import os
from typing import Optional
from .base import BaseTool, ToolResult
from ..safety import classify_command, SafetyTier


class ShellTool(BaseTool):
    """Tool for executing shell commands with safety checks."""
    
    @property
    def name(self) -> str:
        return "shell"
    
    @property
    def description(self) -> str:
        return "Execute shell commands with safety tier classification"
    
    def execute(self, command: str, timeout: int = 300, 
                confirm_token: str = None) -> ToolResult:
        """
        Execute a shell command.
        
        Args:
            command: The shell command to execute
            timeout: Timeout in seconds
            confirm_token: Confirmation token for dangerous commands
            
        Returns:
            ToolResult with execution outcome
        """
        if not command:
            return ToolResult(
                success=False,
                output=None,
                error="No command provided"
            )
        
        # Classify command
        tier, description = classify_command(command)
        
        # Check if confirmation is required
        if tier == SafetyTier.DANGEROUS and not confirm_token:
            return ToolResult(
                success=False,
                output={
                    "requires_confirmation": True,
                    "tier": tier.value,
                    "description": description,
                    "command": command
                },
                error="Dangerous command requires confirmation token"
            )
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.work_dir
            )
            
            success = result.returncode == 0
            output = result.stdout if success else result.stderr
            
            return ToolResult(
                success=success,
                output=output[:10000] if output else "",
                metadata={
                    "command": command,
                    "tier": tier.value,
                    "return_code": result.returncode,
                    "description": description
                }
            )
            
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output=None,
                error=f"Command timed out after {timeout} seconds",
                metadata={"command": command, "tier": tier.value}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
                metadata={"command": command, "tier": tier.value}
            )
    
    def get_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default 300)"
                    },
                    "confirm_token": {
                        "type": "string",
                        "description": "Confirmation token for dangerous commands"
                    }
                },
                "required": ["command"]
            }
        }