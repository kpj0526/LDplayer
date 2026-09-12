"""Shared test doubles for TP-002 stage 3 (no real ADB, no subprocess)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from ldmanager.adb import AdbCommandResult


@dataclass
class FakeAdbRunner:
    """In-memory :class:`~ldmanager.adb.AdbRunner` double.

    ``devices_output`` is returned verbatim by :meth:`list_devices`.
    ``command_results`` optionally maps ``(serial, tuple(args))`` to a
    canned :class:`AdbCommandResult`; any call not found there gets a
    default successful, empty result. Every :meth:`run` call is recorded
    in ``calls`` (in order) so tests can assert commands stayed scoped
    to the right serial and didn't leak across accounts.
    """

    devices_output: str = ""
    command_results: dict = field(default_factory=dict)
    calls: list = field(default_factory=list)
    list_devices_calls: int = 0

    def list_devices(self) -> str:
        self.list_devices_calls += 1
        return self.devices_output

    def run(self, serial: str, args: Sequence[str]) -> AdbCommandResult:
        if not serial:
            raise ValueError("An explicit ADB serial is required.")
        args_tuple = tuple(args)
        self.calls.append((serial, args_tuple))
        canned = self.command_results.get((serial, args_tuple))
        if canned is not None:
            return canned
        return AdbCommandResult(
            serial=serial, args=args_tuple, returncode=0, stdout="", stderr=""
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
