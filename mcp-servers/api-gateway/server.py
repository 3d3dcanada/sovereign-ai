#!/usr/bin/env python3
"""
API Gateway MCP Server
Version: 2.0.0 - February 2026

A unified API gateway that provides access to multiple AI providers
through a single MCP interface. Routes requests to the appropriate
provider based on task type and availability.

Supported Providers:
- NVIDIA NIM (free tier)
- Groq (fast inference)
- OpenAI (GPT-4o, DALL-E)
- Anthropic (Claude)
- Google AI (Gemini)
- Mistral (Codestral)
- OpenRouter (aggregator)
"""

import asyncio
import json
import os
import logging
from typing import Any, Optional, Dict, List
from dataclasses import dataclass
from enum import Enum
import urllib.request
import urllib.error

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api-gateway")

# Create server
server = Server("api-gateway")


class Provider(Enum):
    NVIDIA = "nvidia"
    GROQ = "groq"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    MISTRAL = "mistral"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"


@dataclass
class ProviderConfig:
    name: str
    base_url: str
    api_key_env: str
    models: List[str]
    capabilities: List[str]
    rate_limit: int  # requests per minute


PROVIDER_CONFIGS = {
    Provider.NVIDIA: ProviderConfig(
        name="NVIDIA NIM",
        base_url="https://integrate.api.nvidia.com/v1",
        api_key_env="NVIDIA_API_KEY",
        models=["deepseek-ai/deepseek-r1", "deepseek-ai/deepseek-v3", "meta/llama-3.3-70b"],
        capabilities=["chat", "reasoning", "code"],
        rate_limit=60
    ),
    Provider.GROQ: ProviderConfig(
        name="Groq",
        base_url="https://api.groq.com/openai/v1",
        api_key_env="GROQ_API_KEY",
        models=["llama-3.3-70b-versatile", "deepseek-r1-distill-llama-70b"],
        capabilities=["chat", "code", "fast"],
        rate_limit=30
    ),
    Provider.OPENAI: ProviderConfig(
        name="OpenAI",
        base_url="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        models=["gpt-4o", "gpt-4o-mini", "o1", "dall-e-3"],
        capabilities=["chat", "code", "vision", "image"],
        rate_limit=60
    ),
    Provider.ANTHROPIC: ProviderConfig(
        name="Anthropic",
        base_url="https://api.anthropic.com/v1",
        api_key_env="ANTHROPIC_API_KEY",
        models=["claude-sonnet-4-20250514", "claude-opus-4-20250514"],
        capabilities=["chat", "code", "vision", "reasoning"],
        rate_limit=60
    ),
    Provider.GOOGLE: ProviderConfig(
        name="Google AI",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        api_key_env="GOOGLE_API_KEY",
        models=["gemini-2.5-flash", "gemini-2.5-pro"],
        capabilities=["chat", "code", "vision", "long-context"],
        rate_limit=60
    ),
    Provider.MISTRAL: ProviderConfig(
        name="Mistral",
        base_url="https://api.mistral.ai/v1",
        api_key_env="MISTRAL_API_KEY",
        models=["mistral-large-latest", "codestral-latest"],
        capabilities=["chat", "code"],
        rate_limit=30
    ),
    Provider.OPENROUTER: ProviderConfig(
        name="OpenRouter",
        base_url="https://openrouter.ai/api/v1",
        api_key_env="OPENROUTER_API_KEY",
        models=["openrouter/auto"],
        capabilities=["chat", "code", "all-models"],
        rate_limit=60
    ),
    Provider.OLLAMA: ProviderConfig(
        name="Ollama (Local)",
        base_url="http://localhost:11434",
        api_key_env="",
        models=["deepseek-r1:8b", "qwen3:8b", "nomic-embed-text:v1.5"],
        capabilities=["chat", "code", "embedding", "local"],
        rate_limit=1000
    ),
}


def get_api_key(provider: Provider) -> Optional[str]:
    """Get API key for a provider."""
    config = PROVIDER_CONFIGS.get(provider)
    if not config or not config.api_key_env:
        return None
    return os.environ.get(config.api_key_env, "")


def is_provider_available(provider: Provider) -> bool:
    """Check if a provider has API key configured."""
    if provider == Provider.OLLAMA:
        return True  # Local, always available
    return bool(get_api_key(provider))


def get_available_providers() -> List[Dict]:
    """Get list of available providers with their models."""
    available = []
    for provider, config in PROVIDER_CONFIGS.items():
        if is_provider_available(provider):
            available.append({
                "provider": provider.value,
                "name": config.name,
                "models": config.models,
                "capabilities": config.capabilities
            })
    return available


def recommend_provider(task_type: str) -> Optional[Provider]:
    """Recommend best provider for a task type."""
    recommendations = {
        "reasoning": [Provider.NVIDIA, Provider.ANTHROPIC, Provider.OLLAMA],
        "code": [Provider.GROQ, Provider.MISTRAL, Provider.OPENAI],
        "fast": [Provider.GROQ, Provider.OLLAMA],
        "vision": [Provider.OPENAI, Provider.GOOGLE, Provider.ANTHROPIC],
        "long-context": [Provider.GOOGLE, Provider.ANTHROPIC],
        "image": [Provider.OPENAI],
        "local": [Provider.OLLAMA],
        "chat": [Provider.OLLAMA, Provider.GROQ, Provider.NVIDIA],
    }
    
    for provider in recommendations.get(task_type, [Provider.OLLAMA]):
        if is_provider_available(provider):
            return provider
    
    return Provider.OLLAMA  # Fallback to local


async def call_openai_compatible(
    provider: Provider,
    model: str,
    messages: List[Dict],
    temperature: float = 0.7,
    max_tokens: int = 4096
) -> Dict:
    """Call an OpenAI-compatible API."""
    config = PROVIDER_CONFIGS.get(provider)
    if not config:
        return {"error": f"Unknown provider: {provider}"}
    
    api_key = get_api_key(provider)
    
    url = f"{config.base_url}/chat/completions"
    
    data = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    headers = {
        "Content-Type": "application/json",
    }
    
    if api_key:
        if provider == Provider.ANTHROPIC:
            headers["x-api-key"] = api_key
            headers["anthropic-version"] = "2023-06-01"
            # Anthropic has different format
            data = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens
            }
            url = f"{config.base_url}/messages"
        else:
            headers["Authorization"] = f"Bearer {api_key}"
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode('utf-8'))
        
        return {
            "success": True,
            "provider": provider.value,
            "model": model,
            "response": result
        }
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        return {
            "success": False,
            "error": f"HTTP {e.code}: {error_body}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available API gateway tools."""
    return [
        Tool(
            name="list_providers",
            description="List all available AI providers and their models",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="recommend_provider",
            description="Get recommended provider for a specific task type",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_type": {
                        "type": "string",
                        "description": "Task type: reasoning, code, fast, vision, long-context, image, local, chat"
                    }
                },
                "required": ["task_type"]
            }
        ),
        Tool(
            name="chat",
            description="Send a chat message to an AI provider",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The message to send"
                    },
                    "provider": {
                        "type": "string",
                        "description": "Provider to use (nvidia, groq, openai, anthropic, google, mistral, openrouter, ollama)"
                    },
                    "model": {
                        "type": "string",
                        "description": "Model to use (optional, will use default for provider)"
                    },
                    "system_prompt": {
                        "type": "string",
                        "description": "System prompt (optional)"
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Temperature (0-2, default 0.7)"
                    }
                },
                "required": ["message"]
            }
        ),
        Tool(
            name="chat_with_history",
            description="Send a conversation with message history",
            inputSchema={
                "type": "object",
                "properties": {
                    "messages": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {"type": "string"},
                                "content": {"type": "string"}
                            }
                        },
                        "description": "Message history"
                    },
                    "provider": {
                        "type": "string",
                        "description": "Provider to use"
                    },
                    "model": {
                        "type": "string",
                        "description": "Model to use"
                    }
                },
                "required": ["messages"]
            }
        ),
        Tool(
            name="compare_providers",
            description="Send the same message to multiple providers and compare responses",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The message to send"
                    },
                    "providers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of providers to compare"
                    }
                },
                "required": ["message"]
            }
        ),
        Tool(
            name="get_provider_status",
            description="Check if a specific provider is configured and available",
            inputSchema={
                "type": "object",
                "properties": {
                    "provider": {
                        "type": "string",
                        "description": "Provider to check"
                    }
                },
                "required": ["provider"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    
    if name == "list_providers":
        providers = get_available_providers()
        return [TextContent(
            type="text",
            text=json.dumps({
                "available_providers": providers,
                "count": len(providers)
            }, indent=2)
        )]
    
    elif name == "recommend_provider":
        task_type = arguments.get("task_type", "chat")
        provider = recommend_provider(task_type)
        config = PROVIDER_CONFIGS.get(provider) if provider else None
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "task_type": task_type,
                "recommended_provider": provider.value if provider else None,
                "provider_name": config.name if config else None,
                "recommended_model": config.models[0] if config and config.models else None,
                "reason": f"Best available provider for {task_type} tasks"
            }, indent=2)
        )]
    
    elif name == "chat":
        message = arguments.get("message", "")
        provider_name = arguments.get("provider", "")
        model = arguments.get("model")
        system_prompt = arguments.get("system_prompt")
        temperature = arguments.get("temperature", 0.7)
        
        # Determine provider
        if provider_name:
            try:
                provider = Provider(provider_name.lower())
            except ValueError:
                return [TextContent(type="text", text=json.dumps({
                    "error": f"Unknown provider: {provider_name}",
                    "available": [p.value for p in Provider]
                }))]
        else:
            provider = recommend_provider("chat")
        
        config = PROVIDER_CONFIGS.get(provider)
        if not config:
            return [TextContent(type="text", text=json.dumps({"error": "Provider not found"}))]
        
        # Check availability
        if not is_provider_available(provider):
            return [TextContent(type="text", text=json.dumps({
                "error": f"Provider {provider.value} is not configured",
                "hint": f"Set {config.api_key_env} environment variable"
            }))]
        
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})
        
        # Use default model if not specified
        if not model:
            model = config.models[0]
        
        result = await call_openai_compatible(
            provider, model, messages, temperature
        )
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "chat_with_history":
        messages = arguments.get("messages", [])
        provider_name = arguments.get("provider", "")
        model = arguments.get("model")
        
        if not messages:
            return [TextContent(type="text", text=json.dumps({"error": "No messages provided"}))]
        
        # Determine provider
        if provider_name:
            try:
                provider = Provider(provider_name.lower())
            except ValueError:
                provider = recommend_provider("chat")
        else:
            provider = recommend_provider("chat")
        
        config = PROVIDER_CONFIGS.get(provider)
        if not model and config:
            model = config.models[0]
        
        result = await call_openai_compatible(provider, model, messages)
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "compare_providers":
        message = arguments.get("message", "")
        provider_names = arguments.get("providers", [])
        
        if not provider_names:
            # Use all available providers
            provider_names = [p.value for p in Provider if is_provider_available(p)]
        
        results = {}
        for provider_name in provider_names:
            try:
                provider = Provider(provider_name.lower())
                if not is_provider_available(provider):
                    results[provider_name] = {"status": "not_configured"}
                    continue
                
                config = PROVIDER_CONFIGS.get(provider)
                result = await call_openai_compatible(
                    provider, config.models[0], [{"role": "user", "content": message}]
                )
                results[provider_name] = result
            except ValueError:
                results[provider_name] = {"error": "Unknown provider"}
        
        return [TextContent(type="text", text=json.dumps(results, indent=2))]
    
    elif name == "get_provider_status":
        provider_name = arguments.get("provider", "")
        
        try:
            provider = Provider(provider_name.lower())
            config = PROVIDER_CONFIGS.get(provider)
            available = is_provider_available(provider)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "provider": provider.value,
                    "name": config.name if config else None,
                    "available": available,
                    "models": config.models if config else [],
                    "capabilities": config.capabilities if config else [],
                    "api_key_configured": bool(get_api_key(provider)) if provider != Provider.OLLAMA else "N/A (local)"
                }, indent=2)
            )]
        except ValueError:
            return [TextContent(type="text", text=json.dumps({
                "error": f"Unknown provider: {provider_name}",
                "available_providers": [p.value for p in Provider]
            }))]
    
    return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


async def main():
    """Run the API gateway server."""
    logger.info("Starting API Gateway MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())