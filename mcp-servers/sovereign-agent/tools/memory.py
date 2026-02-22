"""
Memory Tool Module
Version: 2.0.0 - February 2026

Provides memory operations for the agent.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from .base import BaseTool, ToolResult


class MemoryTool(BaseTool):
    """Tool for memory operations."""
    
    @property
    def name(self) -> str:
        return "memory"
    
    @property
    def description(self) -> str:
        return "Store and retrieve information from agent memory"
    
    def __init__(self, work_dir: str = "/home/wess", log_dir: str = None,
                 memory_file: str = None):
        super().__init__(work_dir, log_dir)
        self.memory_file = memory_file or os.path.join(
            os.environ.get("LOG_DIR", "/app/logs"),
            "agent-memory.json"
        )
        self._memory: Dict[str, Dict] = {}
        self._load_memory()
    
    def _load_memory(self):
        """Load memory from file."""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    self._memory = json.load(f)
        except Exception:
            self._memory = {}
    
    def _save_memory(self):
        """Save memory to file."""
        try:
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            with open(self.memory_file, 'w') as f:
                json.dump(self._memory, f, indent=2)
        except Exception as e:
            print(f"Failed to save memory: {e}")
    
    def remember(self, key: str, value: Any, tags: List[str] = None) -> ToolResult:
        """Store a value in memory."""
        try:
            entry = {
                "value": value,
                "timestamp": datetime.now().isoformat(),
                "tags": tags or []
            }
            
            self._memory[key] = entry
            self._save_memory()
            
            return ToolResult(
                success=True,
                output=f"Remembered: {key}",
                metadata={
                    "key": key,
                    "operation": "remember"
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def recall(self, key: str) -> ToolResult:
        """Retrieve a value from memory."""
        try:
            if key not in self._memory:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Key not found: {key}"
                )
            
            entry = self._memory[key]
            
            return ToolResult(
                success=True,
                output=entry.get("value"),
                metadata={
                    "key": key,
                    "timestamp": entry.get("timestamp"),
                    "tags": entry.get("tags", []),
                    "operation": "recall"
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def forget(self, key: str) -> ToolResult:
        """Remove a value from memory."""
        try:
            if key not in self._memory:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Key not found: {key}"
                )
            
            del self._memory[key]
            self._save_memory()
            
            return ToolResult(
                success=True,
                output=f"Forgot: {key}",
                metadata={"key": key, "operation": "forget"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def list_keys(self, tag: str = None) -> ToolResult:
        """List all keys in memory."""
        try:
            if tag:
                keys = [
                    k for k, v in self._memory.items()
                    if tag in v.get("tags", [])
                ]
            else:
                keys = list(self._memory.keys())
            
            return ToolResult(
                success=True,
                output=keys,
                metadata={
                    "count": len(keys),
                    "tag_filter": tag,
                    "operation": "list_keys"
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def search(self, query: str) -> ToolResult:
        """Search memory for matching keys or values."""
        try:
            query_lower = query.lower()
            results = []
            
            for key, entry in self._memory.items():
                value = str(entry.get("value", ""))
                
                if query_lower in key.lower() or query_lower in value.lower():
                    results.append({
                        "key": key,
                        "value": value[:200],  # Truncate for display
                        "timestamp": entry.get("timestamp"),
                        "tags": entry.get("tags", [])
                    })
            
            return ToolResult(
                success=True,
                output=results,
                metadata={
                    "query": query,
                    "count": len(results),
                    "operation": "search"
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def clear(self) -> ToolResult:
        """Clear all memory."""
        try:
            count = len(self._memory)
            self._memory = {}
            self._save_memory()
            
            return ToolResult(
                success=True,
                output=f"Cleared {count} items from memory",
                metadata={"cleared_count": count, "operation": "clear"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def export_memory(self) -> ToolResult:
        """Export all memory as JSON."""
        try:
            return ToolResult(
                success=True,
                output=self._memory,
                metadata={
                    "count": len(self._memory),
                    "operation": "export"
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute a memory operation."""
        operations = {
            "remember": self.remember,
            "recall": self.recall,
            "forget": self.forget,
            "list_keys": self.list_keys,
            "search": self.search,
            "clear": self.clear,
            "export": self.export_memory
        }
        
        if operation not in operations:
            return ToolResult(
                success=False,
                output=None,
                error=f"Unknown operation: {operation}"
            )
        
        return operations[operation](**kwargs)