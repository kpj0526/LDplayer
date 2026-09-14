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

from .adb import AdbRunner, validate_serial
from .bounty_config import BountyMissionConfig
from .coordinates import RelativeCoordinate, RelativeRegion, build_tap_args
from .models import AccountId
from .recognition import Recognizer, RecognitionResult
from .screen_classification import MissionAssessment, assess_mission_target
from .screenshot import capture_screenshot
from .runtime import AccountMissionRuntime, SlotState

ShouldStop = Callable[[], bool]
_FULL_SCREEN = RelativeRegion(x=0.0, y=0.0, width=1.0, height=1.0)


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
    RECOGNITION_FAILED = "recognition_failed"
    CONFIGURATION_ERROR = "configuration_error"


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


def _tap_template(
    runner: AdbRunner, serial: str, config: BountyMissionConfig, recognizer: Recognizer, label: str,
) -> Optional[bool]:
    """Find one configured button in the current ADB frame and tap its
    matched rectangle center on this same serial.

    ``None`` is an unavailable template/capture, ``False`` is a valid frame
    with no confident match, and ``True`` means the real ADB tap succeeded.
    Fixed config points are retained only for legacy fake-test configs that
    have an empty template map; production config must provide this key.
    """
    if label not in config.template_map:
        # A populated production map must never silently fall back to a
        # fixed coordinate for an asset it does not contain.  Empty maps are
        # retained exclusively for legacy fixture tests.
        return False if config.template_map else None
    match = _recognize(runner, serial, config, recognizer, _FULL_SCREEN, label)
    if match is None or not match.matched or match.match_center is None:
        return False
    x, y = match.match_center
    result = runner.run(
        serial,
        build_tap_args(config.screen_size, RelativeCoordinate(x=x, y=y)),
    )
    return result.ok


def _tap_any_template(
    runner: AdbRunner, serial: str, config: BountyMissionConfig, recognizer: Recognizer, labels: tuple[str, ...],
) -> Optional[bool]:
    """One-frame OR search across equivalent button variants.

    The refresh price is not parsed or compared.  Each supplied label is a
    whole-button image variant; the highest confident match supplies the
    center point for one serial-scoped ADB tap.
    """
    configured = tuple(label for label in labels if label in config.template_map)
    if not configured:
        return False if config.template_map else None
    capture = capture_screenshot(runner, serial, config.capture_args)
    if not capture.ok:
        return False
    matches = [
        recognizer.recognize(capture.image_bytes, _FULL_SCREEN, label, config.threshold)
        for label in configured
    ]
    valid = [match for match in matches if match.matched and match.match_center is not None]
    if not valid:
        return False
    best = max(valid, key=lambda match: match.confidence)
    x, y = best.match_center
    return runner.run(serial, build_tap_args(config.screen_size, RelativeCoordinate(x=x, y=y))).ok


def _mission_is_acceptable(runner, serial, config, recognizer) -> MissionAssessment:
    """Is the currently-selected mission the configured target objective?

    GAME-CAL-001: this is now a thin wrapper around the shared
    :func:`ldmanager.screen_classification.assess_mission_target` --
    moved there so mission-title/OCR classification has exactly one
    implementation, shared with
    :func:`ldmanager.screen_classification.complete_mission_if_verified`'s
    own completion-target guard, rather than two copies that could
    silently drift apart. Behavior is unchanged: both the phrase AND the
    quantity must independently match (or the single combined
    ``mission_target_phrase`` production template), never one
    signal alone; a confidently non-matching mission title (e.g. any
    title other than "모든 몬스터 처치") is ``NON_TARGET_CONFIRMED`` --
    never treated as a screen/layout problem, see
    ``ldmanager.screen_classification``'s module docstring."""

    return assess_mission_target(runner, serial, config, recognizer)


def _active_target_is_visible(runner, serial, config, recognizer) -> MissionAssessment:
    """Confirm that the mission about to be completed is still an
    all-monsters target.

    Initial acceptance is stricter: it uses the combined, exact
    ``모든 몬스터 처치 (0/200)`` crop.  Once a target is accepted, the
    counter legitimately changes (``1/200`` ... ``200/200``), so that
    initial crop must *not* be reused to decide whether a completed
    mission is safe to finish.  Production uses the separately supplied
    active-title crop together with the independently matched Complete
    button; an absent/uncertain crop fails closed.
    """
    label = "target_all_monsters_active"
    if label in config.template_map:
        match = _recognize(runner, serial, config, recognizer, _FULL_SCREEN, label)
        if match is None:
            return MissionAssessment.CAPTURE_UNAVAILABLE
        if match.matched:
            return MissionAssessment.TARGET_CONFIRMED
        # A valid but confidently absent title is a non-target.  An
        # unreadable/missing template is an error, never a reroll reason.
        return (
            MissionAssessment.RECOGNITION_FAILED
            if match.status.value in {"unknown", "low_confidence"}
            else MissionAssessment.NON_TARGET_CONFIRMED
        )
    # Legacy fixture configs have no active-title asset.  They retain the
    # historical assessment path solely for compatibility with old tests;
    # a populated production template map never falls through here.
    if config.template_map:
        return MissionAssessment.RECOGNITION_FAILED
    return _mission_is_acceptable(runner, serial, config, recognizer)


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

    dynamic_select = _tap_template(runner, serial, config, recognizer, "mission_slot_unselected")
    if dynamic_select is None:
        select = runner.run(serial, build_tap_args(config.screen_size, config.slot_select_points[slot_index - 1]))
        selected_ok = select.ok
    else:
        selected_ok = dynamic_select
    if not selected_ok:
        return None, BountyCycleResult(
            BountyOutcome.CAPTURE_UNAVAILABLE, (),
            # ``select`` exists only on the legacy fixed-point test path.
            # The production image-template path must not dereference it
            # when the template was missing/no-match, otherwise a harmless
            # failed recognition becomes an unhandled NameError.
            f"Slot {slot_index}: select button was not confidently located or its ADB tap failed.",
        )

    if should_stop():
        return None, BountyCycleResult(
            BountyOutcome.STOPPED, (), f"Stopped mid-slot {slot_index} (after select)."
        )

    already_ok = _mission_is_acceptable(runner, serial, config, recognizer)
    if already_ok is MissionAssessment.CAPTURE_UNAVAILABLE:
        return None, BountyCycleResult(
            BountyOutcome.CAPTURE_UNAVAILABLE, (), f"Slot {slot_index}: capture failed while checking mission."
        )
    if already_ok is MissionAssessment.RECOGNITION_FAILED:
        return None, BountyCycleResult(
            BountyOutcome.RECOGNITION_FAILED, (), f"Slot {slot_index}: target recognition is uncertain; no refresh sent."
        )
    if already_ok is MissionAssessment.TARGET_CONFIRMED:
        return SlotOutcome(slot_index, True, 0, "Already acceptable; no refresh needed."), None

    detail = ""
    # Customer production mode does not impose an arbitrary currency/reroll
    # count.  A non-target is retried until target, Stop, or a real error.
    # The finite legacy branch exists only for the older empty-template test
    # fixtures, which cannot exercise production image recognition.
    attempt = 0
    production_templates = bool(config.template_map)
    while production_templates or attempt < config.max_refresh_attempts:
        attempt += 1
        if should_stop():
            return None, BountyCycleResult(
                BountyOutcome.STOPPED, (), f"Stopped mid-slot {slot_index} (refresh attempt {attempt})."
            )

        dynamic_refresh = _tap_any_template(
            runner, serial, config, recognizer,
            ("button_refresh_4400", "button_refresh_6600", "button_refresh_9900", "button_refresh_14900"),
        )
        if dynamic_refresh is None:
            open_popup = runner.run(serial, build_tap_args(config.screen_size, config.refresh_button_point))
            refresh_ok = open_popup.ok
        else:
            refresh_ok = dynamic_refresh
        if not refresh_ok:
            return None, BountyCycleResult(
                BountyOutcome.CAPTURE_UNAVAILABLE, (),
                f"Slot {slot_index}: refresh button was not confidently located or its ADB tap failed.",
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

        dynamic_confirm = _tap_template(runner, serial, config, recognizer, "button_refresh_confirm")
        if dynamic_confirm is None:
            confirm = runner.run(serial, build_tap_args(config.screen_size, config.refresh_confirm_point))
            confirm_ok = confirm.ok
        else:
            confirm_ok = dynamic_confirm
        if not confirm_ok:
            return None, BountyCycleResult(
                BountyOutcome.CAPTURE_UNAVAILABLE, (),
                f"Slot {slot_index}: verified refresh-confirm button was not confidently located or its ADB tap failed.",
            )

        if should_stop():
            return None, BountyCycleResult(
                BountyOutcome.STOPPED, (), f"Stopped mid-slot {slot_index} (after confirm)."
            )

        acceptable = _mission_is_acceptable(runner, serial, config, recognizer)
        if acceptable is MissionAssessment.CAPTURE_UNAVAILABLE:
            return None, BountyCycleResult(
                BountyOutcome.CAPTURE_UNAVAILABLE, (),
                f"Slot {slot_index}: capture failed while inspecting refreshed mission.",
            )
        if acceptable is MissionAssessment.RECOGNITION_FAILED:
            return None, BountyCycleResult(
                BountyOutcome.RECOGNITION_FAILED, (),
                f"Slot {slot_index}: refreshed mission recognition is uncertain; no further refresh sent.",
            )
        if acceptable is MissionAssessment.TARGET_CONFIRMED:
            accepted = _tap_template(runner, serial, config, recognizer, "button_accept_mission")
            if accepted is False or (accepted is None and config.template_map):
                return None, BountyCycleResult(
                    BountyOutcome.RECOGNITION_FAILED, (),
                    f"Slot {slot_index}: target found but accept button was not confidently located.",
                )
            return SlotOutcome(slot_index, True, attempt, "Accepted after refresh."), None
        detail = f"attempt {attempt}: phrase/quantity not both matched"

    return SlotOutcome(slot_index, False, attempt, detail), None


def run_one_cycle(
    *,
    account_id: AccountId,
    serial: str,
    runner: AdbRunner,
    recognizer: Recognizer,
    config: BountyMissionConfig,
    should_stop: ShouldStop = _default_should_stop,
    on_phase: Optional[Callable[[str], None]] = None,
    runtime: Optional[AccountMissionRuntime] = None,
) -> BountyCycleResult:
    """Run exactly one bounty cycle for one account/serial.

    Returns a structured :class:`BountyCycleResult` — never raises for
    an expected runtime condition. The caller (a worker loop) decides
    whether/when to call this again.
    """

    del account_id  # identity carried by the caller; not needed internally
    # A blank mapping is an ordinary customer setup error, not a worker
    # crash.  Never call capture/touch in this case: every ADB action in a
    # live cycle must have one explicit serial.  The controller will stop
    # this account only and surface the message in the GUI/log.
    try:
        validate_serial(serial)
    except ValueError as exc:
        return BountyCycleResult(
            BountyOutcome.CONFIGURATION_ERROR, (),
            f"ADB serial is not configured for this account ({exc}). Save a valid per-LD serial before Start.",
        )
    slot_outcomes: list[SlotOutcome] = []

    for slot_index in range(1, config.slot_count + 1):
        if runtime is not None and runtime.slots[slot_index - 1] is SlotState.TARGET_LOCKED:
            continue
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
            if runtime is not None:
                runtime.slots[slot_index - 1] = SlotState.NON_TARGET
            return BountyCycleResult(
                BountyOutcome.SLOT_ACCEPT_FAILED, tuple(slot_outcomes),
                f"Slot {slot_index}: no acceptable target within "
                f"{config.max_refresh_attempts} refresh(es).",
            )
        if runtime is not None:
            runtime.slots[slot_index - 1] = SlotState.TARGET_LOCKED

    if runtime is not None:
        runtime.phase = "WAITING_KILL_PROGRESS"

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
        # A completed active mission exposes the actual Complete button.
        # Locate that button by image (not by a fixed coordinate) before
        # allowing the completion transition.
        if "button_complete" in config.template_map:
            complete_badge = _recognize(runner, serial, config, recognizer, _FULL_SCREEN, "button_complete")
        else:
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

    dynamic_complete_select = _tap_template(runner, serial, config, recognizer, "mission_slot_selected")
    if dynamic_complete_select is None:
        select_complete = runner.run(serial, build_tap_args(config.screen_size, config.select_complete_point))
        complete_select_ok = select_complete.ok
    else:
        complete_select_ok = dynamic_complete_select
    if not complete_select_ok:
        return BountyCycleResult(BountyOutcome.CAPTURE_UNAVAILABLE, tuple(slot_outcomes), "Select-complete tap failed.")

    # A complete-looking button alone is not enough: it must belong to the
    # already accepted all-monsters mission currently shown in this account.
    active_target = _active_target_is_visible(runner, serial, config, recognizer)
    if active_target is not MissionAssessment.TARGET_CONFIRMED:
        return BountyCycleResult(
            BountyOutcome.RECOGNITION_FAILED,
            tuple(slot_outcomes),
            f"Completed mission target could not be verified ({active_target.value}); complete not sent.",
        )

    if should_stop():
        return BountyCycleResult(BountyOutcome.STOPPED, tuple(slot_outcomes), "Stopped before complete button.")

    dynamic_complete = _tap_template(runner, serial, config, recognizer, "button_complete")
    if dynamic_complete is None:
        complete_tap = runner.run(serial, build_tap_args(config.screen_size, config.complete_button_point))
        complete_ok = complete_tap.ok
    else:
        complete_ok = dynamic_complete
    if not complete_ok:
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

    dynamic_claim = _tap_template(runner, serial, config, recognizer, "button_claim_reward")
    if dynamic_claim is None:
        claim = runner.run(serial, build_tap_args(config.screen_size, config.claim_point))
        claim_ok = claim.ok
    else:
        claim_ok = dynamic_claim
    if not claim_ok:
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

    dynamic_close = _tap_template(runner, serial, config, recognizer, "button_close_reward")
    if dynamic_close is None:
        close = runner.run(serial, build_tap_args(config.screen_size, config.close_result_point))
        close_ok = close.ok
    else:
        close_ok = dynamic_close
    if not close_ok:
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

    # Only after verified close + mission-list return is it legal to forget
    # locked slots and start a new five-slot configuration.
    if runtime is not None:
        runtime.reset_after_verified_return()
        return BountyCycleResult(BountyOutcome.COMPLETED_CYCLE, tuple(slot_outcomes), "Verified reward cycle complete; slots reset.")

    # --- Legacy stateless re-refresh path. ---
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
