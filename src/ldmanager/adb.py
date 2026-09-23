"""Injectable ADB runner + `adb devices` parsing (TP-002 stage 3 / TP-003).

Scope, deliberately narrow:
  * An :class:`AdbRunner` interface with exactly three operations: list
    devices, run a text-output command scoped to *one* explicit serial,
    and capture a *binary* command's raw stdout (for screenshots) scoped
    to that same one serial.
  * A real, subprocess-backed implementation (:class:`SubprocessAdbRunner`).
  * Safe parsing of `adb devices` text output.

No touch/tap/input command is *issued* by this module (that lives in
``guarded_touch.py``, built strictly on top of ``run()`` here), no OCR,
no template/mission logic, no login/reconnect flow, no web DOM, and no
global mouse control is implemented here or anywhere in this project.
Neither ``run()`` nor ``capture_binary()`` ever guesses or defaults a
serial -- callers (and tests, via a fake runner) must always supply
one, so a command can never silently apply to "whatever device is
current" or to every device at once.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import queue
import threading
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Protocol, Sequence

# NO-CONSOLE-FLICKER-001: a real customer report -- every subprocess.run()
# call below spawns adb.exe as a genuine child console process, and on
# Windows that flashes a brand-new black console window on screen unless
# explicitly suppressed. With one ADB command per tap/capture, a live run
# flickered this open-and-close constantly. creationflags is a
# Windows-only subprocess.run() kwarg (passing it on POSIX raises
# ValueError), so it's built once, guarded by platform, and spread into
# every call below.
_NO_CONSOLE_WINDOW_KWARGS = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}


def resolve_adb_path(explicit_path: str | None = None) -> str:
    """Locate a usable ADB executable without guessing a device port.

    The user supplied path and ``LDMANAGER_ADB_PATH`` win.  Otherwise the
    system PATH and common LDPlayer install locations are checked.  A
    missing executable is returned as ``"adb"`` so subprocess produces an
    honest ``FileNotFoundError``; callers must surface that as a connection
    error, never pretend discovery succeeded.
    """
    candidates: list[str] = []
    if explicit_path:
        candidates.append(explicit_path)
    if os.environ.get("LDMANAGER_ADB_PATH"):
        candidates.append(os.environ["LDMANAGER_ADB_PATH"])
    on_path = shutil.which("adb")
    if on_path:
        candidates.append(on_path)
    for base in (r"C:\\LDPlayer", r"C:\\Program Files\\LDPlayer", r"C:\\Program Files\\dnplayerext2"):
        candidates.append(str(Path(base) / "adb.exe"))
        candidates.append(str(Path(base) / "adb"))
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate))
    return explicit_path or os.environ.get("LDMANAGER_ADB_PATH") or "adb"


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
    """Result of a single-serial, text-output ADB command invocation."""

    serial: str
    args: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


@dataclass(frozen=True)
class AdbBinaryResult:
    """Result of a single-serial ADB command whose stdout is raw bytes.

    Used for screenshot capture (``exec-out screencap -p``), where the
    output must never be decoded as text (that can corrupt binary PNG
    data, e.g. via newline translation).
    """

    serial: str
    args: tuple[str, ...]
    returncode: int
    stdout_bytes: bytes
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


class AdbRunner(Protocol):
    """Minimal interface an ADB runner must satisfy.

    Deliberately just three methods, so a fake test double is trivial to
    write (see ``tests/fakes.py``) and any real implementation stays
    swappable/injectable.
    """

    def list_devices(self) -> str:
        """Return the raw stdout of an `adb devices`-equivalent call."""
        ...

    def run(self, serial: str, args: Sequence[str]) -> AdbCommandResult:
        """Run a text-output command scoped to exactly one device serial."""
        ...

    def capture_binary(self, serial: str, args: Sequence[str]) -> AdbBinaryResult:
        """Run a binary-output command (e.g. a screenshot capture)
        scoped to exactly one device serial."""
        ...


def validate_serial(serial: str) -> None:
    """Reject anything but a genuine, single-token ADB serial.

    Shared by :func:`build_adb_command` and every module (``screenshot.py``,
    ``guarded_touch.py``) that must guarantee a capture/touch is scoped to
    exactly one explicit, nonblank device before doing anything else.
    """

    if not serial or any(ch.isspace() for ch in serial):
        raise ValueError(f"Invalid ADB serial: {serial!r}")


def build_adb_command(adb_path: str, serial: str, args: Sequence[str]) -> list[str]:
    """Build an argv list scoped to exactly one ``serial``.

    Rejects an empty/whitespace-containing serial outright (a valid ADB
    serial never contains whitespace) rather than constructing a command
    that could end up targeting the wrong — or no specific — device.
    """

    validate_serial(serial)
    return [adb_path, "-s", serial, *args]


class SubprocessAdbRunner:
    """Real ADB runner: shells out to the `adb` executable.

    The only place a real process is spawned. ``run`` always requires an
    explicit serial (via :func:`build_adb_command`) — there is no
    "current device" fallback.
    """

    def __init__(self, adb_path: str | None = None, timeout: float = 15.0, logger=None, metrics=None) -> None:
        self.adb_path = resolve_adb_path(adb_path)
        self.timeout = timeout
        self._logger = logger
        self.metrics = metrics

    def record_process_start(self):
        if self.metrics is not None:
            self.metrics.add("adb_process_starts")

    def set_adb_path(self, adb_path: str | None) -> None:
        """Re-resolve and update the ADB executable path at runtime
        (ADB-PATH-001) -- e.g. right after the user Saves a new path
        from the GUI, with no app restart required. Goes through the
        same :func:`resolve_adb_path` candidate order as construction.
        """

        self.adb_path = resolve_adb_path(adb_path)

    def list_devices(self) -> str:
        if self._logger:
            self._logger.info("adb devices via %s", self.adb_path)
        if self.metrics is not None:
            self.metrics.add("adb_discovery_calls")
        self.record_process_start()
        completed = subprocess.run(
            [self.adb_path, "devices"],
            capture_output=True,
            text=True,
            timeout=self.timeout,
            check=False,
            **_NO_CONSOLE_WINDOW_KWARGS,
        )
        return completed.stdout

    def run(self, serial: str, args: Sequence[str]) -> AdbCommandResult:
        full_args = build_adb_command(self.adb_path, serial, args)
        self.record_process_start()
        if self._logger:
            self._logger.info("adb command serial=%s args=%s", serial, list(args))
        completed = subprocess.run(
            full_args,
            capture_output=True,
            text=True,
            timeout=self.timeout,
            check=False,
            **_NO_CONSOLE_WINDOW_KWARGS,
        )
        result = AdbCommandResult(
            serial=serial,
            args=tuple(args),
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
        if self._logger:
            self._logger.info("adb result serial=%s rc=%s", serial, result.returncode)
        return result

    def capture_binary(self, serial: str, args: Sequence[str]) -> AdbBinaryResult:
        full_args = build_adb_command(self.adb_path, serial, args)
        self.record_process_start()
        if self.metrics is not None:
            self.metrics.record_capture()
        if self._logger:
            self._logger.info("adb binary command serial=%s args=%s", serial, list(args))
        completed = subprocess.run(
            full_args,
            capture_output=True,
            text=False,
            timeout=self.timeout,
            check=False,
            **_NO_CONSOLE_WINDOW_KWARGS,
        )
        stderr_text = completed.stderr.decode("utf-8", errors="replace") if completed.stderr else ""
        result = AdbBinaryResult(serial, tuple(args), completed.returncode, completed.stdout or b"", stderr_text)
        if self._logger:
            self._logger.info("adb binary result serial=%s rc=%s bytes=%s", serial, result.returncode, len(result.stdout_bytes))
        return result


class PersistentTapAdbRunner:
    """Keeps one ``adb -s SERIAL shell`` process per account for taps.

    Only the known ``shell input tap X Y`` argv form is sent through a
    persistent shell.  Discovery, screenshots and unrelated commands retain
    the proven subprocess implementation.  Each session has a lock and a
    completion marker, so commands from different LD serials never share
    stdin/stdout or become interleaved.
    """

    def __init__(self, inner: SubprocessAdbRunner, timeout: float = 5.0) -> None:
        self._inner = inner
        self.timeout = timeout
        self._sessions: dict[str, tuple[subprocess.Popen, queue.Queue[str], threading.Lock]] = {}
        self._lock = threading.Lock()

    def _session(self, serial: str):
        with self._lock:
            existing = self._sessions.get(serial)
            if existing is not None and existing[0].poll() is None:
                return existing
            if existing is not None:
                self._sessions.pop(serial, None)
            self._inner.record_process_start()
            process = subprocess.Popen(
                [self._inner.adb_path, "-s", serial, "shell"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                text=True, bufsize=1, **_NO_CONSOLE_WINDOW_KWARGS,
            )
            lines: queue.Queue[str] = queue.Queue()
            def reader() -> None:
                assert process.stdout is not None
                for line in process.stdout:
                    lines.put(line.rstrip("\r\n"))
            threading.Thread(target=reader, name=f"adb-shell-reader-{serial}", daemon=True).start()
            session = (process, lines, threading.Lock())
            self._sessions[serial] = session
            return session

    def list_devices(self) -> str:
        return self._inner.list_devices()

    def capture_binary(self, serial: str, args: Sequence[str]) -> AdbBinaryResult:
        return self._inner.capture_binary(serial, args)

    def set_adb_path(self, adb_path: str | None) -> None:
        self.close()
        self._inner.set_adb_path(adb_path)

    @property
    def adb_path(self) -> str:
        return self._inner.adb_path

    def run(self, serial: str, args: Sequence[str]) -> AdbCommandResult:
        validate_serial(serial)
        parts = tuple(args)
        if len(parts) != 5 or parts[:3] != ("shell", "input", "tap") or not parts[3].isdigit() or not parts[4].isdigit():
            return self._inner.run(serial, args)
        process, lines, session_lock = self._session(serial)
        marker = f"__LDMANAGER_DONE_{uuid.uuid4().hex}__"
        with session_lock:
            if process.poll() is not None or process.stdin is None:
                self.close_serial(serial)
                return AdbCommandResult(serial, parts, 1, "", "Persistent ADB shell is not running.")
            try:
                process.stdin.write(f"input tap {parts[3]} {parts[4]}; echo {marker}:$?\n")
                process.stdin.flush()
                deadline = time.monotonic() + self.timeout
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        self.close_serial(serial)
                        return AdbCommandResult(serial, parts, 1, "", "Persistent ADB shell tap timed out.")
                    try:
                        line = lines.get(timeout=remaining)
                    except queue.Empty:
                        continue
                    if line.startswith(marker + ":"):
                        code = int(line[len(marker) + 1:])
                        return AdbCommandResult(serial, parts, code, "", "" if code == 0 else "Android input tap failed")
            except (BrokenPipeError, OSError) as exc:
                self.close_serial(serial)
                return AdbCommandResult(serial, parts, 1, "", f"Persistent ADB shell failed: {exc}")

    def close_serial(self, serial: str) -> None:
        with self._lock:
            session = self._sessions.pop(serial, None)
        if session is not None and session[0].poll() is None:
            session[0].terminate()
            try:
                session[0].wait(timeout=2)
            except subprocess.TimeoutExpired:
                session[0].kill()
                session[0].wait(timeout=2)
        if session is not None:
            for stream in (session[0].stdin, getattr(session[0], "stdout", None)):
                if stream is not None:
                    stream.close()

    def close(self) -> None:
        with self._lock:
            serials = tuple(self._sessions)
        for serial in serials:
            self.close_serial(serial)

class InputGateAdbRunner:
    """Production runner wrapper: capture/discovery always work; taps require
    explicit live-mode activation.  It never substitutes a fake device."""

    def __init__(self, inner: AdbRunner, live_enabled: bool = False) -> None:
        import threading
        self._inner = inner
        self._live = threading.Event()
        if live_enabled:
            self._live.set()

    @property
    def live_enabled(self) -> bool:
        return self._live.is_set()

    def set_live_enabled(self, enabled: bool) -> None:
        (self._live.set if enabled else self._live.clear)()

    def set_adb_path(self, adb_path: str | None) -> None:
        """Pass-through to the inner runner's ``set_adb_path`` (ADB-PATH-001),
        if it has one -- a plain fake/test double without this method is
        silently a no-op, never an error."""

        inner_setter = getattr(self._inner, "set_adb_path", None)
        if inner_setter is not None:
            inner_setter(adb_path)

    @property
    def adb_path(self) -> str | None:
        """The inner runner's currently effective ADB path, if it
        exposes one -- for GUI display only (ADB-PATH-001)."""

        return getattr(self._inner, "adb_path", None)

    def list_devices(self) -> str:
        return self._inner.list_devices()

    def capture_binary(self, serial: str, args: Sequence[str]) -> AdbBinaryResult:
        return self._inner.capture_binary(serial, args)

    def run(self, serial: str, args: Sequence[str]) -> AdbCommandResult:
        validate_serial(serial)
        if not self.live_enabled:
            return AdbCommandResult(serial, tuple(args), 125, "", "Live input is disabled (safe mode).")
        return self._inner.run(serial, args)


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
