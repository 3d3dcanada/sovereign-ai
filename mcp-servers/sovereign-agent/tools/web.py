"""
Web Tool Module
Version: 2.0.0 - February 2026

Provides web search and HTTP request capabilities.
"""

import json
import os
import urllib.request
import urllib.parse
import urllib.error
import re
from typing import Optional, Dict, List
from .base import BaseTool, ToolResult


class WebTool(BaseTool):
    """Tool for web operations."""
    
    @property
    def name(self) -> str:
        return "web"
    
    @property
    def description(self) -> str:
        return "Search the web and fetch URLs"
    
    def __init__(self, work_dir: Optional[str] = None, log_dir: str = None,
                 brave_api_key: str = None):
        super().__init__(work_dir, log_dir)
        self.brave_api_key = brave_api_key or os.environ.get("BRAVE_API_KEY", "")
    
    def search(self, query: str, count: int = 5) -> ToolResult:
        """Search the web using Brave Search."""
        if not self.brave_api_key:
            return ToolResult(
                success=False,
                output=None,
                error="No Brave API key configured. Set BRAVE_API_KEY environment variable."
            )
        
        try:
            url = "https://api.search.brave.com/res/v1/web/search"
            params = {
                "q": query,
                "count": count,
                "search_lang": "en"
            }
            
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": self.brave_api_key
            }
            
            full_url = f"{url}?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(full_url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            results = []
            if "web" in data and "results" in data["web"]:
                for result in data["web"]["results"][:count]:
                    results.append({
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "description": result.get("description", "")
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
        except urllib.error.HTTPError as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"HTTP Error: {e.code} - {e.reason}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def fetch(self, url: str, max_length: int = 10000) -> ToolResult:
        """Fetch content from a URL."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read().decode('utf-8', errors='ignore')
            
            # Basic HTML stripping
            content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
            content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
            content = re.sub(r'<[^>]+>', ' ', content)
            content = re.sub(r'\s+', ' ', content)
            
            if len(content) > max_length:
                content = content[:max_length] + "\n... (content truncated)"
            
            return ToolResult(
                success=True,
                output=content.strip(),
                metadata={
                    "url": url,
                    "size": len(content),
                    "operation": "fetch"
                }
            )
        except urllib.error.HTTPError as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"HTTP Error: {e.code} - {e.reason}"
            )
        except urllib.error.URLError as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"URL Error: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def post(self, url: str, data: Dict, headers: Dict = None) -> ToolResult:
        """Make a POST request."""
        try:
            req_headers = headers or {"Content-Type": "application/json"}
            req_data = json.dumps(data).encode('utf-8')
            
            req = urllib.request.Request(
                url,
                data=req_data,
                headers=req_headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                result = response.read().decode('utf-8')
            
            return ToolResult(
                success=True,
                output=result,
                metadata={
                    "url": url,
                    "method": "POST",
                    "operation": "post"
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute a web operation."""
        operations = {
            "search": self.search,
            "fetch": self.fetch,
            "post": self.post
        }
        
        if operation not in operations:
            return ToolResult(
                success=False,
                output=None,
                error=f"Unknown operation: {operation}"
            )
        
        return operations[operation](**kwargs)
