"""Packaged dependency/Win32/logging smoke check; never calls ADB or starts workers."""
import json
import sys
from importlib.metadata import version
from pathlib import Path


def run(output):
    import cv2
    import numpy
    import psutil
    import windows_capture
    from .memory_monitor import CallMetrics, MemoryMonitor
    from .window_targets import list_ld_windows
    target = Path(output)
    monitor = MemoryMonitor(CallMetrics(), root=target.parent / "memory-smoke")
    row = monitor.sample()
    result = {"frozen": bool(getattr(sys, "frozen", False)), "python": sys.version,
              "opencv": cv2.__version__, "numpy": numpy.__version__, "psutil": psutil.__version__,
              "windows_capture": version("windows-capture"),
              "window_count": len(list_ld_windows()), "sample": row,
              "logs": str(monitor.directory)}
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if not row["error"] and row["commit_bytes"] is not None else 1
