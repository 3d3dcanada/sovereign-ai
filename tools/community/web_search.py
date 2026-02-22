"""
OpenWebUI Tool: Web Search
Version: 2.0.0
Description: Search the web using Brave Search API.

This tool allows the AI to search the web and return results.
"""

from pydantic import BaseModel, Field
from typing import Optional
import os
import json
import urllib.request
import urllib.parse
import urllib.error


class Tools:
    class Valves(BaseModel):
        brave_api_key: str = Field(
            default="",
            description="Brave Search API key (or set BRAVE_API_KEY env var)"
        )
        result_count: int = Field(
            default=5,
            description="Number of search results to return"
        )
        include_snippets: bool = Field(
            default=True,
            description="Include text snippets from results"
        )
    
    def __init__(self):
        self.valves = self.Valves()
    
    def _get_api_key(self) -> str:
        """Get API key from valves or environment."""
        return self.valves.brave_api_key or os.environ.get("BRAVE_API_KEY", "")
    
    def search_web(
        self,
        query: str,
        count: Optional[int] = None
    ) -> str:
        """
        Search the web using Brave Search.
        
        Args:
            query: Search query
            count: Number of results (optional)
        
        Returns:
            Search results as formatted text
        """
        api_key = self._get_api_key()
        if not api_key:
            return "Error: No Brave API key configured. Set BRAVE_API_KEY environment variable or configure in valves."
        
        count = count or self.valves.result_count
        
        try:
            # Build request
            url = f"https://api.search.brave.com/res/v1/web/search"
            params = {
                "q": query,
                "count": count,
                "search_lang": "en"
            }
            
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": api_key
            }
            
            # Make request
            full_url = f"{url}?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(full_url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # Parse results
            results = []
            
            # Web results
            if "web" in data and "results" in data["web"]:
                for result in data["web"]["results"][:count]:
                    item = {
                        "title": result.get("title", "No title"),
                        "url": result.get("url", ""),
                        "description": result.get("description", "")
                    }
                    results.append(item)
            
            # Format output
            if not results:
                return f"No results found for: {query}"
            
            output = f"## Search Results for: {query}\n\n"
            for i, result in enumerate(results, 1):
                output += f"### {i}. {result['title']}\n"
                output += f"**URL:** {result['url']}\n"
                if self.valves.include_snippets and result['description']:
                    output += f"**Snippet:** {result['description']}\n"
                output += "\n"
            
            return output
            
        except urllib.error.HTTPError as e:
            return f"HTTP Error: {e.code} - {e.reason}"
        except urllib.error.URLError as e:
            return f"URL Error: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def search_news(
        self,
        query: str,
        count: Optional[int] = None
    ) -> str:
        """
        Search for news articles.
        
        Args:
            query: Search query
            count: Number of results (optional)
        
        Returns:
            News results as formatted text
        """
        api_key = self._get_api_key()
        if not api_key:
            return "Error: No Brave API key configured."
        
        count = count or self.valves.result_count
        
        try:
            url = "https://api.search.brave.com/res/v1/news/search"
            params = {
                "q": query,
                "count": count,
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
            if "results" in data:
                for result in data["results"][:count]:
                    item = {
                        "title": result.get("title", "No title"),
                        "url": result.get("url", ""),
                        "description": result.get("description", ""),
                        "age": result.get("age", "")
                    }
                    results.append(item)
            
            if not results:
                return f"No news found for: {query}"
            
            output = f"## News Results for: {query}\n\n"
            for i, result in enumerate(results, 1):
                output += f"### {i}. {result['title']}"
                if result['age']:
                    output += f" ({result['age']})"
                output += "\n"
                output += f"**URL:** {result['url']}\n"
                if result['description']:
                    output += f"**Summary:** {result['description']}\n"
                output += "\n"
            
            return output
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def fetch_url(
        self,
        url: str,
        max_length: int = 5000
    ) -> str:
        """
        Fetch content from a URL.
        
        Args:
            url: URL to fetch
            max_length: Maximum content length to return
        
        Returns:
            Page content as text
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read().decode('utf-8', errors='ignore')
            
            # Basic HTML stripping
            import re
            content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
            content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
            content = re.sub(r'<[^>]+>', ' ', content)
            content = re.sub(r'\s+', ' ', content)
            
            if len(content) > max_length:
                content = content[:max_length] + "\n... (content truncated)"
            
            return content.strip()
            
        except Exception as e:
            return f"Error fetching URL: {str(e)}"


if __name__ == "__main__":
    tools = Tools()
    print(json.dumps({
        "name": "web_search",
        "description": "Search the web using Brave Search API",
        "tools": [
            {
                "name": "search_web",
                "description": "Search the web",
                "parameters": {
                    "query": "string - Search query",
                    "count": "int - Optional number of results"
                }
            },
            {
                "name": "search_news",
                "description": "Search for news articles",
                "parameters": {
                    "query": "string - Search query",
                    "count": "int - Optional number of results"
                }
            },
            {
                "name": "fetch_url",
                "description": "Fetch content from a URL",
                "parameters": {
                    "url": "string - URL to fetch",
                    "max_length": "int - Maximum content length"
                }
            }
        ]
    }, indent=2))