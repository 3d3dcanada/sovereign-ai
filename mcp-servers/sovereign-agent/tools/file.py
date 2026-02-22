"""
File Tool Module
Version: 2.0.0 - February 2026

Provides file and directory operations.
"""

import os
import shutil
from typing import Optional, List
from .base import BaseTool, ToolResult


class FileTool(BaseTool):
    """Tool for file operations."""
    
    @property
    def name(self) -> str:
        return "file"
    
    @property
    def description(self) -> str:
        return "Read, write, and manage files"
    
    def read(self, path: str) -> ToolResult:
        """Read a file's contents."""
        try:
            abs_path = os.path.abspath(path)
            
            if not os.path.exists(abs_path):
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"File not found: {path}"
                )
            
            if not os.path.isfile(abs_path):
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Not a file: {path}"
                )
            
            with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            return ToolResult(
                success=True,
                output=content[:50000],  # Limit to 50KB
                metadata={
                    "path": path,
                    "size": len(content),
                    "operation": "read"
                }
            )
        except PermissionError:
            return ToolResult(
                success=False,
                output=None,
                error=f"Permission denied: {path}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def write(self, path: str, content: str) -> ToolResult:
        """Write content to a file."""
        try:
            abs_path = os.path.abspath(path)
            
            # Create directory if needed
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return ToolResult(
                success=True,
                output=f"Wrote {len(content)} bytes to {path}",
                metadata={
                    "path": path,
                    "size": len(content),
                    "operation": "write"
                }
            )
        except PermissionError:
            return ToolResult(
                success=False,
                output=None,
                error=f"Permission denied: {path}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def append(self, path: str, content: str) -> ToolResult:
        """Append content to a file."""
        try:
            abs_path = os.path.abspath(path)
            
            with open(abs_path, 'a', encoding='utf-8') as f:
                f.write(content)
            
            return ToolResult(
                success=True,
                output=f"Appended {len(content)} bytes to {path}",
                metadata={
                    "path": path,
                    "size": len(content),
                    "operation": "append"
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def delete(self, path: str) -> ToolResult:
        """Delete a file."""
        try:
            abs_path = os.path.abspath(path)
            
            if not os.path.exists(abs_path):
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"File not found: {path}"
                )
            
            if os.path.isdir(abs_path):
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Is a directory, use directory tool: {path}"
                )
            
            os.remove(abs_path)
            
            return ToolResult(
                success=True,
                output=f"Deleted file: {path}",
                metadata={"path": path, "operation": "delete"}
            )
        except PermissionError:
            return ToolResult(
                success=False,
                output=None,
                error=f"Permission denied: {path}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def copy(self, source: str, destination: str) -> ToolResult:
        """Copy a file."""
        try:
            src_path = os.path.abspath(source)
            dst_path = os.path.abspath(destination)
            
            if not os.path.exists(src_path):
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Source not found: {source}"
                )
            
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            shutil.copy2(src_path, dst_path)
            
            return ToolResult(
                success=True,
                output=f"Copied {source} to {destination}",
                metadata={
                    "source": source,
                    "destination": destination,
                    "operation": "copy"
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def move(self, source: str, destination: str) -> ToolResult:
        """Move a file."""
        try:
            src_path = os.path.abspath(source)
            dst_path = os.path.abspath(destination)
            
            if not os.path.exists(src_path):
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Source not found: {source}"
                )
            
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            shutil.move(src_path, dst_path)
            
            return ToolResult(
                success=True,
                output=f"Moved {source} to {destination}",
                metadata={
                    "source": source,
                    "destination": destination,
                    "operation": "move"
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute a file operation."""
        operations = {
            "read": self.read,
            "write": self.write,
            "append": self.append,
            "delete": self.delete,
            "copy": self.copy,
            "move": self.move
        }
        
        if operation not in operations:
            return ToolResult(
                success=False,
                output=None,
                error=f"Unknown operation: {operation}"
            )
        
        return operations[operation](**kwargs)


class DirectoryTool(BaseTool):
    """Tool for directory operations."""
    
    @property
    def name(self) -> str:
        return "directory"
    
    @property
    def description(self) -> str:
        return "List, create, and manage directories"
    
    def list(self, path: str = ".") -> ToolResult:
        """List directory contents."""
        try:
            abs_path = os.path.abspath(path)
            
            if not os.path.exists(abs_path):
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Directory not found: {path}"
                )
            
            if not os.path.isdir(abs_path):
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Not a directory: {path}"
                )
            
            items = []
            for item in os.listdir(abs_path):
                item_path = os.path.join(abs_path, item)
                try:
                    stat = os.stat(item_path)
                    items.append({
                        "name": item,
                        "type": "directory" if os.path.isdir(item_path) else "file",
                        "size": stat.st_size if os.path.isfile(item_path) else None,
                        "modified": stat.st_mtime
                    })
                except:
                    items.append({
                        "name": item,
                        "type": "unknown",
                        "size": None,
                        "modified": None
                    })
            
            return ToolResult(
                success=True,
                output=items,
                metadata={
                    "path": path,
                    "count": len(items),
                    "operation": "list"
                }
            )
        except PermissionError:
            return ToolResult(
                success=False,
                output=None,
                error=f"Permission denied: {path}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def create(self, path: str) -> ToolResult:
        """Create a directory."""
        try:
            abs_path = os.path.abspath(path)
            os.makedirs(abs_path, exist_ok=True)
            
            return ToolResult(
                success=True,
                output=f"Created directory: {path}",
                metadata={"path": path, "operation": "create"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def delete(self, path: str) -> ToolResult:
        """Delete a directory."""
        try:
            abs_path = os.path.abspath(path)
            
            if not os.path.exists(abs_path):
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Directory not found: {path}"
                )
            
            shutil.rmtree(abs_path)
            
            return ToolResult(
                success=True,
                output=f"Deleted directory: {path}",
                metadata={"path": path, "operation": "delete"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def search(self, pattern: str, path: str = ".") -> ToolResult:
        """Search for files matching a pattern."""
        try:
            abs_path = os.path.abspath(path)
            matches = []
            
            for root, dirs, files in os.walk(abs_path):
                for filename in files:
                    if pattern.lower() in filename.lower():
                        matches.append(os.path.join(root, filename))
            
            return ToolResult(
                success=True,
                output=matches[:100],  # Limit to 100 results
                metadata={
                    "pattern": pattern,
                    "path": path,
                    "count": len(matches),
                    "operation": "search"
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute a directory operation."""
        operations = {
            "list": self.list,
            "create": self.create,
            "delete": self.delete,
            "search": self.search
        }
        
        if operation not in operations:
            return ToolResult(
                success=False,
                output=None,
                error=f"Unknown operation: {operation}"
            )
        
        return operations[operation](**kwargs)