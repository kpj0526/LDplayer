"""Explicit HWND/PID window bindings; never select the first substring match."""
from __future__ import annotations

import ctypes
import os
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class WindowTarget:
    hwnd: int
    pid: int
    title: str

    @property
    def display(self):
        return f"{self.title} [PID {self.pid}, HWND {self.hwnd}]"


def _user32():
    if os.name != "nt":
        raise OSError("Window capture requires Windows")
    from ctypes import wintypes
    api = ctypes.WinDLL("user32", use_last_error=True)
    api.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    api.GetWindowThreadProcessId.restype = wintypes.DWORD
    for name in ("IsWindow", "IsWindowVisible", "IsIconic"):
        getattr(api, name).argtypes = [wintypes.HWND]
        getattr(api, name).restype = wintypes.BOOL
    api.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    api.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    return api


def list_ld_windows():
    from ctypes import wintypes
    import psutil
    api = _user32()
    windows = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    @callback_type
    def visit(hwnd, _):
        if not api.IsWindowVisible(hwnd):
            return True
        title = ctypes.create_unicode_buffer(api.GetWindowTextLengthW(hwnd) + 1)
        api.GetWindowTextW(hwnd, title, len(title))
        pid = wintypes.DWORD()
        api.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        try:
            name = psutil.Process(pid.value).name().lower()
            if title.value and name.startswith(("dnplayer", "ldplayer")):
                windows.append(WindowTarget(int(hwnd), pid.value, title.value))
        except psutil.Error:
            pass
        return True
    api.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    api.EnumWindows.restype = wintypes.BOOL
    if not api.EnumWindows(visit, 0):
        raise ctypes.WinError(ctypes.get_last_error())
    return windows


def suggested_window(account, windows):
    matches = [w for w in windows if re.search(r"(?<![\w])" + re.escape(account) + r"(?![\w])", w.title, re.I)]
    return matches[0] if len(matches) == 1 else None


def validate_window(target):
    from ctypes import wintypes
    api = _user32()
    pid = wintypes.DWORD()
    api.GetWindowThreadProcessId(target.hwnd, ctypes.byref(pid))
    if not api.IsWindow(target.hwnd) or pid.value != target.pid:
        raise OSError("Selected LD window closed or changed. Refresh windows and run Test capture again.")
    if api.IsIconic(target.hwnd):
        raise OSError("Selected LD window is minimized. Restore it and run Test capture again.")
