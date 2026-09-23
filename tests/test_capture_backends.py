"""Tests for low-process capture/input production adapters."""
from __future__ import annotations

import queue
import threading
import time
import pytest

from ldmanager.adb import AdbBinaryResult, AdbCommandResult, PersistentTapAdbRunner
from ldmanager.capture_backends import (
    HybridCaptureAdbRunner, WindowCaptureError, WindowsGraphicsCaptureProvider,
    align_game_viewport, normalize_viewport, _encode, _decode,
)
from ldmanager.window_targets import WindowTarget, suggested_window


class _Inner:
    adb_path = "adb"

    def __init__(self):
        self.captures, self.commands = [], []

    def list_devices(self):
        return "List of devices attached\n"

    def capture_binary(self, serial, args):
        self.captures.append((serial, tuple(args)))
        return AdbBinaryResult(serial, tuple(args), 0, b"adb-frame", "")

    def run(self, serial, args):
        self.commands.append((serial, tuple(args)))
        return AdbCommandResult(serial, tuple(args), 0, "", "")

    def set_adb_path(self, path):
        self.adb_path = path or "adb"


class _Provider:
    def __init__(self, png=b"window-frame", error=None, hwnd=10):
        self.png, self.error, self.closed = png, error, False
        self.target = WindowTarget(hwnd, 20, "LD1")
        self.inputs = 0

    def ensure_usable(self):
        if self.closed:
            raise WindowCaptureError("Closed")

    def after_input(self):
        self.inputs += 1

    def capture_png(self):
        if self.error:
            raise self.error
        return self.png

    def close(self):
        self.closed = True


def test_verified_window_capture_is_used_only_for_its_serial():
    inner = _Inner()
    router = HybridCaptureAdbRunner(inner)
    router.register_verified_window("emulator-5554", _Provider())
    assert router.capture_binary("emulator-5554", ("exec-out",)).stdout_bytes == b"window-frame"
    with pytest.raises(WindowCaptureError):
        router.capture_binary("emulator-5556", ("exec-out",))
    assert inner.captures == []


def test_window_failure_latches_and_never_falls_back_or_sends_another_tap():
    inner = _Inner()
    router = HybridCaptureAdbRunner(inner)
    router.register_verified_window("emulator-5554", _Provider(error=WindowCaptureError("black frame")))
    with pytest.raises(WindowCaptureError, match="black frame"):
        router.capture_binary("emulator-5554", ("exec-out",))
    with pytest.raises(WindowCaptureError):
        router.run("emulator-5554", ("shell", "input", "tap", "1", "2"))
    assert inner.captures == []
    assert inner.commands == []
    assert not router.is_verified("emulator-5554")
    assert router.metrics.snapshot()["window_capture_errors"] == 1


def test_replacing_or_unregistering_window_provider_closes_only_that_provider():
    router = HybridCaptureAdbRunner(_Inner())
    first, second = _Provider(), _Provider()
    router.register_verified_window("emulator-5554", first)
    router.register_verified_window("emulator-5554", second)
    assert first.closed and not second.closed
    router.unregister_window("emulator-5554")
    assert second.closed


class _FakeStdin:
    def __init__(self, lines):
        self.lines, self.writes = lines, []

    def write(self, value):
        self.writes.append(value)
        self.lines.put(value.rsplit("echo ", 1)[1].strip().replace("$?", "0"))

    def flush(self):
        pass


class _FakeProcess:
    def __init__(self, lines):
        self.stdin, self._alive = _FakeStdin(lines), True

    def poll(self):
        return None if self._alive else 1

    def terminate(self):
        self._alive = False


def test_persistent_tap_writes_to_the_account_session_not_a_new_command_process(monkeypatch):
    inner, runner, sessions = _Inner(), None, {}
    runner = PersistentTapAdbRunner(inner)

    def fake_session(serial):
        if serial not in sessions:
            lines = queue.Queue()
            sessions[serial] = (_FakeProcess(lines), lines, threading.Lock())
        return sessions[serial]

    monkeypatch.setattr(runner, "_session", fake_session)
    assert runner.run("emulator-5554", ("shell", "input", "tap", "11", "22")).ok
    assert runner.run("emulator-5556", ("shell", "input", "tap", "33", "44")).ok
    assert inner.commands == []
    assert "input tap 11 22" in sessions["emulator-5554"][0].stdin.writes[0]
    assert "input tap 33 44" in sessions["emulator-5556"][0].stdin.writes[0]


def test_non_tap_commands_keep_the_safe_subprocess_path():
    inner = _Inner()
    runner = PersistentTapAdbRunner(inner)
    assert runner.run("emulator-5554", ("shell", "getprop", "ro.product.model")).ok
    assert inner.commands == [("emulator-5554", ("shell", "getprop", "ro.product.model"))]


def test_raw_native_errors_also_pause_and_other_account_continues():
    inner = _Inner()
    router = HybridCaptureAdbRunner(inner)
    router.register_verified_window("a", _Provider(error=RuntimeError("GPU error")))
    router.register_verified_window("b", _Provider(hwnd=11))
    with pytest.raises(WindowCaptureError):
        router.capture_binary("a", ("exec-out",))
    assert router.capture_binary("b", ("exec-out",)).ok
    assert router.run("b", ("shell", "input", "tap", "1", "2")).ok
    assert inner.captures == []
    assert [s for s, _ in inner.commands] == ["b"]


def test_same_hwnd_cannot_bind_to_two_serials_and_new_verification_clears_fault():
    router = HybridCaptureAdbRunner(_Inner())
    router.register_verified_window("a", _Provider())
    with pytest.raises(WindowCaptureError, match="another"):
        router.register_verified_window("b", _Provider())
    router.register_verified_window("b", _Provider(error=WindowCaptureError("stopped"), hwnd=11))
    with pytest.raises(WindowCaptureError):
        router.capture_binary("b", ())
    router.register_verified_window("b", _Provider(hwnd=11))
    assert router.is_verified("b")
    assert router.fault("b") == ""


def test_only_explicit_preflight_reaches_adb_and_never_uses_cached_window():
    inner = _Inner()
    router = HybridCaptureAdbRunner(inner)
    router.register_verified_window("a", _Provider())
    assert router.preflight_capture_binary("a", ("exec-out",)).stdout_bytes == b"adb-frame"
    assert len(inner.captures) == 1
    assert router.capture_binary("a", ("exec-out",)).stdout_bytes == b"window-frame"
    assert len(inner.captures) == 1


def test_title_suggestion_does_not_confuse_ld1_ld10_or_ambiguous_names():
    one, ten = WindowTarget(1, 1, "LD1"), WindowTarget(10, 10, "LD10")
    assert suggested_window("LD1", [ten, one]) == one
    assert suggested_window("LD1", [ten]) is None
    assert suggested_window("LD1", [one, WindowTarget(2, 2, "LD1 - other")]) is None


def _provider_without_native(monkeypatch):
    provider = WindowsGraphicsCaptureProvider(WindowTarget(1, 2, "LD1"))
    monkeypatch.setattr(provider, "_start", lambda: None)
    provider._latest = "old"
    provider._arrived = time.monotonic()
    return provider


def test_stale_frame_times_out_instead_of_reusing_cache(monkeypatch):
    provider = _provider_without_native(monkeypatch)
    with pytest.raises(WindowCaptureError, match="fresh"):
        provider._fresh_frame(0.01)
    assert not provider._waiting


def test_waits_for_frame_after_input_settle_barrier(monkeypatch):
    provider = _provider_without_native(monkeypatch)
    provider.after_input()
    def deliver():
        for delay, value in ((0.02, "too-early"), (0.22, "new")):
            time.sleep(delay)
            with provider._lock:
                provider._latest, provider._arrived = value, time.monotonic()
                provider._lock.notify_all()
    thread = threading.Thread(target=deliver)
    thread.start()
    try:
        assert provider._fresh_frame(1) == "new"
    finally:
        thread.join()


def test_close_releases_frame_and_wakes_waiter(monkeypatch):
    provider = _provider_without_native(monkeypatch)
    timer = threading.Timer(0.02, provider.close)
    timer.start()
    with pytest.raises(WindowCaptureError, match="stopped"):
        provider._fresh_frame(1)
    timer.join()
    assert provider._latest is None


def test_game_area_alignment_removes_window_chrome_and_rejects_resize():
    cv2 = pytest.importorskip("cv2")
    np = pytest.importorskip("numpy")
    from pathlib import Path
    reference = cv2.imread(str(Path(__file__).parent / "fixtures/game_cal_001/source/completed_target.png"))
    assert reference is not None
    h, w = reference.shape[:2]
    native = np.zeros((h + 50, w + 40, 3), dtype=np.uint8)
    native[30:30+h, 8:8+w] = reference
    viewport, png = align_game_viewport(_encode(reference), _encode(native))
    assert abs(viewport.x - 8) <= 3 and abs(viewport.y - 30) <= 3
    assert _decode(png).shape == reference.shape
    with pytest.raises(WindowCaptureError, match="size changed"):
        normalize_viewport(native[:-10], viewport)


@pytest.mark.parametrize("game_x", [0, 40])
def test_game_area_touching_capture_edge_stays_inside_capture(game_x):
    cv2 = pytest.importorskip("cv2")
    np = pytest.importorskip("numpy")
    from pathlib import Path
    reference = cv2.imread(str(Path(__file__).parent / "fixtures/game_cal_001/source/completed_target.png"))
    assert reference is not None
    # Customer rc.34 frame: 635x374 including top chrome and right toolbar;
    # the 595x334 game image starts at y=40 and reaches the bottom edge.
    native = np.zeros((374, 635, 3), dtype=np.uint8)
    native[40:374, game_x:game_x + 595] = cv2.resize(reference, (595, 334))
    viewport, png = align_game_viewport(_encode(reference), _encode(native))
    assert viewport.x >= 0 and viewport.y >= 0
    assert viewport.x + viewport.width <= 635
    assert viewport.y + viewport.height <= 374
    assert _decode(png).shape == reference.shape


def test_blank_and_unrelated_images_cannot_verify():
    np = pytest.importorskip("numpy")
    pytest.importorskip("cv2")
    with pytest.raises(WindowCaptureError, match="Blank"):
        align_game_viewport(_encode(np.zeros((720, 1280, 3), dtype=np.uint8)),
                            _encode(np.zeros((720, 1280, 3), dtype=np.uint8)))
    random = np.random.default_rng(33)
    with pytest.raises(WindowCaptureError, match="comparison failed"):
        align_game_viewport(_encode(random.integers(0, 255, (180, 320, 3), dtype=np.uint8)),
                            _encode(random.integers(0, 255, (200, 360, 3), dtype=np.uint8)))
