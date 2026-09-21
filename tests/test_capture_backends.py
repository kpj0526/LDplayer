"""Tests for low-process capture/input production adapters."""
from __future__ import annotations

import queue
import threading

from ldmanager.adb import AdbBinaryResult, AdbCommandResult, PersistentTapAdbRunner
from ldmanager.capture_backends import HybridCaptureAdbRunner, WindowCaptureError


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
    def __init__(self, png=b"window-frame", error=None):
        self.png, self.error, self.closed = png, error, False

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
    assert router.capture_binary("emulator-5556", ("exec-out",)).stdout_bytes == b"adb-frame"
    assert inner.captures == [("emulator-5556", ("exec-out",))]


def test_window_capture_failure_falls_back_to_serial_scoped_adb_capture():
    inner = _Inner()
    router = HybridCaptureAdbRunner(inner)
    router.register_verified_window("emulator-5554", _Provider(error=WindowCaptureError("black frame")))
    assert router.capture_binary("emulator-5554", ("exec-out",)).stdout_bytes == b"adb-frame"
    assert inner.captures == [("emulator-5554", ("exec-out",))]


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
        self.lines.put(value.rsplit("echo ", 1)[1].strip())

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
