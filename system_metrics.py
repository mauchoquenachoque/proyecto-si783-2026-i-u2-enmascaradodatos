import os
import platform
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

try:
    import psutil
except ImportError:  # pragma: no cover - fallback seguro si falta la dependencia
    psutil = None

_START_TIME = time.time()


def _get_load_average() -> Optional[Dict[str, float]]:
    try:
        loads = os.getloadavg()
        return {"1m": round(loads[0], 3), "5m": round(loads[1], 3), "15m": round(loads[2], 3)}
    except (AttributeError, OSError):
        return None


def _format_uptime(uptime_seconds: int) -> str:
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m"


def collect_system_metrics() -> Dict[str, Any]:
    timestamp = datetime.now(timezone.utc).isoformat()
    uptime_seconds = max(int(time.time() - _START_TIME), 0)

    cpu_percent = psutil.cpu_percent(interval=0.1) if psutil else None
    cpu_cores = psutil.cpu_count(logical=True) if psutil else os.cpu_count()
    memory = psutil.virtual_memory() if psutil else None
    disk = psutil.disk_usage(os.getcwd()) if psutil else None

    return {
        "cpu_percent": round(cpu_percent, 2) if cpu_percent is not None else None,
        "cpu_cores": cpu_cores,
        "load_average": _get_load_average(),
        "memory_total_mb": round(memory.total / (1024 * 1024), 2) if memory else None,
        "memory_used_mb": round(memory.used / (1024 * 1024), 2) if memory else None,
        "memory_free_mb": round(memory.available / (1024 * 1024), 2) if memory else None,
        "memory_percent": round(memory.percent, 2) if memory else None,
        "disk_total_gb": round(disk.total / (1024 * 1024 * 1024), 2) if disk else None,
        "disk_used_gb": round(disk.used / (1024 * 1024 * 1024), 2) if disk else None,
        "disk_free_gb": round(disk.free / (1024 * 1024 * 1024), 2) if disk else None,
        "disk_percent": round(disk.percent, 2) if disk else None,
        "uptime_seconds": uptime_seconds,
        "uptime": _format_uptime(uptime_seconds),
        "start_time": datetime.fromtimestamp(_START_TIME, tz=timezone.utc).isoformat(),
        "current_time": timestamp,
        "platform": platform.platform(),
        "timestamp": timestamp,
    }
