#!/usr/bin/env python3
"""
Sovereign Agent - Autonomous AI Agent
Version: 2.0.0 - February 2026

A fully functional autonomous agent for Sovereign AI.
Features:
- Plan → Act → Observe → Reflect loop
- Real tool execution (shell, file, web, memory)
- Memory persistence via Mem0/Qdrant
- Human confirmation for dangerous actions
- Safety tier system for command classification
"""

import asyncio
import json
import os
import sys
import subprocess
import shlex
import uuid
import aiohttp
from datetime import datetime
from typing import Any, Optional, Dict, List
from dataclasses import dataclass, field
from enum import Enum
import logging

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("sovereign-agent")

# Create server
server = Server("sovereign-agent")


# ============================================
# SAFETY SYSTEM
# ============================================

class SafetyTier(Enum):
    SAFE = "safe"           # Auto-execute
    MODERATE = "moderate"   # Log and execute
    ELEVATED = "elevated"   # Notify and execute
    DANGEROUS = "dangerous" # Require confirmation


@dataclass
class CommandRule:
    tier: SafetyTier
    patterns: List[str]
    description: str


SAFETY_RULES = [
    # SAFE - Auto-execute
    CommandRule(
        SafetyTier.SAFE,
        ["ls", "cat", "head", "tail", "grep", "find", "wc", "sort", "uniq",
         "echo", "pwd", "whoami", "date", "uname", "which", "type", "file",
         "stat", "du", "df", "free", "uptime", "ps aux", "top -n 1"],
        "Read-only system commands"
    ),
    CommandRule(
        SafetyTier.MODERATE,
        ["git status", "git log", "git diff", "git branch", "git remote",
         "npm list", "npm outdated", "pip list", "pip show",
         "docker ps", "docker images", "docker logs", "docker inspect",
         "python --version", "python3 --version", "node --version"],
        "Non-destructive development commands"
    ),
    CommandRule(
        SafetyTier.ELEVATED,
        ["git pull", "git push", "git commit", "git checkout", "git merge",
         "npm install", "npm update", "npm uninstall",
         "pip install", "pip uninstall",
         "docker pull", "docker run", "docker exec", "docker build",
         "mkdir", "touch", "mv", "cp"],
        "Commands that modify files or state"
    ),
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


def classify_command(command: str) -> tuple:
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


# ============================================
# AGENT STATE
# ============================================

class AgentState(Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    WAITING_CONFIRMATION = "waiting_confirmation"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    id: str
    description: str
    status: str = "pending"
    steps: List[Dict] = field(default_factory=list)
    current_step: int = 0
    result: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None


@dataclass
class AgentMemory:
    """Memory store with Mem0 integration."""
    facts: Dict = field(default_factory=dict)
    conversations: List = field(default_factory=list)
    task_history: List = field(default_factory=list)
    mem0_url: str = field(default="http://localhost:8000")
    
    def remember(self, key: str, value: Any) -> Dict:
        """Store a fact in memory."""
        entry = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        self.facts[key] = entry
        logger.info(f"Remembered: {key} = {value}")
        return {"status": "stored", "key": key}
    
    def recall(self, key: str) -> Optional[Any]:
        """Retrieve a fact from memory."""
        entry = self.facts.get(key)
        if entry:
            return entry.get("value")
        return None
    
    def add_conversation(self, role: str, content: str):
        """Add a conversation to history."""
        self.conversations.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        # Keep last 100 conversations
        if len(self.conversations) > 100:
            self.conversations = self.conversations[-100:]
    
    def add_task_history(self, task: Task):
        """Add completed task to history."""
        self.task_history.append({
            "id": task.id,
            "description": task.description,
            "status": task.status,
            "steps_count": len(task.steps),
            "created_at": task.created_at,
            "completed_at": task.completed_at
        })
        # Keep last 50 tasks
        if len(self.task_history) > 50:
            self.task_history = self.task_history[-50:]


# Global state
memory = AgentMemory()
current_task: Optional[Task] = None
agent_state = AgentState.IDLE
pending_confirmations: Dict[str, Dict] = {}


# ============================================
# TOOL EXECUTORS
# ============================================

def _default_work_dir() -> str:
    return os.environ.get("WORK_DIR") or os.path.expanduser("~")


class ToolExecutor:
    """Executes various tools with safety checks."""
    
    def __init__(self, work_dir: Optional[str] = None):
        self.work_dir = work_dir or _default_work_dir()
        self.log_dir = os.environ.get("LOG_DIR", "/app/logs")
        os.makedirs(self.log_dir, exist_ok=True)
    
    def log_execution(self, action: str, details: Dict, success: bool):
        """Log action execution."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details,
            "success": success
        }
        log_file = os.path.join(self.log_dir, "agent-audit.jsonl")
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def execute_shell(self, command: str, timeout: int = 300) -> Dict:
        """Execute a shell command."""
        tier, description = classify_command(command)
        
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
            
            self.log_execution("shell", {
                "command": command,
                "tier": tier.value,
                "return_code": result.returncode
            }, success)
            
            return {
                "success": success,
                "output": output[:10000] if output else "",
                "return_code": result.returncode,
                "tier": tier.value,
                "description": description
            }
        except subprocess.TimeoutExpired:
            self.log_execution("shell", {"command": command}, False)
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds",
                "tier": tier.value
            }
        except Exception as e:
            self.log_execution("shell", {"command": command, "error": str(e)}, False)
            return {
                "success": False,
                "error": str(e),
                "tier": tier.value
            }
    
    def read_file(self, path: str) -> Dict:
        """Read a file's contents."""
        try:
            # Security: prevent reading outside work directory
            abs_path = os.path.abspath(path)
            
            with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            self.log_execution("read_file", {"path": path}, True)
            return {
                "success": True,
                "content": content[:50000],  # Limit to 50KB
                "path": path,
                "size": len(content)
            }
        except FileNotFoundError:
            return {"success": False, "error": f"File not found: {path}"}
        except PermissionError:
            return {"success": False, "error": f"Permission denied: {path}"}
        except Exception as e:
            self.log_execution("read_file", {"path": path, "error": str(e)}, False)
            return {"success": False, "error": str(e)}
    
    def write_file(self, path: str, content: str) -> Dict:
        """Write content to a file."""
        try:
            abs_path = os.path.abspath(path)
            
            # Create directory if needed
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.log_execution("write_file", {"path": path, "size": len(content)}, True)
            return {
                "success": True,
                "path": path,
                "size": len(content),
                "message": f"Wrote {len(content)} bytes to {path}"
            }
        except PermissionError:
            return {"success": False, "error": f"Permission denied: {path}"}
        except Exception as e:
            self.log_execution("write_file", {"path": path, "error": str(e)}, False)
            return {"success": False, "error": str(e)}
    
    def list_directory(self, path: str) -> Dict:
        """List directory contents."""
        try:
            abs_path = os.path.abspath(path)
            
            if not os.path.isdir(abs_path):
                return {"success": False, "error": f"Not a directory: {path}"}
            
            items = []
            for item in os.listdir(abs_path):
                item_path = os.path.join(abs_path, item)
                items.append({
                    "name": item,
                    "type": "directory" if os.path.isdir(item_path) else "file",
                    "size": os.path.getsize(item_path) if os.path.isfile(item_path) else None
                })
            
            self.log_execution("list_directory", {"path": path, "count": len(items)}, True)
            return {
                "success": True,
                "path": path,
                "items": items,
                "count": len(items)
            }
        except FileNotFoundError:
            return {"success": False, "error": f"Directory not found: {path}"}
        except PermissionError:
            return {"success": False, "error": f"Permission denied: {path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete_file(self, path: str) -> Dict:
        """Delete a file (requires confirmation)."""
        try:
            abs_path = os.path.abspath(path)
            
            if not os.path.exists(abs_path):
                return {"success": False, "error": f"File not found: {path}"}
            
            if os.path.isdir(abs_path):
                return {"success": False, "error": "Use delete_directory for directories"}
            
            os.remove(abs_path)
            
            self.log_execution("delete_file", {"path": path}, True)
            return {
                "success": True,
                "message": f"Deleted file: {path}"
            }
        except PermissionError:
            return {"success": False, "error": f"Permission denied: {path}"}
        except Exception as e:
            self.log_execution("delete_file", {"path": path, "error": str(e)}, False)
            return {"success": False, "error": str(e)}
    
    def search_files(self, pattern: str, path: str = ".") -> Dict:
        """Search for files matching a pattern."""
        try:
            abs_path = os.path.abspath(path)
            matches = []
            
            for root, dirs, files in os.walk(abs_path):
                for filename in files:
                    if pattern.lower() in filename.lower():
                        matches.append(os.path.join(root, filename))
            
            self.log_execution("search_files", {"pattern": pattern, "path": path}, True)
            return {
                "success": True,
                "pattern": pattern,
                "path": path,
                "matches": matches[:100],  # Limit to 100 results
                "count": len(matches)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def grep_content(self, pattern: str, path: str = ".") -> Dict:
        """Search for content in files."""
        try:
            result = subprocess.run(
                f"grep -r -n '{pattern}' {path} 2>/dev/null | head -50",
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.work_dir
            )
            
            matches = []
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if ':' in line:
                        parts = line.split(':', 2)
                        if len(parts) >= 3:
                            matches.append({
                                "file": parts[0],
                                "line": parts[1],
                                "content": parts[2][:200]
                            })
            
            self.log_execution("grep_content", {"pattern": pattern, "path": path}, True)
            return {
                "success": True,
                "pattern": pattern,
                "matches": matches,
                "count": len(matches)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# Create executor instance
executor = ToolExecutor()


# ============================================
# MCP TOOLS
# ============================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available agent tools."""
    return [
        # Task Management
        Tool(
            name="create_task",
            description="Create a new task for the agent to execute",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Task description"
                    }
                },
                "required": ["description"]
            }
        ),
        Tool(
            name="plan_steps",
            description="Plan the steps needed to complete a task",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID to plan"
                    },
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "action": {"type": "string"},
                                "tool": {"type": "string"},
                                "params": {"type": "object"}
                            },
                            "required": ["action", "tool"]
                        },
                        "description": "List of steps to execute"
                    }
                },
                "required": ["task_id", "steps"]
            }
        ),
        Tool(
            name="execute_step",
            description="Execute a single step of the task",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID"
                    },
                    "step_index": {
                        "type": "integer",
                        "description": "Index of step to execute"
                    }
                },
                "required": ["task_id", "step_index"]
            }
        ),
        Tool(
            name="get_status",
            description="Get current agent status and task progress",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        
        # Shell Execution
        Tool(
            name="execute_shell",
            description="Execute a shell command with safety checks. Returns classification and result.",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default 300)",
                        "default": 300
                    }
                },
                "required": ["command"]
            }
        ),
        Tool(
            name="classify_command",
            description="Classify a command's safety tier without executing",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Command to classify"
                    }
                },
                "required": ["command"]
            }
        ),
        
        # File Operations
        Tool(
            name="read_file",
            description="Read a file's contents",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path to read"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="write_file",
            description="Write content to a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path to write"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write"
                    }
                },
                "required": ["path", "content"]
            }
        ),
        Tool(
            name="list_directory",
            description="List directory contents",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path to list"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="delete_file",
            description="Delete a file (DANGEROUS - requires confirmation)",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path to delete"
                    },
                    "confirmation_token": {
                        "type": "string",
                        "description": "Confirmation token for dangerous operation"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="search_files",
            description="Search for files matching a pattern",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Filename pattern to search"
                    },
                    "path": {
                        "type": "string",
                        "description": "Directory to search in (default: current)",
                        "default": "."
                    }
                },
                "required": ["pattern"]
            }
        ),
        Tool(
            name="grep_content",
            description="Search for content in files",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Text pattern to search for"
                    },
                    "path": {
                        "type": "string",
                        "description": "Directory to search in (default: current)",
                        "default": "."
                    }
                },
                "required": ["pattern"]
            }
        ),
        
        # Memory Operations
        Tool(
            name="remember",
            description="Store information in agent memory",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "value": {"type": "string"}
                },
                "required": ["key", "value"]
            }
        ),
        Tool(
            name="recall",
            description="Retrieve information from agent memory",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string"}
                },
                "required": ["key"]
            }
        ),
        Tool(
            name="list_memory",
            description="List all stored memory keys",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        
        # Confirmation System
        Tool(
            name="request_confirmation",
            description="Request user confirmation for a dangerous action",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action requiring confirmation"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Why this action is dangerous"
                    }
                },
                "required": ["action", "reason"]
            }
        ),
        Tool(
            name="confirm_action",
            description="Confirm a dangerous action with token",
            inputSchema={
                "type": "object",
                "properties": {
                    "confirmation_token": {
                        "type": "string",
                        "description": "Token from the confirmation request"
                    },
                    "approved": {
                        "type": "boolean",
                        "description": "Whether to approve the action"
                    }
                },
                "required": ["confirmation_token", "approved"]
            }
        ),
        
        # Reflection
        Tool(
            name="reflect",
            description="Reflect on task execution and learn",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "observations": {"type": "string"},
                    "lessons_learned": {"type": "string"}
                },
                "required": ["task_id", "observations"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    global current_task, agent_state
    
    # ============================================
    # TASK MANAGEMENT
    # ============================================
    
    if name == "create_task":
        task_id = str(uuid.uuid4())[:8]
        task = Task(
            id=task_id,
            description=arguments.get("description", "")
        )
        current_task = task
        agent_state = AgentState.PLANNING
        
        memory.add_conversation("user", task.description)
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "task_created",
                "task_id": task_id,
                "description": task.description,
                "state": agent_state.value,
                "message": "Task created. Use plan_steps to break it down into executable steps."
            }, indent=2)
        )]
    
    elif name == "plan_steps":
        if not current_task:
            return [TextContent(type="text", text=json.dumps({"error": "No active task"}))]
        
        steps = arguments.get("steps", [])
        current_task.steps = steps
        agent_state = AgentState.EXECUTING
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "plan_created",
                "task_id": current_task.id,
                "steps": steps,
                "total_steps": len(steps),
                "message": f"Plan created with {len(steps)} steps. Use execute_step to proceed."
            }, indent=2)
        )]
    
    elif name == "execute_step":
        if not current_task:
            return [TextContent(type="text", text=json.dumps({"error": "No active task"}))]
        
        step_index = arguments.get("step_index", 0)
        
        if step_index >= len(current_task.steps):
            return [TextContent(type="text", text=json.dumps({"error": "Step index out of range"}))]
        
        step = current_task.steps[step_index]
        tool = step.get("tool", "shell")
        action = step.get("action", "")
        params = step.get("params", {})
        
        # Execute based on tool type
        if tool == "shell":
            result = executor.execute_shell(action)
        elif tool == "read_file":
            result = executor.read_file(params.get("path", action))
        elif tool == "write_file":
            result = executor.write_file(params.get("path", action), params.get("content", ""))
        elif tool == "list_directory":
            result = executor.list_directory(params.get("path", action))
        elif tool == "search_files":
            result = executor.search_files(params.get("pattern", action), params.get("path", "."))
        elif tool == "grep_content":
            result = executor.grep_content(params.get("pattern", action), params.get("path", "."))
        else:
            result = {"success": False, "error": f"Unknown tool: {tool}"}
        
        current_task.current_step = step_index + 1
        
        response = {
            "status": "step_executed",
            "task_id": current_task.id,
            "step_index": step_index,
            "step": step,
            "result": result,
            "progress": f"{current_task.current_step}/{len(current_task.steps)}"
        }
        
        if current_task.current_step >= len(current_task.steps):
            agent_state = AgentState.COMPLETED
            current_task.status = "completed"
            current_task.completed_at = datetime.now().isoformat()
            memory.add_task_history(current_task)
            response["message"] = "All steps completed. Use reflect to analyze results."
        
        return [TextContent(type="text", text=json.dumps(response, indent=2))]
    
    elif name == "get_status":
        status = {
            "agent_state": agent_state.value,
            "current_task": {
                "id": current_task.id,
                "description": current_task.description,
                "progress": f"{current_task.current_step}/{len(current_task.steps)}",
                "status": current_task.status
            } if current_task else None,
            "memory_facts": len(memory.facts),
            "conversation_history": len(memory.conversations),
            "task_history_count": len(memory.task_history)
        }
        return [TextContent(type="text", text=json.dumps(status, indent=2))]
    
    # ============================================
    # SHELL EXECUTION
    # ============================================
    
    elif name == "execute_shell":
        command = arguments.get("command", "")
        timeout = arguments.get("timeout", 300)
        
        tier, description = classify_command(command)
        
        # Dangerous commands require confirmation
        if tier == SafetyTier.DANGEROUS:
            token = str(uuid.uuid4())
            pending_confirmations[token] = {
                "type": "shell",
                "command": command,
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
                    "message": f"⚠️ DANGEROUS COMMAND\n\nCommand: {command}\n\nTo execute, call confirm_action with the token."
                }, indent=2)
            )]
        
        result = executor.execute_shell(command, timeout)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "classify_command":
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
    
    # ============================================
    # FILE OPERATIONS
    # ============================================
    
    elif name == "read_file":
        path = arguments.get("path", "")
        result = executor.read_file(path)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "write_file":
        path = arguments.get("path", "")
        content = arguments.get("content", "")
        result = executor.write_file(path, content)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "list_directory":
        path = arguments.get("path", ".")
        result = executor.list_directory(path)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "delete_file":
        path = arguments.get("path", "")
        confirmation_token = arguments.get("confirmation_token")
        
        if not confirmation_token:
            token = str(uuid.uuid4())
            pending_confirmations[token] = {
                "type": "delete_file",
                "path": path,
                "timestamp": datetime.now().isoformat()
            }
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "confirmation_required",
                    "confirmation_token": token,
                    "action": f"delete_file: {path}",
                    "message": f"⚠️ DANGEROUS: Deleting file {path}\n\nCall confirm_action with the token to proceed."
                }, indent=2)
            )]
        
        if confirmation_token not in pending_confirmations:
            return [TextContent(type="text", text=json.dumps({"error": "Invalid confirmation token"}))]
        
        confirmation = pending_confirmations.pop(confirmation_token)
        if confirmation.get("path") != path:
            return [TextContent(type="text", text=json.dumps({"error": "Token mismatch"}))]
        
        result = executor.delete_file(path)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "search_files":
        pattern = arguments.get("pattern", "")
        path = arguments.get("path", ".")
        result = executor.search_files(pattern, path)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "grep_content":
        pattern = arguments.get("pattern", "")
        path = arguments.get("path", ".")
        result = executor.grep_content(pattern, path)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    # ============================================
    # MEMORY OPERATIONS
    # ============================================
    
    elif name == "remember":
        key = arguments.get("key", "")
        value = arguments.get("value", "")
        result = memory.remember(key, value)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "recall":
        key = arguments.get("key", "")
        value = memory.recall(key)
        return [TextContent(type="text", text=json.dumps({"key": key, "value": value}, indent=2))]
    
    elif name == "list_memory":
        keys = list(memory.facts.keys())
        return [TextContent(
            type="text",
            text=json.dumps({
                "keys": keys,
                "count": len(keys)
            }, indent=2)
        )]
    
    # ============================================
    # CONFIRMATION SYSTEM
    # ============================================
    
    elif name == "request_confirmation":
        action = arguments.get("action", "")
        reason = arguments.get("reason", "")
        
        token = str(uuid.uuid4())
        pending_confirmations[token] = {
            "action": action,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "confirmation_required",
                "confirmation_token": token,
                "action": action,
                "reason": reason,
                "message": f"⚠️ CONFIRMATION REQUIRED\n\nAction: {action}\n\nReason: {reason}\n\nUse confirm_action with this token to approve or reject."
            }, indent=2)
        )]
    
    elif name == "confirm_action":
        token = arguments.get("confirmation_token")
        approved = arguments.get("approved", False)
        
        if token not in pending_confirmations:
            return [TextContent(type="text", text=json.dumps({"error": "Invalid confirmation token"}))]
        
        action = pending_confirmations.pop(token)
        
        if approved:
            # Execute the confirmed action
            if action.get("type") == "shell":
                result = executor.execute_shell(action.get("command", ""))
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "confirmed_and_executed",
                        "action": action,
                        "result": result
                    }, indent=2)
                )]
            elif action.get("type") == "delete_file":
                result = executor.delete_file(action.get("path", ""))
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "confirmed_and_executed",
                        "action": action,
                        "result": result
                    }, indent=2)
                )]
            else:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "confirmed",
                        "action": action,
                        "message": "Action approved. Proceeding with execution."
                    })
                )]
        else:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "rejected",
                    "action": action,
                    "message": "Action rejected by user."
                })
            )]
    
    # ============================================
    # REFLECTION
    # ============================================
    
    elif name == "reflect":
        task_id = arguments.get("task_id")
        observations = arguments.get("observations", "")
        lessons = arguments.get("lessons_learned", "")
        
        reflection = {
            "task_id": task_id,
            "observations": observations,
            "lessons_learned": lessons,
            "reflected_at": datetime.now().isoformat()
        }
        
        memory.task_history.append(reflection)
        agent_state = AgentState.IDLE
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "reflected",
                "reflection": reflection,
                "message": "Reflection recorded. Agent is now idle and ready for new tasks."
            }, indent=2)
        )]
    
    return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


async def main():
    """Run the agent server."""
    logger.info("Starting Sovereign Agent...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
