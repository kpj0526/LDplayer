"""Windows-only experiment: explicit preflight ADB probe, no runtime fallback."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Sequence

from .adb import AdbBinaryResult, AdbRunner, validate_serial
from .memory_monitor import CallMetrics
from .window_targets import WindowTarget, validate_window


class WindowCaptureError(RuntimeError):
    pass


@dataclass(frozen=True)
class Viewport:
    x: int
    y: int
    width: int
    height: int
    native_width: int
    native_height: int
    target_width: int
    target_height: int
    score: float


def _decode(png):
    import cv2
    import numpy as np
    image = cv2.imdecode(np.frombuffer(png, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise WindowCaptureError("Capture is not a decodable image")
    return image


def align_game_viewport(adb_png, window_png):
    """Locate the ADB game image inside WGC chrome instead of squashing the window.

    Content/geometry comparison cannot prove account identity when two accounts
    show identical screens. The user also confirms the exact selected HWND.
    """
    import cv2
    import numpy as np
    reference, native = _decode(adb_png), _decode(window_png)
    rh, rw = reference.shape[:2]
    nh, nw = native.shape[:2]
    if reference.std() < 8 or native.std() < 8:
        raise WindowCaptureError("Blank/low-detail frame cannot establish a game viewport")
    factor = min(1.0, 480 / nw)
    small = cv2.resize(native, None, fx=factor, fy=factor, interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    max_scale = min(small.shape[1] / rw, small.shape[0] / rh)
    best = None
    for scale in np.linspace(max_scale * 0.65, max_scale, 100):
        w, h = max(2, round(rw * scale)), max(2, round(rh * scale))
        template = cv2.resize(reference, (w, h), interpolation=cv2.INTER_AREA)
        response = cv2.matchTemplate(gray, cv2.cvtColor(template, cv2.COLOR_BGR2GRAY), cv2.TM_CCOEFF_NORMED)
        _, score, _, (x, y) = cv2.minMaxLoc(response)
        if best is None or score > best[0]:
            best = (score, x, y, w, h)
    score, x, y, w, h = best
    viewport = Viewport(round(x / factor), round(y / factor), round(w / factor),
                        round(h / factor), nw, nh, rw, rh, float(score))
    normalized = normalize_viewport(native, viewport)
    error = float(np.mean(cv2.absdiff(
        cv2.resize(reference, (320, 180)), cv2.resize(normalized, (320, 180))))) / 255
    if score < 0.90 or error > 0.08:
        raise WindowCaptureError(f"ADB/window comparison failed (similarity={score:.3f}, difference={error:.3f}). "
                                 "Check the selected LD window and keep its mission screen steady.")
    return viewport, _encode(normalized)


def normalize_viewport(image, viewport):
    import cv2
    if image.shape[:2] != (viewport.native_height, viewport.native_width):
        raise WindowCaptureError("LD window size changed; run Test capture again")
    crop = image[viewport.y:viewport.y + viewport.height, viewport.x:viewport.x + viewport.width]
    if crop.shape[:2] != (viewport.height, viewport.width):
        raise WindowCaptureError("Game viewport is outside the captured window")
    return cv2.resize(crop, (viewport.target_width, viewport.target_height), interpolation=cv2.INTER_AREA)


def _encode(image):
    import cv2
    ok, encoded = cv2.imencode(".png", image)
    if not ok:
        raise WindowCaptureError("PNG encoding failed")
    return encoded.tobytes()


class WindowsGraphicsCaptureProvider:
    """One raw frame retained; PNG encoding only on request. Fresh frame per read."""
    def __init__(self, target: WindowTarget):
        self.target = target
        self.viewport = None
        self._lock = threading.Condition()
        self._start_lock = threading.Lock()
        self._latest = None
        self._arrived = 0.0
        self._error = ""
        self._control = None
        self._capture = None
        self._closed = False
        self._after_input = 0.0
        self._waiting = False

    def ensure_usable(self):
        try:
            validate_window(self.target)
        except Exception as exc:
            raise WindowCaptureError(str(exc)) from exc
        with self._lock:
            if self._closed or self._error:
                raise WindowCaptureError(self._error or "Window capture stopped")

    def _start(self):
        with self._start_lock:
            self.ensure_usable()
            if self._control is not None:
                return
            try:
                from windows_capture import WindowsCapture
                capture = WindowsCapture(cursor_capture=False, draw_border=False,
                                         window_hwnd=self.target.hwnd, minimum_update_interval=200)

                @capture.event
                def on_frame_arrived(frame, _control):
                    try:
                        with self._lock:
                            if self._closed or self._error or not self._waiting:
                                return
                            self._latest = frame.frame_buffer.copy()
                            self._arrived = time.monotonic()
                            self._lock.notify_all()
                    except Exception as exc:
                        self._set_error(f"Window frame failed: {type(exc).__name__}: {exc}")

                @capture.event
                def on_closed():
                    self._set_error("LD window capture closed; run Test capture again")

                self._capture = capture
                self._control = capture.start_free_threaded()
            except Exception as exc:
                self._set_error(f"Cannot start Windows capture: {type(exc).__name__}: {exc}")
                raise WindowCaptureError(self._error) from exc

    def _set_error(self, error):
        with self._lock:
            self._error = error
            self._lock.notify_all()

    def after_input(self):
        with self._lock:
            self._after_input = time.monotonic() + 0.2

    def _fresh_frame(self, timeout_seconds):
        self._start()
        with self._lock:
            barrier = max(time.monotonic(), self._after_input)
            deadline = time.monotonic() + timeout_seconds
            self._waiting = True
            try:
                while not self._error and not self._closed:
                    if self._latest is not None and self._arrived > barrier:
                        return self._latest
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise WindowCaptureError("No fresh Windows frame; account paused (no ADB fallback)")
                    self._lock.wait(remaining)
                raise WindowCaptureError(self._error or "Window capture stopped")
            finally:
                self._waiting = False

    def capture_native_png(self, timeout_seconds=3.0):
        return _encode(self._fresh_frame(timeout_seconds))

    def capture_png(self, timeout_seconds=3.0):
        if self.viewport is None:
            raise WindowCaptureError("Game viewport has not been verified")
        return _encode(normalize_viewport(self._fresh_frame(timeout_seconds), self.viewport))

    def close(self):
        with self._lock:
            self._closed = True
            self._latest = None
            self._lock.notify_all()
        control, self._control = self._control, None
        self._capture = None
        if control is not None:
            try:
                control.stop()
            except Exception:
                pass


class HybridCaptureAdbRunner:
    """Legacy class name, strict Windows-only runtime. ADB preflight is explicit."""
    mode = "windows_only"

    def __init__(self, inner: AdbRunner, metrics=None):
        self._inner = inner
        self.metrics = metrics or CallMetrics()
        self._providers = {}
        self._faults = {}
        self._counts = {}
        self._lock = threading.RLock()

    def register_verified_window(self, serial, provider):
        validate_serial(serial)
        with self._lock:
            for other, item in self._providers.items():
                if other != serial and item.target.hwnd == provider.target.hwnd:
                    raise WindowCaptureError("This LD window is already bound to another ADB serial")
            old = self._providers.get(serial)
            self._providers[serial] = provider
            self._faults.pop(serial, None)
        if old is not None and old is not provider:
            old.close()

    def unregister_window(self, serial):
        with self._lock:
            provider = self._providers.pop(serial, None)
            self._faults.pop(serial, None)
        if provider is not None:
            provider.close()

    def fault(self, serial):
        with self._lock:
            return self._faults.get(serial, "")

    def is_verified(self, serial):
        with self._lock:
            return serial in self._providers and serial not in self._faults

    def snapshot(self):
        with self._lock:
            return {s: {"mode": self.mode, "verified": s in self._providers and s not in self._faults,
                        "window_hwnd": self._providers[s].target.hwnd if s in self._providers else None,
                        "window_calls": self._counts.get(s, 0), "error": self._faults.get(s, "")}
                    for s in self._providers.keys() | self._faults.keys()}

    def _provider(self, serial):
        validate_serial(serial)
        with self._lock:
            if serial in self._faults:
                raise WindowCaptureError(self._faults[serial])
            provider = self._providers.get(serial)
        if provider is None:
            raise WindowCaptureError("Windows capture not verified. Run Test capture before Start.")
        return provider

    def _fail(self, serial, exc):
        detail = f"Windows-only capture paused: {type(exc).__name__}: {exc}"
        with self._lock:
            if serial in self._faults:
                raise WindowCaptureError(self._faults[serial]) from exc
            self._faults[serial] = detail
            provider = self._providers.pop(serial, None)
        self.metrics.add("window_capture_errors")
        if provider is not None:
            provider.close()
        raise WindowCaptureError(detail) from exc

    def list_devices(self):
        return self._inner.list_devices()

    def preflight_capture_binary(self, serial, args):
        validate_serial(serial)
        with self.metrics.preflight():
            return self._inner.capture_binary(serial, args)

    def run(self, serial, args: Sequence[str]):
        try:
            provider = self._provider(serial)
            provider.ensure_usable()
        except Exception as exc:
            return self._fail(serial, exc)
        self.metrics.add("adb_command_calls")
        if tuple(args[:3]) == ("shell", "input", "tap"):
            self.metrics.add("adb_tap_calls")
        result = self._inner.run(serial, args)
        provider.after_input()
        return result

    def capture_binary(self, serial, args):
        try:
            provider = self._provider(serial)
            png = provider.capture_png()
            self.metrics.add("window_capture_calls")
            with self._lock:
                self._counts[serial] = self._counts.get(serial, 0) + 1
            return AdbBinaryResult(serial, tuple(args), 0, png, "")
        except Exception as exc:
            return self._fail(serial, exc)

    def set_adb_path(self, adb_path):
        self.close()
        self._inner.set_adb_path(adb_path)

    @property
    def adb_path(self):
        return getattr(self._inner, "adb_path", None)

    def close(self):
        with self._lock:
            serials = tuple(self._providers)
        for serial in serials:
            self.unregister_window(serial)
        closer = getattr(self._inner, "close", None)
        if closer is not None:
            closer()
