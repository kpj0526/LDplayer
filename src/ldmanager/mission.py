"""Five-slot mission cycle state machine (MVP-001).

A *mock/configurable* control-flow skeleton — not game automation. It
drives the existing single-serial, bounded, cancellable guarded-touch/
screenshot/recognition primitives through the cycle described by the
Manager MVP packet:

    for each of 5 slots:
        capture -> recognize target phrase
        -> if missing: reroll (bounded) and retry
        -> if found: keep it, move to the next slot
    after all 5 slots: 200-kill check (bounded polling, no touch)
    claim reward (guarded touch, verified)
    reset (guarded touch, verified)
    -> caller repeats by calling run_one_cycle() again

Every capture/touch is scoped to exactly one explicit serial. Every
retry loop (reroll, kill-check, claim/reset verification) is bounded by
``MissionConfig``. ``should_stop()`` is checked before every capture and
before every touch, so a cancellation request issues no further input.
Recognition never fabricates a match — the state machine only reacts to
whatever the injected :class:`~ldmanager.recognition.Recognizer` reports,
never assumes success on its own. No OCR/template matching, no mission/
game "intelligence", and no login/reconnect logic is implemented here.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from .adb import AdbRunner
from .coordinates import build_tap_args
from .guarded_touch import perform_guarded_touch
from .mission_config import MissionConfig
from .models import AccountId
from .recognition import Recognizer
from .screenshot import capture_screenshot

ShouldStop = Callable[[], bool]


def _default_should_stop() -> bool:
    return False


class MissionOutcome(str, Enum):
    COMPLETED = "completed"
    STOPPED = "stopped"
    CAPTURE_UNAVAILABLE = "capture_unavailable"
    SLOT_RECOGNITION_FAILED = "slot_recognition_failed"
    KILL_CHECK_FAILED = "kill_check_failed"
    CLAIM_FAILED = "claim_failed"
    RESET_FAILED = "reset_failed"


@dataclass(frozen=True)
class SlotOutcome:
    slot_index: int
    matched: bool
    attempts: int
    detail: str


@dataclass(frozen=True)
class MissionCycleResult:
    outcome: MissionOutcome
    slots: tuple[SlotOutcome, ...]
    detail: str

    @property
    def ok(self) -> bool:
        return self.outcome is MissionOutcome.COMPLETED


def run_one_cycle(
    *,
    account_id: AccountId,
    serial: str,
    runner: AdbRunner,
    recognizer: Recognizer,
    config: MissionConfig,
    should_stop: ShouldStop = _default_should_stop,
    on_slot_start: Optional[Callable[[int], None]] = None,
) -> MissionCycleResult:
    """Run exactly one mission cycle for one account/serial.

    Returns a structured :class:`MissionCycleResult` — never raises for
    an expected runtime condition (capture failure, recognition miss,
    exhausted retries, cancellation); the caller (a worker loop) decides
    whether/when to call this again.
    """

    slot_results: list[SlotOutcome] = []

    for index, roi in enumerate(config.slot_rois, start=1):
        if should_stop():
            return MissionCycleResult(
                MissionOutcome.STOPPED, tuple(slot_results),
                f"Stopped before slot {index}.",
            )
        if on_slot_start:
            on_slot_start(index)

        matched = False
        attempts = 0
        detail = ""

        for attempt in range(1, config.max_reroll_attempts + 1):
            attempts = attempt

            if should_stop():
                return MissionCycleResult(
                    MissionOutcome.STOPPED, tuple(slot_results),
                    f"Stopped mid-slot {index} (attempt {attempt}).",
                )

            capture = capture_screenshot(runner, serial, config.capture_args)
            if not capture.ok:
                detail = f"capture failed: {capture.detail}"
                if attempt < config.max_reroll_attempts:
                    continue
                return MissionCycleResult(
                    MissionOutcome.CAPTURE_UNAVAILABLE, tuple(slot_results),
                    f"Slot {index}: {detail}",
                )

            result = recognizer.recognize(
                capture.image_bytes, roi, config.target_label, config.threshold
            )
            detail = result.detail
            if result.matched:
                matched = True
                break

            if attempt < config.max_reroll_attempts:
                if should_stop():
                    return MissionCycleResult(
                        MissionOutcome.STOPPED, tuple(slot_results),
                        f"Stopped before reroll at slot {index}.",
                    )
                reroll = runner.run(serial, build_tap_args(config.screen_size, config.reroll_point))
                if not reroll.ok:
                    slot_results.append(SlotOutcome(index, False, attempts, detail))
                    return MissionCycleResult(
                        MissionOutcome.SLOT_RECOGNITION_FAILED, tuple(slot_results),
                        f"Slot {index}: reroll touch failed (rc={reroll.returncode}).",
                    )

        slot_results.append(SlotOutcome(index, matched, attempts, detail))
        if not matched:
            return MissionCycleResult(
                MissionOutcome.SLOT_RECOGNITION_FAILED, tuple(slot_results),
                f"Slot {index}: target not found within "
                f"{config.max_reroll_attempts} attempt(s); no further input sent.",
            )

    # --- 200-kill check: bounded polling, no touch involved. -------------
    if should_stop():
        return MissionCycleResult(
            MissionOutcome.STOPPED, tuple(slot_results), "Stopped before kill check."
        )

    kill_check_ok = False
    kill_detail = ""
    for _attempt in range(1, config.max_kill_check_attempts + 1):
        if should_stop():
            return MissionCycleResult(
                MissionOutcome.STOPPED, tuple(slot_results), "Stopped during kill check."
            )
        capture = capture_screenshot(runner, serial, config.capture_args)
        if not capture.ok:
            kill_detail = f"capture failed: {capture.detail}"
            continue
        result = recognizer.recognize(
            capture.image_bytes, config.kill_check_roi, config.kill_check_label, config.threshold
        )
        kill_detail = result.detail
        if result.matched:
            kill_check_ok = True
            break

    if not kill_check_ok:
        return MissionCycleResult(
            MissionOutcome.KILL_CHECK_FAILED, tuple(slot_results),
            f"200-kill check not confirmed within "
            f"{config.max_kill_check_attempts} attempt(s): {kill_detail}",
        )

    # --- Claim reward: reuse the guarded-touch contract. ------------------
    if should_stop():
        return MissionCycleResult(
            MissionOutcome.STOPPED, tuple(slot_results), "Stopped before claim."
        )

    claim_result = perform_guarded_touch(
        account_id=account_id,
        serial=serial,
        runner=runner,
        screen_size=config.screen_size,
        point=config.claim_point,
        precondition=lambda _image_bytes: True,  # kill-check already confirmed readiness
        postcondition=lambda image_bytes: recognizer.recognize(
            image_bytes, config.claimed_roi, config.claimed_label, config.threshold
        ).matched,
        capture_args=config.capture_args,
        max_capture_attempts=config.max_capture_attempts,
        max_postcondition_attempts=config.max_claim_verify_attempts,
        retry_delay_seconds=config.retry_delay_seconds,
    )
    if not claim_result.ok:
        return MissionCycleResult(
            MissionOutcome.CLAIM_FAILED, tuple(slot_results),
            f"Claim step: {claim_result.detail}",
        )

    # --- Reset: reuse the guarded-touch contract again. -------------------
    if should_stop():
        return MissionCycleResult(
            MissionOutcome.STOPPED, tuple(slot_results), "Stopped before reset."
        )

    reset_result = perform_guarded_touch(
        account_id=account_id,
        serial=serial,
        runner=runner,
        screen_size=config.screen_size,
        point=config.reset_point,
        precondition=lambda _image_bytes: True,
        postcondition=lambda image_bytes: recognizer.recognize(
            image_bytes, config.ready_roi, config.ready_label, config.threshold
        ).matched,
        capture_args=config.capture_args,
        max_capture_attempts=config.max_capture_attempts,
        max_postcondition_attempts=config.max_reset_verify_attempts,
        retry_delay_seconds=config.retry_delay_seconds,
    )
    if not reset_result.ok:
        return MissionCycleResult(
            MissionOutcome.RESET_FAILED, tuple(slot_results),
            f"Reset step: {reset_result.detail}",
        )

    return MissionCycleResult(
        MissionOutcome.COMPLETED, tuple(slot_results),
        "Cycle completed (slots + kill-check + claim + reset).",
    )
