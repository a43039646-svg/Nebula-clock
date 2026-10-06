from __future__ import annotations

import os
import platform
from pathlib import Path


def _read_os_release() -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
            if "=" not in line or line.startswith("#"):
                continue
            key, value = line.split("=", 1)
            values[key] = value.strip().strip('"').strip("'")
    except OSError:
        pass
    return values


def _cpu_model() -> str:
    try:
        lines = Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="ignore").splitlines()
        for line in lines:
            if line.lower().startswith("model name") and ":" in line:
                return line.split(":", 1)[1].strip()
        for line in lines:
            if line.lower().startswith("hardware") and ":" in line:
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "Unknown CPU"


def _memory() -> str:
    try:
        values = {}
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            key, value = line.split(":", 1)
            if key in ("MemTotal", "MemAvailable"):
                values[key] = int(value.strip().split()[0])
        total = values.get("MemTotal", 0)
        available = values.get("MemAvailable", 0)
        used = max(0, total - available)
        return f"{used / 1024 / 1024:.1f}/{total / 1024 / 1024:.1f} GB"
    except (OSError, ValueError):
        return "Unknown"


def _uptime() -> str:
    try:
        total_seconds = int(float(Path("/proc/uptime").read_text().split()[0]))
        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)
        if days:
            return f"{days}d {hours}h"
        if hours:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    except (OSError, ValueError):
        return "Unknown"


def collect(theme_name: str) -> list[tuple[str, str]]:
    os_data = _read_os_release()
    distro = os_data.get("PRETTY_NAME") or theme_name.replace("_", " ").title()
    return [
        ("OS", distro),
        ("Kernel", platform.release()),
        ("CPU", _cpu_model()),
        ("RAM", _memory()),
        ("Uptime", _uptime()),
        ("Cores", str(os.cpu_count() or 1)),
    ]
