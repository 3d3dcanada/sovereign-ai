"""
OpenWebUI Action: Quick Actions
Version: 2.0.0
Description: User-triggered actions for common tasks.

Actions available:
- Summarize conversation
- Export to markdown
- Execute code
- Search web
"""

from pydantic import BaseModel, Field
from typing import Optional, List
import json
import urllib.request
import urllib.parse
import os


class Action:
    class Valves(BaseModel):
        brave_api_key: str = Field(
            default="",
            description="Brave Search API key"
        )
        enable_web_search: bool = Field(default=True)
        enable_code_exec: bool = Field(default=True)
    
    def __init__(self):
        self.valves = self.Valves()
    
    def actions(self) -> list:
        """Return available actions."""
        actions_list = [
            {
                "id": "summarize",
                "name": "📝 Summarize",
                "description": "Summarize the conversation",
                "icon": "📝",
                "type": "default"
            },
            {
                "id": "export_markdown",
                "name": "📄 Export Markdown",
                "description": "Export conversation to markdown",
                "icon": "📄",
                "type": "default"
            }
        ]
        
        if self.valves.enable_web_search:
            actions_list.append({
                "id": "web_search",
                "name": "🔍 Web Search",
                "description": "Search the web for information",
                "icon": "🔍",
                "type": "default"
            })
        
        if self.valves.enable_code_exec:
            actions_list.append({
                "id": "execute_code",
                "name": "▶️ Execute Code",
                "description": "Execute code block",
                "icon": "▶️",
                "type": "default"
            })
        
        return actions_list
    
    def action(self, action_id: str, messages: list, **kwargs) -> dict:
        """Execute an action."""
        
        if action_id == "summarize":
            return self._summarize(messages)
        
        elif action_id == "export_markdown":
            return self._export_markdown(messages)
        
        elif action_id == "web_search":
            query = kwargs.get("query", "")
            return self._web_search(query)
        
        elif action_id == "execute_code":
            code = kwargs.get("code", "")
            return self._execute_code(code)
        
        return {
            "status": "error",
            "message": f"Unknown action: {action_id}"
        }
    
    def _summarize(self, messages: list) -> dict:
        """Generate a summary of the conversation."""
        if not messages:
            return {
                "status": "error",
                "message": "No messages to summarize"
            }
        
        # Extract text content
        content_parts = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if content:
                content_parts.append(f"**{role.title()}**: {content[:500]}")
        
        summary_prompt = (
            "Please provide a concise summary of the following conversation:\n\n"
            + "\n\n".join(content_parts[-10:])  # Last 10 messages
        )
        
        return {
            "status": "success",
            "action": "summarize",
            "message": "Summary request generated. The AI will summarize the conversation.",
            "data": {
                "prompt": summary_prompt
            }
        }
    
    def _export_markdown(self, messages: list) -> dict:
        """Export conversation to markdown format."""
        if not messages:
            return {
                "status": "error",
                "message": "No messages to export"
            }
        
        markdown_lines = [
            "# Conversation Export",
            f"*Exported from Sovereign AI*",
            "",
            "---",
            ""
        ]
        
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if role == "user":
                markdown_lines.append(f"## 👤 User")
            elif role == "assistant":
                markdown_lines.append(f"## 🤖 Assistant")
            else:
                markdown_lines.append(f"## 📋 {role.title()}")
            
            markdown_lines.append("")
            markdown_lines.append(content)
            markdown_lines.append("")
            markdown_lines.append("---")
            markdown_lines.append("")
        
        markdown_content = "\n".join(markdown_lines)
        
        return {
            "status": "success",
            "action": "export_markdown",
            "message": "Conversation exported to markdown",
            "data": {
                "content": markdown_content,
                "filename": "conversation.md"
            }
        }
    
    def _web_search(self, query: str) -> dict:
        """Search the web using Brave Search."""
        if not query:
            return {
                "status": "error",
                "message": "No search query provided"
            }
        
        api_key = self.valves.brave_api_key or os.environ.get("BRAVE_API_KEY", "")
        
        if not api_key:
            return {
                "status": "error",
                "message": "No Brave API key configured. Set BRAVE_API_KEY environment variable."
            }
        
        try:
            url = f"https://api.search.brave.com/res/v1/web/search"
            params = {
                "q": query,
                "count": 5,
                "search_lang": "en"
            }
            
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": api_key
            }
            
            full_url = f"{url}?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(full_url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            results = []
            if "web" in data and "results" in data["web"]:
                for result in data["web"]["results"][:5]:
                    results.append({
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "description": result.get("description", "")
                    })
            
            return {
                "status": "success",
                "action": "web_search",
                "message": f"Found {len(results)} results for: {query}",
                "data": {
                    "query": query,
                    "results": results
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Search failed: {str(e)}"
            }
    
    def _execute_code(self, code: str) -> dict:
        """Execute Python code safely."""
        if not code:
            return {
                "status": "error",
                "message": "No code provided"
            }
        
        import subprocess
        import tempfile
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False
            ) as f:
                f.write(code)
                temp_file = f.name
            
            # Execute with timeout
            result = subprocess.run(
                ['python3', temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Clean up
            os.unlink(temp_file)
            
            if result.returncode == 0:
                return {
                    "status": "success",
                    "action": "execute_code",
                    "message": "Code executed successfully",
                    "data": {
                        "output": result.stdout,
                        "return_code": result.returncode
                    }
                }
            else:
                return {
                    "status": "error",
                    "message": f"Code execution failed",
                    "data": {
                        "error": result.stderr,
                        "return_code": result.returncode
                    }
                }
                
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": "Code execution timed out (30s limit)"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Execution failed: {str(e)}"
            }