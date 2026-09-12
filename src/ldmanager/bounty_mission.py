"""Free regional-bounty five-slot mission cycle (MVP-001-CV).

Models the actual observed free-regional-bounty flow (per Manager's
customer-video extension), as a *mock/configurable* state machine —
still not game automation. Every action follows the same contract:

    capture -> check expected state/condition -> ONE explicit-serial
    guarded relative touch (only if the condition holds) -> capture
    to observe the change

States implemented, in order:

1. For each of 5 slots: select the slot, capture+check whether its
   current mission already satisfies BOTH acceptance conditions
   (target phrase AND quantity == 200). If not, open the refresh
   confirmation popup, verify it **structurally** (two independent,
   cost-INDEPENDENT landmarks — never the displayed refresh cost, which
   varies), confirm only if verified, inspect the new mission, and
   retry (bounded). Move to the next slot only after a verified
   acceptance.
2. After all 5 slots: poll (bounded) for kill-progress completion —
   either the "200/200" counter or an explicit complete-state badge.
   **0-199/200 never taps select/complete/claim** — this function
   simply reports "not yet" and returns; it is the caller's job to try
   again later (real kill progress advances from real gameplay, not
   from anything this code does).
3. Only once eligible: select the completed mission, tap complete,
   verify the reward screen, claim, verify the result screen, close
   it, verify the mission list is showing again.
4. Re-refresh + re-accept each slot (reusing step 1's per-slot helper)
   so the caller can repeat the whole cycle.

``should_stop()`` is checked before every capture and before every
touch — a cancellation request issues no further input. Every retry
loop is bounded by :class:`~ldmanager.bounty_config.BountyMissionConfig`.
Recognition never fabricates a match; acceptance always requires two
independent recognizer calls to agree (never "one OCR output alone").
No OCR/template-matching implementation, no mission "intelligence",
and no login/reconnect logic exists here — see
``ldmanager.recognition.PlaceholderRecognizer``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from .adb import AdbRunner
from .bounty_config import BountyMissionConfig
from .coordinates import build_tap_args
from .models import AccountId
from .recognition import Recognizer, RecognitionResult
from .screenshot import capture_screenshot

ShouldStop = Callable[[], bool]


def _default_should_stop() -> bool:
    return False


class BountyOutcome(str, Enum):
    COMPLETED_CYCLE = "completed_cycle"  # full: 5 accepted -> claimed -> re-accepted, ready to repeat
    STOPPED = "stopped"
    CAPTURE_UNAVAILABLE = "capture_unavailable"
    SLOT_ACCEPT_FAILED = "slot_accept_failed"  # bounded refresh exhausted without a both-conditions match
    REFRESH_POPUP_NOT_VERIFIED = "refresh_popup_not_verified"  # structural check never confirmed -> never confirmed blindly
    KILL_PROGRESS_NOT_COMPLETE = "kill_progress_not_complete"  # 0-199/200: informational, not an error
    REWARD_VERIFY_FAILED = "reward_verify_failed"
    RESULT_VERIFY_FAILED = "result_verify_failed"
    MISSION_LIST_VERIFY_FAILED = "mission_list_verify_failed"
    RE_ACCEPT_FAILED = "re_accept_failed"


@dataclass(frozen=True)
class SlotOutcome:
    slot_index: int
    accepted: bool
    refresh_attempts: int
    detail: str


@dataclass(frozen=True)
class BountyCycleResult:
    outcome: BountyOutcome
    slots: tuple[SlotOutcome, ...]
    detail: str

    @property
    def ok(self) -> bool:
        return self.outcome is BountyOutcome.COMPLETED_CYCLE


def _recognize(runner, serial, config, recognizer, roi, label) -> Optional[RecognitionResult]:
    """Capture once and recognize ``roi``/``label``; ``None`` means the
    capture itself failed (never means "recognized but no match")."""

    capture = capture_screenshot(runner, serial, config.capture_args)
    if not capture.ok:
        return None
    return recognizer.recognize(capture.image_bytes, roi, label, config.threshold)


def _mission_is_acceptable(runner, serial, config, recognizer) -> Optional[bool]:
    """Both the phrase AND the quantity must independently match.

    Returns ``None`` on capture failure (distinct from ``False``, which
    means "captured fine, but not both conditions held").
    """

    phrase = _recognize(runner, serial, config, recognizer, config.mission_phrase_roi, config.mission_phrase_label)
    if phrase is None:
        return None
    quantity = _recognize(runner, serial, config, recognizer, config.mission_quantity_roi, config.mission_quantity_label)
    if quantity is None:
        return None
    return phrase.matched and quantity.matched


def _verify_refresh_popup(runner, serial, config, recognizer) -> Optional[bool]:
    """Structural popup check: two independent, cost-independent
    landmarks must BOTH match. Returns ``None`` on capture failure."""

    anchor = _recognize(
        runner, serial, config, recognizer,
        config.refresh_popup_anchor_roi, config.refresh_popup_anchor_label,
    )
    if anchor is None:
        return None
    title = _recognize(
        runner, serial, config, recognizer,
        config.refresh_popup_title_roi, config.refresh_popup_title_label,
    )
    if title is None:
        return None
    return anchor.matched and title.matched


def _accept_or_refresh_slot(
    *, slot_index: int, serial: str, runner: AdbRunner, recognizer: Recognizer,
    config: BountyMissionConfig, should_stop: ShouldStop,
) -> "tuple[SlotOutcome | None, BountyCycleResult | None]":
    """Select+check one slot; refresh (bounded) until an acceptable
    mission is found. Returns ``(SlotOutcome, None)`` on a definitive
    per-slot result, or ``(None, BountyCycleResult)`` if the whole cycle
    must stop/abort right here (cancellation or unrecoverable failure).
    """

    if should_stop():
        return None, BountyCycleResult(
            BountyOutcome.STOPPED, (), f"Stopped before slot {slot_index}."
        )

    select = runner.run(serial, build_tap_args(config.screen_size, config.slot_select_points[slot_index - 1]))
    if not select.ok:
        return None, BountyCycleResult(
            BountyOutcome.CAPTURE_UNAVAILABLE, (),
            f"Slot {slot_index}: select tap failed (rc={select.returncode}).",
        )

    if should_stop():
        return None, BountyCycleResult(
            BountyOutcome.STOPPED, (), f"Stopped mid-slot {slot_index} (after select)."
        )

    already_ok = _mission_is_acceptable(runner, serial, config, recognizer)
    if already_ok is None:
        return None, BountyCycleResult(
            BountyOutcome.CAPTURE_UNAVAILABLE, (), f"Slot {slot_index}: capture failed while checking mission."
        )
    if already_ok:
        return SlotOutcome(slot_index, True, 0, "Already acceptable; no refresh needed."), None

    detail = ""
    for attempt in range(1, config.max_refresh_attempts + 1):
        if should_stop():
            return None, BountyCycleResult(
                BountyOutcome.STOPPED, (), f"Stopped mid-slot {slot_index} (refresh attempt {attempt})."
            )

        open_popup = runner.run(serial, build_tap_args(config.screen_size, config.refresh_button_point))
        if not open_popup.ok:
            return None, BountyCycleResult(
                BountyOutcome.CAPTURE_UNAVAILABLE, (),
                f"Slot {slot_index}: refresh-open tap failed (rc={open_popup.returncode}).",
            )

        if should_stop():
            return None, BountyCycleResult(
                BountyOutcome.STOPPED, (), f"Stopped mid-slot {slot_index} (popup open)."
            )

        popup_verified = None
        for popup_attempt in range(1, config.max_popup_verify_attempts + 1):
            if should_stop():
                return None, BountyCycleResult(
                    BountyOutcome.STOPPED, (), f"Stopped mid-slot {slot_index} (popup verify)."
                )
            popup_verified = _verify_refresh_popup(runner, serial, config, recognizer)
            if popup_verified:
                break
            if popup_attempt < config.max_popup_verify_attempts:
                continue

        if not popup_verified:
            # Never confirm blindly: structural verification failed --
            # do not tap confirm.
            return None, BountyCycleResult(
                BountyOutcome.REFRESH_POPUP_NOT_VERIFIED, (),
                f"Slot {slot_index}: refresh popup never verified structurally "
                f"within {config.max_popup_verify_attempts} attempt(s); confirm not sent.",
            )

        if should_stop():
            return None, BountyCycleResult(
                BountyOutcome.STOPPED, (), f"Stopped mid-slot {slot_index} (before confirm)."
            )

        confirm = runner.run(serial, build_tap_args(config.screen_size, config.refresh_confirm_point))
        if not confirm.ok:
            return None, BountyCycleResult(
                BountyOutcome.CAPTURE_UNAVAILABLE, (),
                f"Slot {slot_index}: refresh-confirm tap failed (rc={confirm.returncode}).",
            )

        if should_stop():
            return None, BountyCycleResult(
                BountyOutcome.STOPPED, (), f"Stopped mid-slot {slot_index} (after confirm)."
            )

        acceptable = _mission_is_acceptable(runner, serial, config, recognizer)
        if acceptable is None:
            return None, BountyCycleResult(
                BountyOutcome.CAPTURE_UNAVAILABLE, (),
                f"Slot {slot_index}: capture failed while inspecting refreshed mission.",
            )
        if acceptable:
            return SlotOutcome(slot_index, True, attempt, "Accepted after refresh."), None
        detail = f"attempt {attempt}: phrase/quantity not both matched"

    return SlotOutcome(slot_index, False, config.max_refresh_attempts, detail), None


def run_one_cycle(
    *,
    account_id: AccountId,
    serial: str,
    runner: AdbRunner,
    recognizer: Recognizer,
    config: BountyMissionConfig,
    should_stop: ShouldStop = _default_should_stop,
    on_phase: Optional[Callable[[str], None]] = None,
) -> BountyCycleResult:
    """Run exactly one bounty cycle for one account/serial.

    Returns a structured :class:`BountyCycleResult` — never raises for
    an expected runtime condition. The caller (a worker loop) decides
    whether/when to call this again.
    """

    del account_id  # identity carried by the caller; not needed internally
    slot_outcomes: list[SlotOutcome] = []

    for slot_index in range(1, config.slot_count + 1):
        if on_phase:
            on_phase(f"slot {slot_index}: select/check")
        slot_outcome, abort = _accept_or_refresh_slot(
            slot_index=slot_index, serial=serial, runner=runner, recognizer=recognizer,
            config=config, should_stop=should_stop,
        )
        if abort is not None:
            return BountyCycleResult(abort.outcome, tuple(slot_outcomes), abort.detail)

        slot_outcomes.append(slot_outcome)
        if not slot_outcome.accepted:
            return BountyCycleResult(
                BountyOutcome.SLOT_ACCEPT_FAILED, tuple(slot_outcomes),
                f"Slot {slot_index}: no acceptable target within "
                f"{config.max_refresh_attempts} refresh(es).",
            )

    # --- Kill-progress: bounded polling, 0-199/200 never touches anything. ---
    if on_phase:
        on_phase("kill progress: observing")
    if should_stop():
        return BountyCycleResult(BountyOutcome.STOPPED, tuple(slot_outcomes), "Stopped before kill-progress check.")

    eligible = False
    progress_detail = ""
    for _attempt in range(1, config.max_kill_progress_poll_attempts + 1):
        if should_stop():
            return BountyCycleResult(BountyOutcome.STOPPED, tuple(slot_outcomes), "Stopped during kill-progress check.")
        progress = _recognize(runner, serial, config, recognizer, config.kill_progress_roi, config.kill_progress_complete_label)
        if progress is not None and progress.matched:
            eligible = True
            break
        complete_badge = _recognize(runner, serial, config, recognizer, config.complete_state_roi, config.complete_state_label)
        if complete_badge is not None and complete_badge.matched:
            eligible = True
            break
        progress_detail = "kill progress not yet complete"

    if not eligible:
        return BountyCycleResult(
            BountyOutcome.KILL_PROGRESS_NOT_COMPLETE, tuple(slot_outcomes),
            f"0-199/200: not eligible yet ({progress_detail}); no complete/reward action taken.",
        )

    # --- Complete -> reward -> claim -> result -> close -> mission list. ---
    if on_phase:
        on_phase("completing: select + complete")
    if should_stop():
        return BountyCycleResult(BountyOutcome.STOPPED, tuple(slot_outcomes), "Stopped before completing.")

    select_complete = runner.run(serial, build_tap_args(config.screen_size, config.select_complete_point))
    if not select_complete.ok:
        return BountyCycleResult(BountyOutcome.CAPTURE_UNAVAILABLE, tuple(slot_outcomes), "Select-complete tap failed.")

    if should_stop():
        return BountyCycleResult(BountyOutcome.STOPPED, tuple(slot_outcomes), "Stopped before complete button.")

    complete_tap = runner.run(serial, build_tap_args(config.screen_size, config.complete_button_point))
    if not complete_tap.ok:
        return BountyCycleResult(BountyOutcome.CAPTURE_UNAVAILABLE, tuple(slot_outcomes), "Complete tap failed.")

    if should_stop():
        return BountyCycleResult(BountyOutcome.STOPPED, tuple(slot_outcomes), "Stopped before reward verification.")

    reward_ok = False
    for attempt in range(1, config.max_reward_verify_attempts + 1):
        if should_stop():
            return BountyCycleResult(BountyOutcome.STOPPED, tuple(slot_outcomes), "Stopped during reward verification.")
        reward = _recognize(runner, serial, config, recognizer, config.reward_screen_roi, config.reward_screen_label)
        if reward is not None and reward.matched:
            reward_ok = True
            break
    if not reward_ok:
        return BountyCycleResult(
            BountyOutcome.REWARD_VERIFY_FAILED, tuple(slot_outcomes),
            f"Reward screen never verified within {config.max_reward_verify_attempts} attempt(s).",
        )

    if on_phase:
        on_phase("claiming reward")
    if should_stop():
        return BountyCycleResult(BountyOutcome.STOPPED, tuple(slot_outcomes), "Stopped before claim.")

    claim = runner.run(serial, build_tap_args(config.screen_size, config.claim_point))
    if not claim.ok:
        return BountyCycleResult(BountyOutcome.CAPTURE_UNAVAILABLE, tuple(slot_outcomes), "Claim tap failed.")

    if should_stop():
        return BountyCycleResult(BountyOutcome.STOPPED, tuple(slot_outcomes), "Stopped before result verification.")

    result_ok = False
    for attempt in range(1, config.max_result_verify_attempts + 1):
        if should_stop():
            return BountyCycleResult(BountyOutcome.STOPPED, tuple(slot_outcomes), "Stopped during result verification.")
        result = _recognize(runner, serial, config, recognizer, config.result_screen_roi, config.result_screen_label)
        if result is not None and result.matched:
            result_ok = True
            break
    if not result_ok:
        return BountyCycleResult(
            BountyOutcome.RESULT_VERIFY_FAILED, tuple(slot_outcomes),
            f"Result screen never verified within {config.max_result_verify_attempts} attempt(s).",
        )

    if on_phase:
        on_phase("closing result, returning to mission list")
    if should_stop():
        return BountyCycleResult(BountyOutcome.STOPPED, tuple(slot_outcomes), "Stopped before closing result.")

    close = runner.run(serial, build_tap_args(config.screen_size, config.close_result_point))
    if not close.ok:
        return BountyCycleResult(BountyOutcome.CAPTURE_UNAVAILABLE, tuple(slot_outcomes), "Close-result tap failed.")

    if should_stop():
        return BountyCycleResult(BountyOutcome.STOPPED, tuple(slot_outcomes), "Stopped before mission-list verification.")

    list_ok = False
    for attempt in range(1, config.max_mission_list_verify_attempts + 1):
        if should_stop():
            return BountyCycleResult(BountyOutcome.STOPPED, tuple(slot_outcomes), "Stopped during mission-list verification.")
        listing = _recognize(runner, serial, config, recognizer, config.mission_list_roi, config.mission_list_label)
        if listing is not None and listing.matched:
            list_ok = True
            break
    if not list_ok:
        return BountyCycleResult(
            BountyOutcome.MISSION_LIST_VERIFY_FAILED, tuple(slot_outcomes),
            f"Mission list never verified within {config.max_mission_list_verify_attempts} attempt(s).",
        )

    # --- Re-refresh each slot and accept a new target, ready to repeat. ---
    if on_phase:
        on_phase("re-refreshing slots for new targets")
    re_accepted: list[SlotOutcome] = []
    for slot_index in range(1, config.slot_count + 1):
        slot_outcome, abort = _accept_or_refresh_slot(
            slot_index=slot_index, serial=serial, runner=runner, recognizer=recognizer,
            config=config, should_stop=should_stop,
        )
        if abort is not None:
            return BountyCycleResult(abort.outcome, tuple(slot_outcomes) + tuple(re_accepted), abort.detail)
        re_accepted.append(slot_outcome)
        if not slot_outcome.accepted:
            return BountyCycleResult(
                BountyOutcome.RE_ACCEPT_FAILED, tuple(slot_outcomes) + tuple(re_accepted),
                f"Slot {slot_index}: re-accept after claim failed within "
                f"{config.max_refresh_attempts} refresh(es).",
            )

    return BountyCycleResult(
        BountyOutcome.COMPLETED_CYCLE, tuple(slot_outcomes) + tuple(re_accepted),
        "Full cycle complete: 5 accepted, claimed, 5 re-accepted; ready to repeat.",
    )
