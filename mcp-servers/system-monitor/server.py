#!/usr/bin/env python3
"""
System Monitor MCP Server
Version: 2.0.0 - February 2026

A comprehensive system monitoring MCP server that provides:
- CPU, memory, disk, and network metrics
- GPU monitoring (NVIDIA)
- Docker container status
- Process monitoring
- Service health checks
- Alert thresholds
"""

import asyncio
import json
import os
import logging
import subprocess
import shutil
from typing import Any, Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime
import urllib.request

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("system-monitor")

# Create server
server = Server("system-monitor")


@dataclass
class AlertThreshold:
    metric: str
    warning: float
    critical: float
    unit: str


DEFAULT_THRESHOLDS = [
    AlertThreshold("cpu_percent", 70, 90, "%"),
    AlertThreshold("memory_percent", 80, 95, "%"),
    AlertThreshold("disk_percent", 85, 95, "%"),
    AlertThreshold("gpu_memory_percent", 80, 95, "%"),
    AlertThreshold("gpu_temp", 80, 90, "°C"),
]


def get_cpu_info() -> Dict:
    """Get CPU information and usage."""
    try:
        # Get CPU count
        cpu_count = os.cpu_count() or 1
        
        # Get load average
        load1, load5, load15 = os.getloadavg()
        
        # Get CPU usage (Linux)
        try:
            with open('/proc/stat', 'r') as f:
                line = f.readline()
                values = line.split()[1:8]
                total = sum(int(v) for v in values)
                idle = int(values[3])
                
            # Read again after a moment for accurate calculation
            import time
            time.sleep(0.1)
            
            with open('/proc/stat', 'r') as f:
                line = f.readline()
                values2 = line.split()[1:8]
                total2 = sum(int(v) for v in values2)
                idle2 = int(values2[3])
            
            cpu_percent = 100 * (1 - (idle2 - idle) / (total2 - total))
        except:
            cpu_percent = (load1 / cpu_count) * 100
        
        return {
            "cpu_count": cpu_count,
            "load_avg": {
                "1min": round(load1, 2),
                "5min": round(load5, 2),
                "15min": round(load15, 2)
            },
            "cpu_percent": round(cpu_percent, 1)
        }
    except Exception as e:
        return {"error": str(e)}


def get_memory_info() -> Dict:
    """Get memory information and usage."""
    try:
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()
        
        info = {}
        for line in meminfo.split('\n'):
            if 'MemTotal:' in line:
                info['total_gb'] = round(int(line.split()[1]) / 1024 / 1024, 2)
            elif 'MemFree:' in line:
                info['free_gb'] = round(int(line.split()[1]) / 1024 / 1024, 2)
            elif 'MemAvailable:' in line:
                info['available_gb'] = round(int(line.split()[1]) / 1024 / 1024, 2)
            elif 'Buffers:' in line:
                info['buffers_gb'] = round(int(line.split()[1]) / 1024 / 1024, 2)
            elif 'Cached:' in line:
                info['cached_gb'] = round(int(line.split()[1]) / 1024 / 1024, 2)
            elif 'SwapTotal:' in line:
                info['swap_total_gb'] = round(int(line.split()[1]) / 1024 / 1024, 2)
            elif 'SwapFree:' in line:
                info['swap_free_gb'] = round(int(line.split()[1]) / 1024 / 1024, 2)
        
        if 'total_gb' in info and 'available_gb' in info:
            info['used_gb'] = round(info['total_gb'] - info['available_gb'], 2)
            info['memory_percent'] = round((info['used_gb'] / info['total_gb']) * 100, 1)
        
        return info
    except Exception as e:
        return {"error": str(e)}


def get_disk_info() -> Dict:
    """Get disk information and usage."""
    try:
        disks = []
        
        # Get root partition
        total, used, free = shutil.disk_usage('/')
        disks.append({
            "mount": "/",
            "total_gb": round(total / 1024**3, 2),
            "used_gb": round(used / 1024**3, 2),
            "free_gb": round(free / 1024**3, 2),
            "percent": round((used / total) * 100, 1)
        })
        
        # Check for home partition
        if os.path.exists('/home'):
            try:
                total, used, free = shutil.disk_usage('/home')
                disks.append({
                    "mount": "/home",
                    "total_gb": round(total / 1024**3, 2),
                    "used_gb": round(used / 1024**3, 2),
                    "free_gb": round(free / 1024**3, 2),
                    "percent": round((used / total) * 100, 1)
                })
            except:
                pass
        
        return {
            "disks": disks,
            "disk_percent": disks[0]["percent"] if disks else 0
        }
    except Exception as e:
        return {"error": str(e)}


def get_gpu_info() -> Dict:
    """Get GPU information (NVIDIA)."""
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total,memory.used,memory.free,temperature.gpu,utilization.gpu', 
             '--format=csv,noheader,nounits'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return {"available": False, "error": "nvidia-smi not available"}
        
        gpus = []
        for line in result.stdout.strip().split('\n'):
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 6:
                memory_total = float(parts[1])
                memory_used = float(parts[2])
                
                gpus.append({
                    "name": parts[0],
                    "memory_total_mb": memory_total,
                    "memory_used_mb": memory_used,
                    "memory_free_mb": float(parts[3]),
                    "memory_percent": round((memory_used / memory_total) * 100, 1) if memory_total > 0 else 0,
                    "temperature_c": int(parts[4]),
                    "gpu_utilization": int(parts[5])
                })
        
        return {
            "available": True,
            "gpu_count": len(gpus),
            "gpus": gpus,
            "gpu_memory_percent": gpus[0]["memory_percent"] if gpus else 0,
            "gpu_temp": gpus[0]["temperature_c"] if gpus else 0
        }
    except FileNotFoundError:
        return {"available": False, "error": "nvidia-smi not found"}
    except Exception as e:
        return {"available": False, "error": str(e)}


def get_docker_info() -> Dict:
    """Get Docker container status."""
    try:
        result = subprocess.run(
            ['docker', 'ps', '-a', '--format', 'json'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return {"available": False, "error": "Docker not available"}
        
        containers = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    container = json.loads(line)
                    containers.append({
                        "id": container.get("ID", "")[:12],
                        "name": container.get("Names", ""),
                        "image": container.get("Image", ""),
                        "status": container.get("Status", ""),
                        "state": container.get("State", "")
                    })
                except:
                    pass
        
        running = len([c for c in containers if c.get("state") == "running"])
        
        return {
            "available": True,
            "total_containers": len(containers),
            "running_containers": running,
            "stopped_containers": len(containers) - running,
            "containers": containers
        }
    except FileNotFoundError:
        return {"available": False, "error": "Docker not found"}
    except Exception as e:
        return {"available": False, "error": str(e)}


def get_process_info(limit: int = 10) -> Dict:
    """Get top processes by memory usage."""
    try:
        result = subprocess.run(
            ['ps', 'aux', '--sort=-%mem'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        processes = []
        lines = result.stdout.strip().split('\n')
        
        for line in lines[1:limit+1]:  # Skip header
            parts = line.split(None, 10)
            if len(parts) >= 11:
                processes.append({
                    "user": parts[0],
                    "pid": int(parts[1]),
                    "cpu_percent": float(parts[2]),
                    "mem_percent": float(parts[3]),
                    "vsz_kb": int(parts[4]),
                    "rss_kb": int(parts[5]),
                    "command": parts[10][:50]  # Truncate command
                })
        
        return {
            "top_processes": processes,
            "count": len(processes)
        }
    except Exception as e:
        return {"error": str(e)}


def get_network_info() -> Dict:
    """Get network interface information."""
    try:
        result = subprocess.run(
            ['ip', '-j', 'addr'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        interfaces = []
        if result.returncode == 0:
            for iface in json.loads(result.stdout):
                if iface.get("ifname") != "lo":  # Skip loopback
                    addrs = []
                    for addr_info in iface.get("addr_info", []):
                        if addr_info.get("family") == "inet":
                            addrs.append(addr_info.get("local"))
                    
                    interfaces.append({
                        "name": iface.get("ifname"),
                        "state": iface.get("operstate"),
                        "addresses": addrs
                    })
        
        return {
            "interfaces": interfaces,
            "interface_count": len(interfaces)
        }
    except Exception as e:
        return {"error": str(e)}


def check_service_health(services: List[str]) -> Dict:
    """Check health of specified services."""
    results = {}
    
    service_ports = {
        "ollama": 11434,
        "openwebui": 3000,
        "mcpo": 8000,
        "mem0": 8765,
        "qdrant": 6333,
        "redis": 6379,
        "open-notebook": 8502
    }
    
    for service in services:
        port = service_ports.get(service)
        if port:
            try:
                url = f"http://localhost:{port}"
                req = urllib.request.Request(url, method='HEAD')
                urllib.request.urlopen(req, timeout=5)
                results[service] = {"status": "healthy", "port": port}
            except urllib.error.HTTPError:
                results[service] = {"status": "running", "port": port}
            except:
                results[service] = {"status": "unhealthy", "port": port}
        else:
            results[service] = {"status": "unknown", "error": "Unknown service"}
    
    return results


def check_alerts(metrics: Dict, thresholds: List[AlertThreshold] = None) -> List[Dict]:
    """Check metrics against alert thresholds."""
    thresholds = thresholds or DEFAULT_THRESHOLDS
    alerts = []
    
    for threshold in thresholds:
        value = metrics.get(threshold.metric)
        if value is None:
            continue
        
        if value >= threshold.critical:
            alerts.append({
                "level": "critical",
                "metric": threshold.metric,
                "value": f"{value}{threshold.unit}",
                "threshold": f"{threshold.critical}{threshold.unit}",
                "message": f"{threshold.metric} is at critical level: {value}{threshold.unit}"
            })
        elif value >= threshold.warning:
            alerts.append({
                "level": "warning",
                "metric": threshold.metric,
                "value": f"{value}{threshold.unit}",
                "threshold": f"{threshold.warning}{threshold.unit}",
                "message": f"{threshold.metric} is at warning level: {value}{threshold.unit}"
            })
    
    return alerts


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available monitoring tools."""
    return [
        Tool(
            name="get_system_status",
            description="Get comprehensive system status including CPU, memory, disk, and GPU",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_cpu_status",
            description="Get CPU information and usage",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_memory_status",
            description="Get memory information and usage",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_disk_status",
            description="Get disk information and usage",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_gpu_status",
            description="Get GPU information and usage (NVIDIA)",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_docker_status",
            description="Get Docker container status",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_top_processes",
            description="Get top processes by memory usage",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of processes to return (default 10)"
                    }
                }
            }
        ),
        Tool(
            name="get_network_status",
            description="Get network interface information",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="check_services",
            description="Check health of Sovereign AI services",
            inputSchema={
                "type": "object",
                "properties": {
                    "services": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Services to check (ollama, openwebui, mcpo, mem0, qdrant, redis, open-notebook)"
                    }
                }
            }
        ),
        Tool(
            name="check_alerts",
            description="Check system metrics against alert thresholds",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_full_report",
            description="Get a comprehensive system report with all metrics and alerts",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    
    if name == "get_system_status":
        cpu = get_cpu_info()
        memory = get_memory_info()
        disk = get_disk_info()
        gpu = get_gpu_info()
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "timestamp": datetime.now().isoformat(),
                "cpu": cpu,
                "memory": memory,
                "disk": disk,
                "gpu": gpu
            }, indent=2)
        )]
    
    elif name == "get_cpu_status":
        return [TextContent(type="text", text=json.dumps(get_cpu_info(), indent=2))]
    
    elif name == "get_memory_status":
        return [TextContent(type="text", text=json.dumps(get_memory_info(), indent=2))]
    
    elif name == "get_disk_status":
        return [TextContent(type="text", text=json.dumps(get_disk_info(), indent=2))]
    
    elif name == "get_gpu_status":
        return [TextContent(type="text", text=json.dumps(get_gpu_info(), indent=2))]
    
    elif name == "get_docker_status":
        return [TextContent(type="text", text=json.dumps(get_docker_info(), indent=2))]
    
    elif name == "get_top_processes":
        limit = arguments.get("limit", 10)
        return [TextContent(type="text", text=json.dumps(get_process_info(limit), indent=2))]
    
    elif name == "get_network_status":
        return [TextContent(type="text", text=json.dumps(get_network_info(), indent=2))]
    
    elif name == "check_services":
        services = arguments.get("services", ["ollama", "openwebui", "mcpo", "qdrant", "redis"])
        return [TextContent(type="text", text=json.dumps(check_service_health(services), indent=2))]
    
    elif name == "check_alerts":
        cpu = get_cpu_info()
        memory = get_memory_info()
        disk = get_disk_info()
        gpu = get_gpu_info()
        
        metrics = {
            "cpu_percent": cpu.get("cpu_percent", 0),
            "memory_percent": memory.get("memory_percent", 0),
            "disk_percent": disk.get("disk_percent", 0),
            "gpu_memory_percent": gpu.get("gpu_memory_percent", 0),
            "gpu_temp": gpu.get("gpu_temp", 0)
        }
        
        alerts = check_alerts(metrics)
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "metrics": metrics,
                "alerts": alerts,
                "alert_count": len(alerts),
                "has_critical": any(a["level"] == "critical" for a in alerts)
            }, indent=2)
        )]
    
    elif name == "get_full_report":
        cpu = get_cpu_info()
        memory = get_memory_info()
        disk = get_disk_info()
        gpu = get_gpu_info()
        docker = get_docker_info()
        processes = get_process_info(5)
        network = get_network_info()
        services = check_service_health(["ollama", "openwebui", "mcpo", "qdrant", "redis"])
        
        metrics = {
            "cpu_percent": cpu.get("cpu_percent", 0),
            "memory_percent": memory.get("memory_percent", 0),
            "disk_percent": disk.get("disk_percent", 0),
            "gpu_memory_percent": gpu.get("gpu_memory_percent", 0),
            "gpu_temp": gpu.get("gpu_temp", 0)
        }
        
        alerts = check_alerts(metrics)
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "timestamp": datetime.now().isoformat(),
                "hostname": os.uname().nodename,
                "uptime": subprocess.run(['uptime', '-p'], capture_output=True, text=True).stdout.strip(),
                "cpu": cpu,
                "memory": memory,
                "disk": disk,
                "gpu": gpu,
                "docker": docker,
                "top_processes": processes,
                "network": network,
                "services": services,
                "alerts": alerts,
                "summary": {
                    "healthy": len(alerts) == 0,
                    "alert_count": len(alerts),
                    "critical_alerts": len([a for a in alerts if a["level"] == "critical"]),
                    "warning_alerts": len([a for a in alerts if a["level"] == "warning"])
                }
            }, indent=2)
        )]
    
    return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


async def main():
    """Run the system monitor server."""
    logger.info("Starting System Monitor MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())