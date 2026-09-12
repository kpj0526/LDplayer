"""Injectable ADB runner + `adb devices` parsing (TP-002 stage 3).

Scope, deliberately narrow:
  * An :class:`AdbRunner` interface with exactly two operations: list
    devices, and run a command scoped to *one* explicit serial.
  * A real, subprocess-backed implementation (:class:`SubprocessAdbRunner`).
  * Safe parsing of `adb devices` text output.

No touch/tap/input, no screenshot capture, no login/reconnect flow, no
web DOM, no global mouse control, and no game action is implemented
here or anywhere in this stage. ``run()`` never guesses or defaults a
serial -- callers (and tests, via a fake runner) must always supply
one, so a command can never silently apply to "whatever device is
current" or to every device at once.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, Sequence


class AdbDeviceState(str, Enum):
    """Normalized state from the second column of `adb devices` output."""

    DEVICE = "device"  # online and authorized
    OFFLINE = "offline"
    UNAUTHORIZED = "unauthorized"
    UNKNOWN = "unknown"  # any token we don't specifically recognize


_KNOWN_STATES = {
    "device": AdbDeviceState.DEVICE,
    "offline": AdbDeviceState.OFFLINE,
    "unauthorized": AdbDeviceState.UNAUTHORIZED,
}


@dataclass(frozen=True)
class AdbDevice:
    """One row of parsed `adb devices` output."""

    serial: str
    state: AdbDeviceState
    raw_state: str  # the exact token ADB printed, kept for diagnostics


@dataclass(frozen=True)
class AdbCommandResult:
    """Result of a single-serial ADB command invocation."""

    serial: str
    args: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


class AdbRunner(Protocol):
    """Minimal interface an ADB runner must satisfy.

    Deliberately just two methods, so a fake test double is trivial to
    write (see ``tests/fakes.py``) and any real implementation stays
    swappable/injectable.
    """

    def list_devices(self) -> str:
        """Return the raw stdout of an `adb devices`-equivalent call."""
        ...

    def run(self, serial: str, args: Sequence[str]) -> AdbCommandResult:
        """Run a command scoped to exactly one device serial."""
        ...


def build_adb_command(adb_path: str, serial: str, args: Sequence[str]) -> list[str]:
    """Build an argv list scoped to exactly one ``serial``.

    Rejects an empty/whitespace-containing serial outright (a valid ADB
    serial never contains whitespace) rather than constructing a command
    that could end up targeting the wrong — or no specific — device.
    """

    if not serial or any(ch.isspace() for ch in serial):
        raise ValueError(f"Invalid ADB serial: {serial!r}")
    return [adb_path, "-s", serial, *args]


class SubprocessAdbRunner:
    """Real ADB runner: shells out to the `adb` executable.

    The only place a real process is spawned. ``run`` always requires an
    explicit serial (via :func:`build_adb_command`) — there is no
    "current device" fallback.
    """

    def __init__(self, adb_path: str = "adb", timeout: float = 15.0) -> None:
        self.adb_path = adb_path
        self.timeout = timeout

    def list_devices(self) -> str:
        completed = subprocess.run(
            [self.adb_path, "devices"],
            capture_output=True,
            text=True,
            timeout=self.timeout,
            check=False,
        )
        return completed.stdout

    def run(self, serial: str, args: Sequence[str]) -> AdbCommandResult:
        full_args = build_adb_command(self.adb_path, serial, args)
        completed = subprocess.run(
            full_args,
            capture_output=True,
            text=True,
            timeout=self.timeout,
            check=False,
        )
        return AdbCommandResult(
            serial=serial,
            args=tuple(args),
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )


def parse_adb_devices_output(raw_output: str) -> list[AdbDevice]:
    """Safely parse `adb devices` output.

    Tolerant of the banner line ("List of devices attached"), blank
    lines, and daemon-status lines (e.g. "* daemon not running;
    starting now *"). A line that doesn't have at least a serial and a
    state column is skipped rather than raising — a genuinely malformed
    or truncated line must never crash discovery; it just means that
    one line contributes no device. An entirely empty/garbage input
    safely yields an empty list.
    """

    devices: list[AdbDevice] = []
    for line in raw_output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.lower().startswith("list of devices"):
            continue
        if stripped.startswith("*"):
            continue
        parts = stripped.split()
        if len(parts) < 2:
            continue
        serial, raw_state = parts[0], parts[1]
        state = _KNOWN_STATES.get(raw_state, AdbDeviceState.UNKNOWN)
        devices.append(AdbDevice(serial=serial, state=state, raw_state=raw_state))
    return devices
