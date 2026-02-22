"""
OpenWebUI Tool: Image Generation
Version: 2.0.0
Description: Generate images using various AI image generation APIs.

Supports: OpenAI DALL-E, Stability AI, and local models.
"""

from pydantic import BaseModel, Field
from typing import Optional
import os
import json
import base64
import urllib.request
import urllib.error


class Tools:
    class Valves(BaseModel):
        provider: str = Field(
            default="openai",
            description="Image provider: openai, stability, or local"
        )
        openai_api_key: str = Field(
            default="",
            description="OpenAI API key (or set OPENAI_API_KEY env var)"
        )
        stability_api_key: str = Field(
            default="",
            description="Stability AI API key (or set STABILITY_API_KEY env var)"
        )
        default_size: str = Field(
            default="1024x1024",
            description="Default image size"
        )
        default_style: str = Field(
            default="vivid",
            description="Default style for DALL-E: vivid or natural"
        )
        save_path: str = Field(
            default="/home/wess/sovereign-ai/data/images",
            description="Path to save generated images"
        )
    
    def __init__(self):
        self.valves = self.Valves()
    
    def _get_openai_key(self) -> str:
        return self.valves.openai_api_key or os.environ.get("OPENAI_API_KEY", "")
    
    def _get_stability_key(self) -> str:
        return self.valves.stability_api_key or os.environ.get("STABILITY_API_KEY", "")
    
    def generate_image(
        self,
        prompt: str,
        size: Optional[str] = None,
        style: Optional[str] = None,
        provider: Optional[str] = None
    ) -> str:
        """
        Generate an image from a text prompt.
        
        Args:
            prompt: Image description
            size: Image size (e.g., "1024x1024", "512x512")
            style: Style for DALL-E ("vivid" or "natural")
            provider: Provider to use ("openai", "stability")
        
        Returns:
            Path to generated image or URL
        """
        provider = provider or self.valves.provider
        size = size or self.valves.default_size
        style = style or self.valves.default_style
        
        if provider == "openai":
            return self._generate_openai(prompt, size, style)
        elif provider == "stability":
            return self._generate_stability(prompt, size)
        else:
            return f"Unknown provider: {provider}. Use 'openai' or 'stability'."
    
    def _generate_openai(self, prompt: str, size: str, style: str) -> str:
        """Generate image using OpenAI DALL-E."""
        api_key = self._get_openai_key()
        if not api_key:
            return "Error: No OpenAI API key configured."
        
        try:
            url = "https://api.openai.com/v1/images/generations"
            
            data = {
                "model": "dall-e-3",
                "prompt": prompt,
                "n": 1,
                "size": size,
                "style": style,
                "response_format": "url"
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
            
            if "data" in result and len(result["data"]) > 0:
                image_url = result["data"][0]["url"]
                revised_prompt = result["data"][0].get("revised_prompt", prompt)
                
                # Download and save image
                os.makedirs(self.valves.save_path, exist_ok=True)
                import time
                filename = f"dalle_{int(time.time())}.png"
                filepath = os.path.join(self.valves.save_path, filename)
                
                img_req = urllib.request.Request(image_url)
                with urllib.request.urlopen(img_req, timeout=30) as img_response:
                    with open(filepath, 'wb') as f:
                        f.write(img_response.read())
                
                return f"Image generated successfully!\n\n**Prompt:** {revised_prompt}\n**Saved to:** {filepath}\n**URL:** {image_url}"
            else:
                return f"Error: No image generated. Response: {result}"
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            return f"HTTP Error: {e.code}\n{error_body}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _generate_stability(self, prompt: str, size: str) -> str:
        """Generate image using Stability AI."""
        api_key = self._get_stability_key()
        if not api_key:
            return "Error: No Stability AI API key configured."
        
        try:
            # Parse size
            width, height = map(int, size.split('x'))
            
            url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
            
            data = {
                "text_prompts": [{"text": prompt}],
                "cfg_scale": 7,
                "height": height,
                "width": width,
                "samples": 1,
                "steps": 30
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json"
            }
            
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode('utf-8'))
            
            if "artifacts" in result and len(result["artifacts"]) > 0:
                # Save base64 image
                os.makedirs(self.valves.save_path, exist_ok=True)
                import time
                filename = f"stability_{int(time.time())}.png"
                filepath = os.path.join(self.valves.save_path, filename)
                
                image_data = base64.b64decode(result["artifacts"][0]["base64"])
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                
                return f"Image generated successfully!\n\n**Prompt:** {prompt}\n**Saved to:** {filepath}"
            else:
                return f"Error: No image generated. Response: {result}"
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            return f"HTTP Error: {e.code}\n{error_body}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def describe_image(
        self,
        image_path: str
    ) -> str:
        """
        Describe an image using vision models.
        
        Args:
            image_path: Path to the image file
        
        Returns:
            Description of the image
        """
        if not os.path.exists(image_path):
            return f"Error: Image not found at {image_path}"
        
        api_key = self._get_openai_key()
        if not api_key:
            return f"Image found at {image_path}. No OpenAI API key configured for vision model."
        
        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Determine MIME type
            ext = os.path.splitext(image_path)[1].lower()
            mime_types = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }
            mime_type = mime_types.get(ext, 'image/png')
            
            # Call OpenAI Vision API
            url = "https://api.openai.com/v1/chat/completions"
            
            data = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Describe this image in detail. Include the main subjects, colors, composition, mood, and any notable elements."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1000
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
            
            if "choices" in result and len(result["choices"]) > 0:
                description = result["choices"][0]["message"]["content"]
                return f"**Image Description:**\n\n{description}"
            else:
                return f"Error: No description generated. Response: {result}"
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            return f"HTTP Error: {e.code}\n{error_body}"
        except Exception as e:
            return f"Error describing image: {str(e)}"
    
    def list_generated_images(self) -> str:
        """
        List all generated images.
        
        Returns:
            List of generated image files
        """
        if not os.path.exists(self.valves.save_path):
            return "No images generated yet."
        
        images = []
        for f in os.listdir(self.valves.save_path):
            if f.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                filepath = os.path.join(self.valves.save_path, f)
                size = os.path.getsize(filepath)
                images.append(f"- {f} ({size / 1024:.1f} KB)")
        
        if not images:
            return "No images found."
        
        return "## Generated Images\n\n" + "\n".join(images)
    
    def analyze_image_url(self, url: str) -> str:
        """
        Analyze an image from a URL.
        
        Args:
            url: URL of the image to analyze
        
        Returns:
            Description of the image
        """
        api_key = self._get_openai_key()
        if not api_key:
            return "Error: No OpenAI API key configured for vision model."
        
        try:
            # Call OpenAI Vision API with URL
            api_url = "https://api.openai.com/v1/chat/completions"
            
            data = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Describe this image in detail. Include the main subjects, colors, composition, mood, and any notable elements."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": url
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1000
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            req = urllib.request.Request(
                api_url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
            
            if "choices" in result and len(result["choices"]) > 0:
                description = result["choices"][0]["message"]["content"]
                return f"**Image Description:**\n\n{description}"
            else:
                return f"Error: No description generated. Response: {result}"
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            return f"HTTP Error: {e.code}\n{error_body}"
        except Exception as e:
            return f"Error analyzing image: {str(e)}"


if __name__ == "__main__":
    tools = Tools()
    print(json.dumps({
        "name": "image_generation",
        "description": "Generate images using AI",
        "tools": [
            {
                "name": "generate_image",
                "description": "Generate an image from text",
                "parameters": {
                    "prompt": "string - Image description",
                    "size": "string - Optional size (e.g., 1024x1024)",
                    "style": "string - Optional style (vivid/natural)",
                    "provider": "string - Optional provider (openai/stability)"
                }
            },
            {
                "name": "describe_image",
                "description": "Describe an image using vision model",
                "parameters": {
                    "image_path": "string - Path to image"
                }
            },
            {
                "name": "analyze_image_url",
                "description": "Analyze an image from a URL",
                "parameters": {
                    "url": "string - URL of the image"
                }
            },
            {
                "name": "list_generated_images",
                "description": "List all generated images",
                "parameters": {}
            }
        ]
    }, indent=2))