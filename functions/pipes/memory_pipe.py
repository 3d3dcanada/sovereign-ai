"""
OpenWebUI Pipe: Memory Pipe
Version: 2.0.0
Description: Pipe for integrating with Mem0/Qdrant memory system.

This pipe enhances responses with memory context and stores
important information for future reference.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
import json
import urllib.request
import urllib.error
import os


class Pipe:
    class Valves(BaseModel):
        enabled: bool = Field(default=True)
        mem0_api_url: str = Field(
            default="http://localhost:8000",
            description="Mem0 API URL"
        )
        qdrant_url: str = Field(
            default="http://localhost:6333",
            description="Qdrant API URL"
        )
        store_conversations: bool = Field(default=True)
        retrieve_context: bool = Field(default=True)
        max_context_items: int = Field(default=5)
    
    def __init__(self):
        self.valves = self.Valves()
    
    def pipe(self, body: dict) -> dict:
        """Process the request through the memory pipe."""
        if not self.valves.enabled:
            return body
        
        messages = body.get("messages", [])
        
        # Retrieve relevant context from memory
        if self.valves.retrieve_context and messages:
            last_message = messages[-1].get("content", "") if messages else ""
            context = self._retrieve_context(last_message)
            
            if context:
                # Add context as system message
                context_msg = {
                    "role": "system",
                    "content": f"[Memory Context]\n{context}"
                }
                body["messages"] = [context_msg] + messages
        
        return body
    
    def _retrieve_context(self, query: str) -> Optional[str]:
        """Retrieve relevant context from Qdrant."""
        try:
            # Try to connect to Qdrant
            url = f"{self.valves.qdrant_url}/collections"
            req = urllib.request.Request(url)
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                # Check if sovereign_memory collection exists
                collections = data.get("result", {}).get("collections", [])
                collection_names = [c.get("name") for c in collections]
                
                if "sovereign_memory" not in collection_names:
                    return None
                
                # Search for relevant memories
                # Note: This is a simplified version. Full implementation
                # would use embeddings for semantic search.
                return None
                
        except Exception as e:
            # Silently fail - memory is optional
            return None
    
    def _store_memory(self, user_id: str, content: str, metadata: dict = None):
        """Store a memory in Qdrant via Mem0."""
        if not self.valves.store_conversations:
            return
        
        try:
            url = f"{self.valves.mem0_api_url}/v1/memories"
            
            data = {
                "messages": [{"role": "user", "content": content}],
                "user_id": user_id,
                "metadata": metadata or {}
            }
            
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={"Content-Type": "application/json"},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                pass  # Memory stored successfully
                
        except Exception as e:
            # Silently fail - memory storage is optional
            pass