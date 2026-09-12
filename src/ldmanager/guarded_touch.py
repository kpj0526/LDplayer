"""Guarded relative-touch foundation (TP-003).

This is a strict, bounded state machine — **not** game automation:

    fresh capture -> caller-supplied precondition hook
        -> (only if accepted) exactly one serial-scoped touch
        -> fresh capture -> caller-supplied postcondition hook

A false/low-confidence precondition, a hook raising, an invalid/failed
capture, or a bounded-retry timeout at any stage issues **no further
input** and returns an account-local, structured
:class:`GuardedTouchResult` instead of raising or guessing. At most one
touch command is ever sent per call, regardless of how many capture/
verification retries happen before or after it.

No OCR, no template/image matching, no mission/game logic, no GUI, no
login/reconnect flow, no web DOM, and no global desktop mouse control
exists here or anywhere in this project — the "touch" is exactly one
`adb -s <serial> shell input tap <x> <y>` invocation, built from a
validated :class:`~ldmanager.coordinates.RelativeCoordinate` and scoped
to exactly one explicit, nonblank serial.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Sequence

from .adb import AdbRunner, validate_serial
from .coordinates import RelativeCoordinate, ScreenSize, build_tap_args
from .models import AccountId
from .screenshot import DEFAULT_CAPTURE_ARGS, capture_screenshot

#: A hook receives the freshly captured, already-validated PNG bytes and
#: returns True to proceed/accept, False to reject. Any exception it
#: raises is treated the same as an explicit rejection (with its own
#: distinct outcome so the two are never confused in a diagnostic).
VerificationHook = Callable[[bytes], bool]


class TouchOutcome(str, Enum):
    SUCCESS = "success"
    CAPTURE_FAILED = "capture_failed"  # pre-touch capture never became valid
    PRECONDITION_REJECTED = "precondition_rejected"
    PRECONDITION_ERROR = "precondition_error"
    TOUCH_FAILED = "touch_failed"  # the tap command itself returned nonzero
    POST_CAPTURE_FAILED = "post_capture_failed"  # post-touch capture never became valid
    POSTCONDITION_REJECTED = "postcondition_rejected"  # bounded retries exhausted
    POSTCONDITION_ERROR = "postcondition_error"


@dataclass(frozen=True)
class GuardedTouchResult:
    """Account-local, structured outcome of one guarded-touch attempt.

    ``touched`` is true iff a touch command was actually sent — it is
    independent of whether that touch (or anything after it) ultimately
    succeeded, so a caller can always tell "did we physically touch the
    screen" apart from "did we get a verified success".
    """

    account_id: AccountId
    serial: str
    outcome: TouchOutcome
    touched: bool
    capture_attempts: int
    verify_attempts: int
    detail: str

    @property
    def ok(self) -> bool:
        return self.outcome is TouchOutcome.SUCCESS


def _no_sleep(_seconds: float) -> None:
    """Default no-op sleep so a bounded loop never actually blocks unless
    a caller explicitly wants pacing (e.g. the real runtime, not tests)."""


def perform_guarded_touch(
    *,
    account_id: AccountId,
    serial: str,
    runner: AdbRunner,
    screen_size: ScreenSize,
    point: RelativeCoordinate,
    precondition: VerificationHook,
    postcondition: VerificationHook,
    capture_args: Sequence[str] = DEFAULT_CAPTURE_ARGS,
    max_capture_attempts: int = 3,
    max_postcondition_attempts: int = 3,
    retry_delay_seconds: float = 0.0,
    sleep_fn: Callable[[float], None] = _no_sleep,
) -> GuardedTouchResult:
    """Run one guarded touch for ``account_id`` on exactly ``serial``.

    ``point``/``screen_size`` are already-validated
    (:class:`~ldmanager.coordinates.RelativeCoordinate`/
    :class:`~ldmanager.coordinates.ScreenSize` raise at construction for
    anything out of range), so this function does not re-derive or
    guess a coordinate — it only ever converts the one point it was
    given into device pixels for exactly one tap.

    ``max_capture_attempts``/``max_postcondition_attempts`` bound every
    retry loop; ``sleep_fn`` (default: a no-op, so tests never actually
    block) is called between retries so a real caller can inject a
    paced ``time.sleep``.
    """

    validate_serial(serial)

    # 1. Fresh pre-touch capture, bounded retries. No touch is possible
    #    until this yields a validated screenshot.
    pre_capture = None
    capture_attempts = 0
    for attempt in range(1, max_capture_attempts + 1):
        capture_attempts = attempt
        pre_capture = capture_screenshot(runner, serial, capture_args)
        if pre_capture.ok:
            break
        if attempt < max_capture_attempts:
            sleep_fn(retry_delay_seconds)

    if pre_capture is None or not pre_capture.ok:
        detail = pre_capture.detail if pre_capture else "no capture attempted"
        return GuardedTouchResult(
            account_id=account_id,
            serial=serial,
            outcome=TouchOutcome.CAPTURE_FAILED,
            touched=False,
            capture_attempts=capture_attempts,
            verify_attempts=0,
            detail=f"Pre-touch capture never succeeded after {capture_attempts} "
            f"attempt(s): {detail}",
        )

    # 2. Precondition hook. False/raising -> zero touches, controlled result.
    try:
        precondition_ok = bool(precondition(pre_capture.image_bytes))
    except Exception as exc:
        return GuardedTouchResult(
            account_id=account_id,
            serial=serial,
            outcome=TouchOutcome.PRECONDITION_ERROR,
            touched=False,
            capture_attempts=capture_attempts,
            verify_attempts=0,
            detail=f"Precondition hook raised {type(exc).__name__}: {exc}",
        )

    if not precondition_ok:
        return GuardedTouchResult(
            account_id=account_id,
            serial=serial,
            outcome=TouchOutcome.PRECONDITION_REJECTED,
            touched=False,
            capture_attempts=capture_attempts,
            verify_attempts=0,
            detail="Precondition hook rejected the pre-touch capture; no touch sent.",
        )

    # 3. Exactly one serial-scoped touch.
    tap_args = build_tap_args(screen_size, point)
    touch_result = runner.run(serial, tap_args)
    if not touch_result.ok:
        return GuardedTouchResult(
            account_id=account_id,
            serial=serial,
            outcome=TouchOutcome.TOUCH_FAILED,
            touched=True,
            capture_attempts=capture_attempts,
            verify_attempts=0,
            detail=f"Touch command returned nonzero exit code {touch_result.returncode}; "
            "device state is uncertain, no repeat touch was sent.",
        )

    # 4. Fresh post-touch capture + postcondition, bounded retries. The
    #    touch above is never repeated no matter how this loop ends.
    post_capture = None
    verify_attempts = 0
    for attempt in range(1, max_postcondition_attempts + 1):
        verify_attempts = attempt
        post_capture = capture_screenshot(runner, serial, capture_args)

        if not post_capture.ok:
            if attempt < max_postcondition_attempts:
                sleep_fn(retry_delay_seconds)
            continue

        try:
            verified = bool(postcondition(post_capture.image_bytes))
        except Exception as exc:
            return GuardedTouchResult(
                account_id=account_id,
                serial=serial,
                outcome=TouchOutcome.POSTCONDITION_ERROR,
                touched=True,
                capture_attempts=capture_attempts,
                verify_attempts=verify_attempts,
                detail=f"Postcondition hook raised {type(exc).__name__}: {exc}",
            )

        if verified:
            return GuardedTouchResult(
                account_id=account_id,
                serial=serial,
                outcome=TouchOutcome.SUCCESS,
                touched=True,
                capture_attempts=capture_attempts,
                verify_attempts=verify_attempts,
                detail="Touch verified by postcondition.",
            )

        if attempt < max_postcondition_attempts:
            sleep_fn(retry_delay_seconds)

    if post_capture is None or not post_capture.ok:
        return GuardedTouchResult(
            account_id=account_id,
            serial=serial,
            outcome=TouchOutcome.POST_CAPTURE_FAILED,
            touched=True,
            capture_attempts=capture_attempts,
            verify_attempts=verify_attempts,
            detail=f"Post-touch capture never succeeded after {verify_attempts} "
            "attempt(s); no repeat touch was sent.",
        )

    return GuardedTouchResult(
        account_id=account_id,
        serial=serial,
        outcome=TouchOutcome.POSTCONDITION_REJECTED,
        touched=True,
        capture_attempts=capture_attempts,
        verify_attempts=verify_attempts,
        detail=f"Postcondition not satisfied within {verify_attempts} bounded "
        "attempt(s); no repeat touch was sent.",
    )
