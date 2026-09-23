"""Bounded-memory counters and 30-second diagnostic CSVs; no ADB polling."""
from __future__ import annotations

import csv
import ctypes
import os
import threading
import time
import uuid
from contextlib import contextmanager
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


COUNTERS = (
    "adb_process_starts", "adb_capture_calls", "adb_preflight_captures",
    "adb_runtime_captures", "adb_command_calls", "adb_tap_calls", "adb_discovery_calls",
    "window_capture_calls", "window_capture_errors",
)


class CallMetrics:
    def __init__(self):
        self._lock = threading.Lock()
        self._totals = Counter({key: 0 for key in COUNTERS})
        self._context = threading.local()

    @contextmanager
    def preflight(self):
        previous = getattr(self._context, "preflight", False)
        self._context.preflight = True
        try:
            yield
        finally:
            self._context.preflight = previous

    def record_capture(self):
        with self._lock:
            self._totals["adb_capture_calls"] += 1
            key = "adb_preflight_captures" if getattr(self._context, "preflight", False) else "adb_runtime_captures"
            self._totals[key] += 1

    def add(self, key):
        with self._lock:
            self._totals[key] += 1

    def snapshot(self):
        with self._lock:
            result = dict(self._totals)
            result["adb_calls"] = result["adb_capture_calls"] + result["adb_command_calls"] + result["adb_discovery_calls"]
            return result


def system_commit():
    """GetPerformanceInfo reports pages, NOT bytes or physical working set."""
    if os.name != "nt":
        raise OSError("Windows commit counters are unavailable on this platform")
    from ctypes import wintypes

    class PerformanceInfo(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in (
                "CommitTotal", "CommitLimit", "CommitPeak", "PhysicalTotal",
                "PhysicalAvailable", "SystemCache", "KernelTotal", "KernelPaged",
                "KernelNonpaged", "PageSize",
            )
        ] + [(name, wintypes.DWORD) for name in ("HandleCount", "ProcessCount", "ThreadCount")]

    info = PerformanceInfo()
    info.cb = ctypes.sizeof(info)
    api = ctypes.WinDLL("psapi", use_last_error=True).GetPerformanceInfo
    api.argtypes = [ctypes.POINTER(PerformanceInfo), wintypes.DWORD]
    api.restype = wintypes.BOOL
    if not api(ctypes.byref(info), info.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return {
        "commit_bytes": info.CommitTotal * info.PageSize,
        "commit_limit_bytes": info.CommitLimit * info.PageSize,
        "kernel_paged_bytes": info.KernelPaged * info.PageSize,
        "kernel_nonpaged_bytes": info.KernelNonpaged * info.PageSize,
    }


def process_memory():
    import psutil
    rows = []
    for process in psutil.process_iter(["pid", "name"]):
        name = (process.info["name"] or "").lower()
        if process.pid == os.getpid():
            group = "ldmanager"
        elif name in ("adb.exe", "adb"):
            group = "adb"
        elif name.startswith(("dnplayer", "ldplayer", "ldvbox", "ld9box", "ldconsole", "dnconsole")):
            group = "ldplayer"
        elif name.startswith(("python", "ldmanager")):
            group = "other_python_or_manager"
        else:
            continue
        try:
            mem = process.memory_info()
            # Windows psutil.private = PrivateUsage (private committed bytes).
            # Never substitute RSS/VMS as if they were the same measurement.
            rows.append({"pid": process.pid, "name": name, "group": group,
                         "created_at": process.create_time(),
                         "private_bytes": getattr(mem, "private", None),
                         "working_set_bytes": mem.rss, "error": ""})
        except (psutil.Error, OSError) as exc:
            rows.append({"pid": process.pid, "name": name, "group": group,
                         "created_at": None, "private_bytes": None,
                         "working_set_bytes": None, "error": type(exc).__name__})
    return rows


class MemoryMonitor:
    def __init__(self, metrics, state=lambda: {}, root=Path("diagnostics/memory"),
                 interval=30.0, system_reader=system_commit, process_reader=process_memory):
        session = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8]
        self.directory = Path(root) / session
        self.metrics, self.state = metrics, state
        self.interval, self.system_reader, self.process_reader = interval, system_reader, process_reader
        self._stop = threading.Event()
        self._thread = None
        self._sample_lock = threading.Lock()
        self._started = time.monotonic()
        self._previous = None
        self.latest = {}
        self.error = ""

    def _append(self, name, rows):
        if not rows:
            return
        self.directory.mkdir(parents=True, exist_ok=True)
        # Rotate to a new part at 10 MiB; no accumulated in-memory history.
        part = 0
        while True:
            path = self.directory / (name if part == 0 else f"{Path(name).stem}-{part}.csv")
            if not path.exists() or path.stat().st_size < 10 * 1024 * 1024:
                break
            part += 1
        new = not path.exists()
        with path.open("a", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            if new:
                writer.writeheader()
            writer.writerows(rows)

    def sample(self):
        with self._sample_lock:
            stamp = datetime.now(timezone.utc).isoformat()
            errors = []
            try:
                system = self.system_reader()
            except Exception as exc:
                system = dict.fromkeys(("commit_bytes", "commit_limit_bytes", "kernel_paged_bytes", "kernel_nonpaged_bytes"))
                errors.append(f"system: {type(exc).__name__}: {exc}")
            try:
                processes = self.process_reader()
            except Exception as exc:
                processes = []
                errors.append(f"processes: {type(exc).__name__}: {exc}")
            counts = self.metrics.snapshot()
            ld_processes = [p for p in processes if p["group"] == "ldplayer"]
            ld_private = (None if any(p["private_bytes"] is None for p in ld_processes)
                          else sum(p["private_bytes"] for p in ld_processes))
            current = system.get("commit_bytes")
            delta = current - self._previous[0] if current is not None and self._previous else None
            calls = counts["adb_capture_calls"] - self._previous[1] if self._previous else 0
            row = {"utc": stamp, "elapsed_seconds": round(time.monotonic() - self._started, 2),
                   "mode": "windows_only", **system, **counts,
                   "commit_delta_bytes": delta, "adb_capture_delta": calls,
                   "commit_delta_per_1000_adb_captures": delta * 1000 / calls if delta is not None and calls else None,
                   "adb_process_count": sum(p["group"] == "adb" for p in processes),
                   "ldplayer_private_bytes": ld_private,
                   "ldmanager_private_bytes": next((p["private_bytes"] for p in processes if p["group"] == "ldmanager"), None),
                   "process_read_errors": sum(bool(p["error"]) for p in processes),
                   "error": "; ".join(errors)}
            self._append("summary.csv", [row])
            self._append("processes.csv", [{"utc": stamp, **p} for p in processes])
            states = self.state()
            self._append("accounts.csv", [{"utc": stamp, "serial": s, **v} for s, v in states.items()])
            self._previous = (current, counts["adb_capture_calls"]) if current is not None else None
            self.latest, self.error = row, row["error"]
            return row

    def start(self):
        if self._thread is not None:
            return
        def loop():
            while not self._stop.is_set():
                try:
                    self.sample()
                except Exception as exc:
                    self.error = f"Cannot save memory log: {type(exc).__name__}: {exc}"
                self._stop.wait(self.interval)
        self._thread = threading.Thread(target=loop, name="memory-monitor", daemon=True)
        self._thread.start()

    def close(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=3)
            if not self._thread.is_alive():
                try:
                    self.sample()
                except Exception as exc:
                    self.error = f"Cannot save final memory sample: {exc}"
