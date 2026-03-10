"""
Base Tool Module
Version: 2.0.0 - February 2026

Provides the base class for all agent tools.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
from datetime import datetime
import os


@dataclass
class ToolResult:
    """Result of a tool execution."""
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


class BaseTool(ABC):
    """
    Abstract base class for all agent tools.
    
    All tools must implement:
    - name: Tool identifier
    - description: What the tool does
    - execute: The main execution method
    """
    
    def __init__(self, work_dir: Optional[str] = None, log_dir: str = None):
        """
        Initialize the tool.
        
        Args:
            work_dir: Working directory for operations
            log_dir: Directory for logs
        """
        self.work_dir = work_dir or os.environ.get("WORK_DIR") or os.path.expanduser("~")
        self.log_dir = log_dir or "/app/logs"
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool.
        
        Args:
            **kwargs: Tool-specific arguments
            
        Returns:
            ToolResult with execution outcome
        """
        pass
    
    def validate_args(self, **kwargs) -> Optional[str]:
        """
        Validate tool arguments.
        
        Args:
            **kwargs: Arguments to validate
            
        Returns:
            Error message if validation fails, None otherwise
        """
        return None
    
    def get_schema(self) -> Dict:
        """
        Get the tool's input schema.
        
        Returns:
            JSON Schema for tool inputs
        """
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {}
            }
        }
    
    def __call__(self, **kwargs) -> ToolResult:
        """Allow calling tool directly."""
        error = self.validate_args(**kwargs)
        if error:
            return ToolResult(success=False, output=None, error=error)
        
        return self.execute(**kwargs)
