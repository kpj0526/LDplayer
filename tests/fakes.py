"""Shared test doubles for TP-002/TP-003 (no real ADB, no subprocess)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from ldmanager.adb import AdbBinaryResult, AdbCommandResult, validate_serial


@dataclass
class FakeAdbRunner:
    """In-memory :class:`~ldmanager.adb.AdbRunner` double.

    ``devices_output`` is returned verbatim by :meth:`list_devices`.
    ``command_results`` optionally maps ``(serial, tuple(args))`` to a
    canned :class:`AdbCommandResult`; any :meth:`run` call not found
    there gets a default successful, empty result. ``capture_results``
    is the same idea for :meth:`capture_binary`, keyed the same way,
    with a default successful-but-empty :class:`AdbBinaryResult`.

    Every :meth:`run` call is recorded in ``calls`` and every
    :meth:`capture_binary` call in ``capture_calls`` (both in order,
    each as ``(serial, tuple(args))``) so tests can assert commands
    stayed scoped to the right serial, didn't leak across accounts, and
    — for the guarded-touch state machine — that a touch was never
    repeated no matter how many captures/retries happened around it.
    """

    devices_output: str = ""
    command_results: dict = field(default_factory=dict)
    capture_results: dict = field(default_factory=dict)
    calls: list = field(default_factory=list)
    capture_calls: list = field(default_factory=list)
    list_devices_calls: int = 0

    def list_devices(self) -> str:
        self.list_devices_calls += 1
        return self.devices_output

    def run(self, serial: str, args: Sequence[str]) -> AdbCommandResult:
        validate_serial(serial)
        args_tuple = tuple(args)
        self.calls.append((serial, args_tuple))
        canned = self.command_results.get((serial, args_tuple))
        if canned is not None:
            return canned
        return AdbCommandResult(
            serial=serial, args=args_tuple, returncode=0, stdout="", stderr=""
        )

    def capture_binary(self, serial: str, args: Sequence[str]) -> AdbBinaryResult:
        validate_serial(serial)
        args_tuple = tuple(args)
        self.capture_calls.append((serial, args_tuple))
        canned = self.capture_results.get((serial, args_tuple))
        if canned is not None:
            return canned
        return AdbBinaryResult(
            serial=serial, args=args_tuple, returncode=0, stdout_bytes=b"", stderr=""
        )


class BrokenAdbRunner:
    """An AdbRunner whose device listing always fails.

    Used to test that discovery failure is surfaced as a structured,
    per-account status rather than propagating an exception.
    """

    def __init__(self, message: str = "adb executable not found") -> None:
        self.message = message

    def list_devices(self) -> str:
        raise RuntimeError(self.message)

    def run(self, serial: str, args: Sequence[str]) -> AdbCommandResult:  # pragma: no cover
        raise NotImplementedError("BrokenAdbRunner.run is not used by these tests")

    def capture_binary(self, serial: str, args: Sequence[str]) -> AdbBinaryResult:  # pragma: no cover
        raise NotImplementedError("BrokenAdbRunner.capture_binary is not used by these tests")


class ExceptionRaisingCaptureRunner:
    """An AdbRunner whose ``capture_binary`` always raises.

    Distinct from a canned nonzero-returncode :class:`AdbBinaryResult`:
    this exercises the "the runner itself raised" path in
    :func:`ldmanager.screenshot.capture_screenshot` (and, transitively,
    the guarded-touch state machine), proving neither propagates the
    exception -- it becomes a structured, ``ok=False`` result instead.
    """

    def __init__(self, message: str = "capture backend crashed") -> None:
        self.message = message
        self.calls: list = []
        self.capture_calls: list = []

    def list_devices(self) -> str:
        return ""

    def run(self, serial: str, args: Sequence[str]) -> AdbCommandResult:
        validate_serial(serial)
        args_tuple = tuple(args)
        self.calls.append((serial, args_tuple))
        return AdbCommandResult(
            serial=serial, args=args_tuple, returncode=0, stdout="", stderr=""
        )

    def capture_binary(self, serial: str, args: Sequence[str]) -> AdbBinaryResult:
        validate_serial(serial)
        self.capture_calls.append((serial, tuple(args)))
        raise RuntimeError(self.message)
