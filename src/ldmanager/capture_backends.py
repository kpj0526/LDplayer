"""Window Graphics Capture with safe ADB fallback.

The game renderer can be captured directly from its LDPlayer window while
touches stay serial-scoped through ADB.  A provider is enabled only after a
per-account probe has produced a valid 1280x720 PNG; any capture failure
falls back to the ordinary ADB screencap path rather than fabricating a
frame or blocking another account.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Sequence

from .adb import AdbBinaryResult, AdbCommandResult, AdbRunner, validate_serial


class WindowCaptureError(RuntimeError):
    pass


class WindowsGraphicsCaptureProvider:
    """Latest-frame-only Windows Graphics Capture provider.

    ``window_name`` is a case-insensitive substring chosen from the account
    name (LD1..LD9).  The native capture callback replaces the prior frame;
    it never queues frames, so a slow worker cannot accumulate video RAM.
    """

    def __init__(self, window_name: str, *, width: int = 1280, height: int = 720,
                 minimum_update_interval_ms: int = 200) -> None:
        self.window_name = window_name
        self.width = width
        self.height = height
        self.minimum_update_interval_ms = minimum_update_interval_ms
        self._lock = threading.Condition()
        self._latest_png: bytes | None = None
        self._error = ""
        self._control = None
        self._started = False

    def _start(self) -> None:
        if self._started:
            return
        if __import__("os").name != "nt":
            raise WindowCaptureError("Windows Graphics Capture is available only on Windows.")
        try:
            import cv2  # type: ignore
            from windows_capture import WindowsCapture  # type: ignore
        except ImportError as exc:
            raise WindowCaptureError("windows-capture/OpenCV dependency is unavailable.") from exc

        capture = WindowsCapture(
            cursor_capture=False,
            draw_border=False,
            window_name=self.window_name,
            minimum_update_interval=self.minimum_update_interval_ms,
        )

        @capture.event
        def on_frame_arrived(frame, _control):
            try:
                image = frame.frame_buffer.copy()
                # Capture APIs yield BGRA.  Resize only when the captured
                # client image differs from the configured internal game
                # size; OpenCV templates and ADB touch coordinates remain
                # in the same 1280x720 coordinate system.
                if image.shape[1] != self.width or image.shape[0] != self.height:
                    image = cv2.resize(image, (self.width, self.height), interpolation=cv2.INTER_AREA)
                ok, encoded = cv2.imencode(".png", image)
                if not ok:
                    raise RuntimeError("OpenCV PNG encoding failed")
                with self._lock:
                    self._latest_png = encoded.tobytes()
                    self._error = ""
                    self._lock.notify_all()
            except Exception as exc:  # callback exceptions must not kill GUI
                with self._lock:
                    self._error = f"window frame processing failed: {type(exc).__name__}: {exc}"
                    self._lock.notify_all()

        @capture.event
        def on_closed():
            with self._lock:
                self._error = "LDPlayer window capture closed."
                self._lock.notify_all()

        self._control = capture.start_free_threaded()
        self._started = True

    def capture_png(self, timeout_seconds: float = 2.0) -> bytes:
        self._start()
        deadline = time.monotonic() + timeout_seconds
        with self._lock:
            while self._latest_png is None and not self._error:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise WindowCaptureError(f"No frame received for window {self.window_name!r}.")
                self._lock.wait(remaining)
            if self._error:
                raise WindowCaptureError(self._error)
            assert self._latest_png is not None
            return self._latest_png

    def close(self) -> None:
        if self._control is not None:
            self._control.stop()
        self._control = None
        self._started = False


class HybridCaptureAdbRunner:
    """Routes verified serials to window capture; otherwise delegates ADB.

    Touches never go through this class: ``run`` is delegated unchanged to
    the underlying serial-scoped runner.  Each serial has its own provider,
    so LD1 cannot obtain LD2's frame.
    """

    def __init__(self, inner: AdbRunner) -> None:
        self._inner = inner
        self._providers: dict[str, WindowsGraphicsCaptureProvider] = {}
        self._lock = threading.Lock()

    def register_verified_window(self, serial: str, provider: WindowsGraphicsCaptureProvider) -> None:
        validate_serial(serial)
        with self._lock:
            old = self._providers.get(serial)
            self._providers[serial] = provider
        if old is not None and old is not provider:
            old.close()

    def unregister_window(self, serial: str) -> None:
        with self._lock:
            provider = self._providers.pop(serial, None)
        if provider is not None:
            provider.close()

    def list_devices(self) -> str:
        return self._inner.list_devices()

    def run(self, serial: str, args: Sequence[str]) -> AdbCommandResult:
        return self._inner.run(serial, args)

    def capture_binary(self, serial: str, args: Sequence[str]) -> AdbBinaryResult:
        validate_serial(serial)
        with self._lock:
            provider = self._providers.get(serial)
        if provider is not None:
            try:
                png = provider.capture_png()
                return AdbBinaryResult(serial, tuple(args), 0, png, "")
            except WindowCaptureError:
                # A minimized/closed/GPU-incompatible window must not take
                # down the worker; fall back to the known ADB path.
                pass
        return self._inner.capture_binary(serial, args)

    def set_adb_path(self, adb_path: str | None) -> None:
        setter = getattr(self._inner, "set_adb_path", None)
        if setter is not None:
            setter(adb_path)

    @property
    def adb_path(self):
        return getattr(self._inner, "adb_path", None)
