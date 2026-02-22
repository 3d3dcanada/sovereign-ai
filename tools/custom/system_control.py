"""
OpenWebUI Tool: System Control
Version: 2.0.0
Description: Control system operations with safety checks.
"""

from pydantic import BaseModel, Field
from typing import Optional
import subprocess
import os
import json
import shutil


class Tools:
    class Valves(BaseModel):
        allow_dangerous_commands: bool = Field(default=False)
        require_confirmation: bool = Field(default=True)
        log_commands: bool = Field(default=True)
        log_path: str = Field(default="/home/wess/sovereign-ai/logs/audit/system-commands.jsonl")
    
    def __init__(self):
        self.valves = self.Valves()
    
    def system_info(self) -> str:
        """Get system information."""
        info = {}
        try:
            info["hostname"] = os.uname().nodename
            with open("/proc/cpuinfo", "r") as f:
                cpuinfo = f.read()
            info["cpu_cores"] = len([l for l in cpuinfo.split("\n") if "processor" in l])
            with open("/proc/meminfo", "r") as f:
                meminfo = f.read()
            for line in meminfo.split("\n"):
                if "MemTotal" in line:
                    info["memory_total_gb"] = round(int(line.split()[1]) / 1024 / 1024, 2)
                if "MemAvailable" in line:
                    info["memory_available_gb"] = round(int(line.split()[1]) / 1024 / 1024, 2)
            total, used, free = shutil.disk_usage("/")
            info["disk_total_gb"] = round(total / 1024**3, 2)
            info["disk_used_gb"] = round(used / 1024**3, 2)
        except Exception as e:
            return f"Error getting system info: {e}"
        return json.dumps(info, indent=2)
    
    def list_processes(self, filter_name: Optional[str] = None) -> str:
        """List running processes."""
        try:
            cmd = "ps aux --sort=-%mem | head -20"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.stdout
        except Exception as e:
            return f"Error: {e}"
    
    def docker_status(self) -> str:
        """Get Docker container status."""
        try:
            result = subprocess.run("docker ps -a", shell=True, capture_output=True, text=True)
            return result.stdout or result.stderr
        except Exception as e:
            return f"Error: {e}"
    
    def docker_logs(self, container: str, lines: int = 50) -> str:
        """Get Docker container logs."""
        try:
            result = subprocess.run(f"docker logs {container} --tail {lines}", shell=True, capture_output=True, text=True)
            return result.stdout[-5000:] if len(result.stdout) > 5000 else result.stdout
        except Exception as e:
            return f"Error: {e}"
    
    def check_gpu(self) -> str:
        """Check GPU status."""
        try:
            result = subprocess.run("nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free,temperature.gpu --format=csv", shell=True, capture_output=True, text=True)
            return result.stdout or "nvidia-smi not available"
        except Exception as e:
            return f"Error: {e}"
    
    def ollama_status(self) -> str:
        """Check Ollama status and loaded models."""
        try:
            result = subprocess.run("curl -s http://localhost:11434/api/tags", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return json.dumps(json.loads(result.stdout), indent=2)
            return "Ollama not responding"
        except Exception as e:
            return f"Error: {e}"