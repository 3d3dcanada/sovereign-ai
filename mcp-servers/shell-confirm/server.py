#!/usr/bin/env python3
"""
Shell Confirm MCP Server
Executes shell commands with safety tiers and confirmation requirements.

Safety Tiers:
- SAFE: Auto-execute (ls, cat, grep, head, etc.)
- MODERATE: Log and execute (git, npm, pip, docker ps)
- ELEVATED: Notify and execute (docker run, npm install)
- DANGEROUS: Require confirmation button (rm -rf, sudo, mkfs, dd)
"""

import asyncio
import json
import logging
import os
import subprocess
import shlex
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional
from datetime import datetime

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("shell-confirm")

# Create server instance
server = Server("shell-confirm")


class SafetyTier(Enum):
    SAFE = "safe"
    MODERATE = "moderate"
    ELEVATED = "elevated"
    DANGEROUS = "dangerous"


@dataclass
class CommandRule:
    tier: SafetyTier
    patterns: list[str]
    description: str


# Safety rules configuration
SAFETY_RULES = [
    # SAFE - Auto-execute
    CommandRule(
        SafetyTier.SAFE,
        ["ls", "cat", "head", "tail", "grep", "find", "wc", "sort", "uniq",
         "echo", "pwd", "whoami", "date", "uname", "which", "type", "file",
         "stat", "du", "df", "free", "uptime", "ps aux", "top -n 1", "htop -n 1"],
        "Read-only system commands"
    ),
    
    # MODERATE - Log and execute
    CommandRule(
        SafetyTier.MODERATE,
        ["git status", "git log", "git diff", "git branch", "git remote",
         "npm list", "npm outdated", "pip list", "pip show",
         "docker ps", "docker images", "docker logs", "docker inspect",
         "python --version", "python3 --version", "node --version", "npm --version"],
        "Non-destructive development commands"
    ),
    
    # ELEVATED - Notify and execute
    CommandRule(
        SafetyTier.ELEVATED,
        ["git pull", "git push", "git commit", "git checkout", "git merge",
         "npm install", "npm update", "npm uninstall",
         "pip install", "pip uninstall", "pip upgrade",
         "docker pull", "docker run", "docker exec", "docker build",
         "mkdir", "touch", "mv", "cp"],
        "Commands that modify files or state"
    ),
    
    # DANGEROUS - Require confirmation
    CommandRule(
        SafetyTier.DANGEROUS,
        ["rm -rf", "rm -r", "sudo", "mkfs", "dd", "fdisk", "format",
         "chmod 777", "chown -R", "> /dev/", "kill -9", "pkill -9",
         "shutdown", "reboot", "halt", "poweroff",
         "docker rm", "docker rmi", "docker system prune",
         "git push --force", "git reset --hard", "git clean -fd"],
        "Destructive or system-level commands"
    ),
]


def classify_command(command: str) -> tuple[SafetyTier, str]:
    """Classify a command into a safety tier."""
    command_lower = command.lower().strip()
    
    # Check dangerous first (highest priority)
    for rule in SAFETY_RULES:
        if rule.tier == SafetyTier.DANGEROUS:
            for pattern in rule.patterns:
                if pattern.lower() in command_lower:
                    return rule.tier, rule.description
    
    # Check elevated
    for rule in SAFETY_RULES:
        if rule.tier == SafetyTier.ELEVATED:
            for pattern in rule.patterns:
                if pattern.lower() in command_lower:
                    return rule.tier, rule.description
    
    # Check moderate
    for rule in SAFETY_RULES:
        if rule.tier == SafetyTier.MODERATE:
            for pattern in rule.patterns:
                if command_lower.startswith(pattern.lower()):
                    return rule.tier, rule.description
    
    # Check safe
    for rule in SAFETY_RULES:
        if rule.tier == SafetyTier.SAFE:
            for pattern in rule.patterns:
                if command_lower.startswith(pattern.lower()):
                    return rule.tier, rule.description
    
    # Default to elevated for unknown commands
    return SafetyTier.ELEVATED, "Unknown command - requires review"


def log_command(command: str, tier: SafetyTier, result: str, success: bool):
    """Log command execution to audit log."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "tier": tier.value,
        "success": success,
        "result_preview": result[:500] if result else None
    }
    
    log_dir = os.environ.get("LOG_DIR", "/app/logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, "shell-audit.jsonl")
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    logger.info(f"Command executed: {command} (tier: {tier.value}, success: {success})")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="execute_command",
            description="""Execute a shell command with safety checks.
            
Safety Tiers:
- SAFE: Auto-executed (read-only commands)
- MODERATE: Logged and executed (git status, docker ps)
- ELEVATED: Notified and executed (npm install, docker run)
- DANGEROUS: Requires confirmation button (rm -rf, sudo)

Returns the command classification and result.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute"
                    },
                    "confirmation_token": {
                        "type": "string",
                        "description": "Confirmation token for dangerous commands (optional)"
                    }
                },
                "required": ["command"]
            }
        ),
        Tool(
            name="classify_command",
            description="Classify a command's safety tier without executing it",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command to classify"
                    }
                },
                "required": ["command"]
            }
        ),
        Tool(
            name="request_confirmation",
            description="Request user confirmation for a dangerous command",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command requiring confirmation"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Why this command is dangerous"
                    }
                },
                "required": ["command", "reason"]
            }
        )
    ]


# Store pending confirmations
pending_confirmations: dict[str, dict] = {}


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    
    if name == "classify_command":
        command = arguments.get("command", "")
        tier, description = classify_command(command)
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "command": command,
                "tier": tier.value,
                "description": description,
                "requires_confirmation": tier == SafetyTier.DANGEROUS
            }, indent=2)
        )]
    
    elif name == "request_confirmation":
        command = arguments.get("command", "")
        reason = arguments.get("reason", "")
        
        import uuid
        token = str(uuid.uuid4())
        
        pending_confirmations[token] = {
            "command": command,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "confirmation_required",
                "confirmation_token": token,
                "command": command,
                "reason": reason,
                "message": f"⚠️ DANGEROUS COMMAND DETECTED\n\nCommand: {command}\n\nReason: {reason}\n\nTo execute, provide the confirmation_token with your command."
            }, indent=2)
        )]
    
    elif name == "execute_command":
        command = arguments.get("command", "")
        confirmation_token = arguments.get("confirmation_token")
        
        if not command:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "No command provided"}, indent=2)
            )]
        
        tier, description = classify_command(command)
        
        # Handle dangerous commands
        if tier == SafetyTier.DANGEROUS:
            if not confirmation_token:
                # Request confirmation
                import uuid
                token = str(uuid.uuid4())
                
                pending_confirmations[token] = {
                    "command": command,
                    "tier": tier.value,
                    "description": description,
                    "timestamp": datetime.now().isoformat()
                }
                
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "confirmation_required",
                        "confirmation_token": token,
                        "command": command,
                        "tier": tier.value,
                        "description": description,
                        "message": f"⚠️ DANGEROUS COMMAND\n\nThis command requires confirmation.\n\nCommand: {command}\n\nTo execute, call execute_command again with confirmation_token: {token}"
                    }, indent=2)
                )]
            
            # Validate confirmation token
            if confirmation_token not in pending_confirmations:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "Invalid confirmation token",
                        "message": "The confirmation token is invalid or expired. Request a new confirmation."
                    }, indent=2)
                )]
            
            # Check if token matches command
            confirmation = pending_confirmations.pop(confirmation_token)
            if confirmation["command"] != command:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "Token mismatch",
                        "message": "Confirmation token does not match this command."
                    }, indent=2)
                )]
        
        # Execute the command
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            success = result.returncode == 0
            output = result.stdout if success else result.stderr
            
            # Log the execution
            log_command(command, tier, output, success)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "success" if success else "error",
                    "command": command,
                    "tier": tier.value,
                    "description": description,
                    "return_code": result.returncode,
                    "output": output[:10000] if output else None,  # Limit output size
                    "executed_at": datetime.now().isoformat()
                }, indent=2)
            )]
            
        except subprocess.TimeoutExpired:
            log_command(command, tier, "Timeout", False)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Command timed out",
                    "command": command,
                    "timeout": 300
                }, indent=2)
            )]
        except Exception as e:
            log_command(command, tier, str(e), False)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "command": command
                }, indent=2)
            )]
    
    return [TextContent(
        type="text",
        text=json.dumps({"error": f"Unknown tool: {name}"}, indent=2)
    )]


async def main():
    """Run the server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())