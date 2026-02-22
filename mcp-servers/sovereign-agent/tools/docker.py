"""
Docker Tool Module
Version: 2.0.0 - February 2026

Provides Docker container management operations.
"""

import json
import subprocess
from typing import Dict, List, Optional
from .base import BaseTool, ToolResult


class DockerTool(BaseTool):
    """Tool for Docker operations."""
    
    @property
    def name(self) -> str:
        return "docker"
    
    @property
    def description(self) -> str:
        return "Manage Docker containers and images"
    
    def _run_docker(self, args: List[str], timeout: int = 60) -> tuple:
        """Run a docker command."""
        try:
            result = subprocess.run(
                ["docker"] + args,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except FileNotFoundError:
            return -1, "", "Docker not found"
        except Exception as e:
            return -1, "", str(e)
    
    def ps(self, all: bool = False) -> ToolResult:
        """List containers."""
        args = ["ps", "--format", "json"]
        if all:
            args.append("-a")
        
        returncode, stdout, stderr = self._run_docker(args)
        
        if returncode != 0:
            return ToolResult(
                success=False,
                output=None,
                error=stderr or "Failed to list containers"
            )
        
        containers = []
        for line in stdout.strip().split('\n'):
            if line:
                try:
                    container = json.loads(line)
                    containers.append({
                        "id": container.get("ID", "")[:12],
                        "name": container.get("Names", ""),
                        "image": container.get("Image", ""),
                        "status": container.get("Status", ""),
                        "state": container.get("State", ""),
                        "ports": container.get("Ports", "")
                    })
                except:
                    pass
        
        return ToolResult(
            success=True,
            output=containers,
            metadata={
                "count": len(containers),
                "operation": "ps"
            }
        )
    
    def images(self) -> ToolResult:
        """List images."""
        returncode, stdout, stderr = self._run_docker(
            ["images", "--format", "json"]
        )
        
        if returncode != 0:
            return ToolResult(
                success=False,
                output=None,
                error=stderr or "Failed to list images"
            )
        
        images = []
        for line in stdout.strip().split('\n'):
            if line:
                try:
                    img = json.loads(line)
                    images.append({
                        "id": img.get("ID", ""),
                        "repository": img.get("Repository", ""),
                        "tag": img.get("Tag", ""),
                        "size": img.get("Size", ""),
                        "created": img.get("CreatedAt", "")
                    })
                except:
                    pass
        
        return ToolResult(
            success=True,
            output=images,
            metadata={
                "count": len(images),
                "operation": "images"
            }
        )
    
    def logs(self, container: str, lines: int = 50) -> ToolResult:
        """Get container logs."""
        returncode, stdout, stderr = self._run_docker(
            ["logs", container, "--tail", str(lines)]
        )
        
        if returncode != 0:
            return ToolResult(
                success=False,
                output=None,
                error=stderr or f"Failed to get logs for {container}"
            )
        
        output = stdout + stderr
        return ToolResult(
            success=True,
            output=output[-10000:],  # Limit output
            metadata={
                "container": container,
                "lines": lines,
                "operation": "logs"
            }
        )
    
    def inspect(self, container: str) -> ToolResult:
        """Inspect a container."""
        returncode, stdout, stderr = self._run_docker(
            ["inspect", container]
        )
        
        if returncode != 0:
            return ToolResult(
                success=False,
                output=None,
                error=stderr or f"Failed to inspect {container}"
            )
        
        try:
            data = json.loads(stdout)
            return ToolResult(
                success=True,
                output=data,
                metadata={
                    "container": container,
                    "operation": "inspect"
                }
            )
        except:
            return ToolResult(
                success=True,
                output=stdout,
                metadata={
                    "container": container,
                    "operation": "inspect"
                }
            )
    
    def start(self, container: str) -> ToolResult:
        """Start a container."""
        returncode, stdout, stderr = self._run_docker(["start", container])
        
        if returncode != 0:
            return ToolResult(
                success=False,
                output=None,
                error=stderr or f"Failed to start {container}"
            )
        
        return ToolResult(
            success=True,
            output=f"Started container: {container}",
            metadata={"container": container, "operation": "start"}
        )
    
    def stop(self, container: str, timeout: int = 10) -> ToolResult:
        """Stop a container."""
        returncode, stdout, stderr = self._run_docker(
            ["stop", "-t", str(timeout), container]
        )
        
        if returncode != 0:
            return ToolResult(
                success=False,
                output=None,
                error=stderr or f"Failed to stop {container}"
            )
        
        return ToolResult(
            success=True,
            output=f"Stopped container: {container}",
            metadata={"container": container, "operation": "stop"}
        )
    
    def restart(self, container: str) -> ToolResult:
        """Restart a container."""
        returncode, stdout, stderr = self._run_docker(["restart", container])
        
        if returncode != 0:
            return ToolResult(
                success=False,
                output=None,
                error=stderr or f"Failed to restart {container}"
            )
        
        return ToolResult(
            success=True,
            output=f"Restarted container: {container}",
            metadata={"container": container, "operation": "restart"}
        )
    
    def exec(self, container: str, command: str) -> ToolResult:
        """Execute a command in a container."""
        returncode, stdout, stderr = self._run_docker(
            ["exec", container, "sh", "-c", command],
            timeout=120
        )
        
        if returncode != 0:
            return ToolResult(
                success=False,
                output=stdout,
                error=stderr or f"Command failed in {container}"
            )
        
        return ToolResult(
            success=True,
            output=stdout,
            metadata={
                "container": container,
                "command": command,
                "operation": "exec"
            }
        )
    
    def stats(self, container: str = None) -> ToolResult:
        """Get container stats."""
        args = ["stats", "--no-stream", "--format", "json"]
        if container:
            args.append(container)
        
        returncode, stdout, stderr = self._run_docker(args)
        
        if returncode != 0:
            return ToolResult(
                success=False,
                output=None,
                error=stderr or "Failed to get stats"
            )
        
        stats = []
        for line in stdout.strip().split('\n'):
            if line:
                try:
                    stat = json.loads(line)
                    stats.append({
                        "container": stat.get("Container", ""),
                        "name": stat.get("Name", ""),
                        "cpu_percent": stat.get("CPUPerc", ""),
                        "memory_usage": stat.get("MemUsage", ""),
                        "memory_percent": stat.get("MemPerc", ""),
                        "network_io": stat.get("NetIO", ""),
                        "block_io": stat.get("BlockIO", "")
                    })
                except:
                    pass
        
        return ToolResult(
            success=True,
            output=stats,
            metadata={
                "count": len(stats),
                "operation": "stats"
            }
        )
    
    def compose_ps(self) -> ToolResult:
        """List docker compose services."""
        returncode, stdout, stderr = self._run_docker(
            ["compose", "ps", "--format", "json"]
        )
        
        if returncode != 0:
            return ToolResult(
                success=False,
                output=None,
                error=stderr or "Failed to list compose services"
            )
        
        services = []
        try:
            data = json.loads(stdout)
            if isinstance(data, list):
                services = data
            else:
                services = [data]
        except:
            pass
        
        return ToolResult(
            success=True,
            output=services,
            metadata={
                "count": len(services),
                "operation": "compose_ps"
            }
        )
    
    def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute a Docker operation."""
        operations = {
            "ps": self.ps,
            "images": self.images,
            "logs": self.logs,
            "inspect": self.inspect,
            "start": self.start,
            "stop": self.stop,
            "restart": self.restart,
            "exec": self.exec,
            "stats": self.stats,
            "compose_ps": self.compose_ps
        }
        
        if operation not in operations:
            return ToolResult(
                success=False,
                output=None,
                error=f"Unknown operation: {operation}"
            )
        
        return operations[operation](**kwargs)