"""Per-instance ADB screenshot capture with safe byte validation (TP-003).

Capture only: no OCR, no template matching, no mission/game logic, no
GUI. A capture is always scoped to exactly one explicit, nonblank
serial via the injected :class:`~ldmanager.adb.AdbRunner`. Never reads,
logs, or forwards any credential material.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from .adb import AdbRunner, validate_serial

#: `exec-out` streams raw bytes without the newline/CR translation that
#: `adb shell screencap -p` is prone to on some adb/shell versions.
DEFAULT_CAPTURE_ARGS: tuple[str, ...] = ("exec-out", "screencap", "-p")

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_MIN_PLAUSIBLE_PNG_BYTES = len(_PNG_MAGIC)


class CaptureError(str, Enum):
    NONE = "none"
    RUNNER_FAILED = "runner_failed"  # adb exited with a nonzero returncode
    EMPTY_OUTPUT = "empty_output"  # zero bytes captured
    INVALID_IMAGE_BYTES = "invalid_image_bytes"  # missing/short PNG magic
    EXCEPTION = "exception"  # the runner itself raised


@dataclass(frozen=True)
class ScreenshotCaptureResult:
    """Outcome of one screenshot capture attempt for one serial.

    ``detail`` is a short, secret-free diagnostic string — it never
    contains the image bytes or any credential.
    """

    serial: str
    ok: bool
    image_bytes: bytes
    error: CaptureError
    detail: str


def _looks_like_png(data: bytes) -> bool:
    return len(data) >= _MIN_PLAUSIBLE_PNG_BYTES and data.startswith(_PNG_MAGIC)


def capture_screenshot(
    runner: AdbRunner,
    serial: str,
    capture_args: Sequence[str] = DEFAULT_CAPTURE_ARGS,
) -> ScreenshotCaptureResult:
    """Capture one screenshot from exactly ``serial`` and validate it.

    Never raises for an *expected* runtime failure (nonzero returncode,
    empty output, non-PNG bytes, or the runner itself raising) — each of
    those is reported as a structured ``ok=False`` result instead, so a
    caller (e.g. the guarded-touch state machine) can chain this into a
    bounded retry loop without exception handling of its own.

    A blank/whitespace serial is still rejected immediately via
    :func:`~ldmanager.adb.validate_serial` (``ValueError``), since that
    is a caller/programmer error — not an environmental one — and must
    fail fast before any capture is attempted.
    """

    validate_serial(serial)

    try:
        result = runner.capture_binary(serial, capture_args)
    except Exception as exc:
        return ScreenshotCaptureResult(
            serial=serial,
            ok=False,
            image_bytes=b"",
            error=CaptureError.EXCEPTION,
            detail=f"ADB capture raised {type(exc).__name__}: {exc}",
        )

    if result.returncode != 0:
        return ScreenshotCaptureResult(
            serial=serial,
            ok=False,
            image_bytes=b"",
            error=CaptureError.RUNNER_FAILED,
            detail=f"adb exited with code {result.returncode} during capture.",
        )

    data = result.stdout_bytes
    if not data:
        return ScreenshotCaptureResult(
            serial=serial,
            ok=False,
            image_bytes=b"",
            error=CaptureError.EMPTY_OUTPUT,
            detail="Capture returned zero bytes.",
        )

    if not _looks_like_png(data):
        return ScreenshotCaptureResult(
            serial=serial,
            ok=False,
            image_bytes=b"",
            error=CaptureError.INVALID_IMAGE_BYTES,
            detail="Captured bytes do not look like a valid PNG (bad/missing magic header).",
        )

    return ScreenshotCaptureResult(
        serial=serial,
        ok=True,
        image_bytes=data,
        error=CaptureError.NONE,
        detail="ok",
    )
