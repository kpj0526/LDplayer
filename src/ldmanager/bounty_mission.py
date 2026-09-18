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
   COMPLETE-SLOT-TRACKING-001: since a slot's own completion state is
   only visible in *that slot's own opened detail view* (confirmed
   against real captures — the mission-list rows themselves carry no
   per-row completion indicator), each poll attempt visits every
   still-candidate locked slot in turn (a plain select/navigation tap)
   to check it individually, remembering exactly which `slot_index`
   qualifies. **0-199/200 never taps complete/claim** — a select tap
   during this polling is only ever navigation to *look*, never a
   completion/claim action, and this function still simply reports
   "not yet" and returns when nothing qualifies; it is the caller's job
   to try again later (real kill progress advances from real gameplay,
   not from anything this code does).
3. Only once a *specific* slot is verified eligible: re-select that
   SAME slot (never a different, possibly still-incomplete one — the
   real customer bug this replaced: a fixed "always row 1" point),
   tap complete, verify the reward screen, claim, verify the result
   screen, close it, verify the mission list is showing again.
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

import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from .adb import AdbRunner
from .bounty_config import BountyMissionConfig
from .coordinates import RelativeCoordinate, RelativeRegion, build_tap_args
from .models import AccountId
from .recognition import Recognizer, RecognitionResult
from .screen_classification import MissionAssessment, assess_mission_target
from .screenshot import capture_screenshot
from .runtime import AccountMissionRuntime, SlotState

ShouldStop = Callable[[], bool]
SleepFn = Callable[[float], None]
_FULL_SCREEN = RelativeRegion(x=0.0, y=0.0, width=1.0, height=1.0)


def _default_should_stop() -> bool:
    return False


_MAX_STDERR_DETAIL_CHARS = 200


def _short(stderr: str) -> str:
    """Trim a raw ADB stderr string for inclusion in a one-line failure
    detail (DIAGNOSTIC-DETAIL-001-adjacent). Never raises on empty/None.
    Not a secret-redaction step itself -- this text still passes
    through the per-account logger's existing
    SensitiveDataRedactionFilter (logs.py) once controller.py logs it;
    an ADB tap's stderr is not expected to ever contain credential-
    shaped text, but that filter remains the actual safety net."""

    text = (stderr or "").strip().replace("\n", " ")
    if len(text) > _MAX_STDERR_DETAIL_CHARS:
        text = text[:_MAX_STDERR_DETAIL_CHARS] + "..."
    return text or "(empty)"


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
    config: BountyMissionConfig, should_stop: ShouldStop, sleep_fn: SleepFn,
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

    # SLOT-SELECT-CALIBRATION-001: always position-based, never a
    # _tap_template() image search. A real customer capture proved two
    # structural problems with matching a "mission_slot_unselected"
    # template here: (1) that crop bakes in the literal mission-title
    # text, the exact anti-pattern GAME-CAL-001 fixed elsewhere; (2)
    # even a perfect crop cannot tell slot 1 apart from slot 3 when both
    # show identical unselected styling -- a single whole-frame search
    # has no notion of "the Nth matching row". Position-based tapping is
    # the actually-correct mechanism for "select the Nth row of a list",
    # so this step no longer attempts template matching at all -- see
    # docs/HANDOFF_CODE.md's TAP-FALLBACK-CRASH-001/
    # SLOT-SELECT-CALIBRATION-001 sections.
    select_result = runner.run(serial, build_tap_args(config.screen_size, config.slot_select_points[slot_index - 1]))
    if not select_result.ok:
        return None, BountyCycleResult(
            BountyOutcome.CAPTURE_UNAVAILABLE, (),
            f"Slot {slot_index}: select tap failed (rc={select_result.returncode}, "
            f"stderr={_short(select_result.stderr)}).",
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
        # ACCEPT-CONFIRM-001: a real customer live run got stuck here --
        # this fast path (target already matched, no refresh needed)
        # previously returned without ever tapping the mission-detail
        # popup's "확인" button, leaving it open on screen and blocking
        # every subsequent slot's select tap. Always taps
        # accept_mission_point directly (real, measured; never a
        # template search -- see docs/HANDOFF_CODE.md's
        # ACCEPT-CONFIRM-001 section for why).
        accept = runner.run(serial, build_tap_args(config.screen_size, config.accept_mission_point))
        if not accept.ok:
            return None, BountyCycleResult(
                BountyOutcome.CAPTURE_UNAVAILABLE, (),
                f"Slot {slot_index}: accept-mission tap failed "
                f"(rc={accept.returncode}, stderr={_short(accept.stderr)}).",
            )
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

        # REFRESH-CALIBRATION-001 / REFRESH-TRIGGER-CORRECTION-001:
        # always position-based, never a _tap_any_template() image
        # search. A real customer capture proved button_refresh_4400/
        # 6600/9900/14900 (pre-GAME-CAL-001 placeholder assets, never
        # real crops) never confidently match -- and because
        # template_map being non-empty overall makes
        # _tap_any_template() return a hard False (not None), this
        # silently blocked the fixed-point fallback from ever running
        # (the same TAP-FALLBACK-CRASH-001/SLOT-SELECT-CALIBRATION-001
        # gotcha). refresh_button_point taps the accept popup's OWN
        # embedded price/counter box (the popup is already open by
        # this point -- select immediately shows it) -- positionally
        # fixed regardless of its currently displayed price -- so this
        # step no longer attempts template matching at all -- see
        # docs/HANDOFF_CODE.md's REFRESH-CALIBRATION-001 and
        # REFRESH-TRIGGER-CORRECTION-001 sections.
        open_popup = runner.run(serial, build_tap_args(config.screen_size, config.refresh_button_point))
        if not open_popup.ok:
            return None, BountyCycleResult(
                BountyOutcome.CAPTURE_UNAVAILABLE, (),
                f"Slot {slot_index}: refresh-open tap failed "
                f"(rc={open_popup.returncode}, stderr={_short(open_popup.stderr)}).",
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
            # RETRY-PACING-001: a real customer report traced back to
            # this -- retry_delay_seconds was configured but never
            # actually applied anywhere in this module, so every
            # bounded verify loop fired its captures back-to-back with
            # no pause for the game's own UI transition/animation to
            # finish, spuriously reporting "never verified" even with a
            # correct tap. Only pace BETWEEN attempts, never after the
            # last one (about to give up either way).
            if popup_attempt < config.max_popup_verify_attempts:
                sleep_fn(config.retry_delay_seconds)

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

        # REFRESH-CALIBRATION-001: same reasoning as the refresh-open tap
        # above -- always the real, measured refresh_confirm_point, safe
        # because the structural popup_verified check just above already
        # confirmed the real renewal-confirm dialog is actually showing.
        confirm = runner.run(serial, build_tap_args(config.screen_size, config.refresh_confirm_point))
        if not confirm.ok:
            return None, BountyCycleResult(
                BountyOutcome.CAPTURE_UNAVAILABLE, (),
                f"Slot {slot_index}: refresh-confirm tap failed "
                f"(rc={confirm.returncode}, stderr={_short(confirm.stderr)}).",
            )

        if should_stop():
            return None, BountyCycleResult(
                BountyOutcome.STOPPED, (), f"Stopped mid-slot {slot_index} (after confirm)."
            )

        # REFRESH-RESULT-DISMISS-001: real customer report -- after
        # confirming the renewal, the game shows one more brief
        # acknowledgment popup for the newly-rolled mission (title +
        # "확률" odds + a single reward icon + "닫기") before returning
        # to the normal accept-popup state. The refresh loop never knew
        # about this screen, so it sat there indefinitely -- every
        # subsequent popup-verify/mission-acceptability check saw this
        # unexpected screen and correctly reported "not verified"/
        # "not acceptable", looping forever without ever dismissing it.
        # Structurally identical to reward_screen (same real "확률"
        # anchor, confirmed via a real customer capture, 1.0
        # confidence) and its close button sits at the exact same real,
        # already-measured position as close_result_point/claim_point
        # -- both already-calibrated assets are reused here, no new
        # template or position needed. Single best-effort check+tap
        # (not a retry loop): if it's not showing, this is a harmless
        # no-op and the acceptability check below proceeds normally.
        ack_popup = _recognize(runner, serial, config, recognizer, config.reward_screen_roi, config.reward_screen_label)
        if ack_popup is not None and ack_popup.matched:
            dismiss = runner.run(serial, build_tap_args(config.screen_size, config.close_result_point))
            if not dismiss.ok:
                return None, BountyCycleResult(
                    BountyOutcome.CAPTURE_UNAVAILABLE, (),
                    f"Slot {slot_index}: refresh-result-dismiss tap failed "
                    f"(rc={dismiss.returncode}, stderr={_short(dismiss.stderr)}).",
                )
            if should_stop():
                return None, BountyCycleResult(
                    BountyOutcome.STOPPED, (), f"Stopped mid-slot {slot_index} (after refresh-result dismiss)."
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
            # ACCEPT-CONFIRM-001: same fix as the fast path above --
            # always accept_mission_point directly, never a template
            # search (button_accept_mission is the same kind of stale,
            # pre-GAME-CAL-001 placeholder asset already fixed for the
            # refresh buttons in REFRESH-CALIBRATION-001).
            accept = runner.run(serial, build_tap_args(config.screen_size, config.accept_mission_point))
            if not accept.ok:
                return None, BountyCycleResult(
                    BountyOutcome.CAPTURE_UNAVAILABLE, (),
                    f"Slot {slot_index}: accept-mission tap failed "
                    f"(rc={accept.returncode}, stderr={_short(accept.stderr)}).",
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
    sleep_fn: SleepFn = time.sleep,
) -> BountyCycleResult:
    """Run exactly one bounty cycle for one account/serial.

    Returns a structured :class:`BountyCycleResult` — never raises for
    an expected runtime condition. The caller (a worker loop) decides
    whether/when to call this again.
    """

    del account_id  # identity carried by the caller; not needed internally
    slot_outcomes: list[SlotOutcome] = []
    # EARLY-COMPLETE-CHECK-001: if a freshly (re-)accepted slot turns out
    # to already be complete, remember it here so the dedicated
    # kill-progress polling loop below can be skipped entirely -- fixes
    # a real, reported inefficiency: after runtime.reset_after_verified_
    # return() unlocks all 5 slots for a new round, every slot gets
    # re-visited to confirm its target phrase (accept_or_refresh_slot
    # only checks the phrase, never completion) -- an already-complete
    # slot was previously "accepted" here and then required a WHOLE
    # SEPARATE pass through every locked slot afterward just to
    # rediscover what this same view already showed. No extra tap is
    # needed for this: it reuses the same already-selected slot's
    # current view.
    eligible_slot_index: Optional[int] = None

    for slot_index in range(1, config.slot_count + 1):
        if runtime is not None and runtime.slots[slot_index - 1] is SlotState.TARGET_LOCKED:
            continue
        if on_phase:
            on_phase(f"slot {slot_index}: select/check")
        slot_outcome, abort = _accept_or_refresh_slot(
            slot_index=slot_index, serial=serial, runner=runner, recognizer=recognizer,
            config=config, should_stop=should_stop, sleep_fn=sleep_fn,
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

        if eligible_slot_index is None:
            if should_stop():
                return BountyCycleResult(
                    BountyOutcome.STOPPED, tuple(slot_outcomes), f"Stopped after accepting slot {slot_index}."
                )
            progress = _recognize(runner, serial, config, recognizer, config.kill_progress_roi, config.kill_progress_complete_label)
            already_complete = progress is not None and progress.matched
            if not already_complete:
                if "button_complete" in config.template_map:
                    complete_badge = _recognize(runner, serial, config, recognizer, _FULL_SCREEN, "button_complete")
                else:
                    complete_badge = _recognize(runner, serial, config, recognizer, config.complete_state_roi, config.complete_state_label)
                already_complete = complete_badge is not None and complete_badge.matched
            if already_complete:
                # EARLY-COMPLETE-JUMP-001: stop accepting/refreshing the
                # remaining slots this pass and go straight to claiming
                # this one -- real customer question: after finding a
                # complete slot partway down the list, why keep touring
                # the rest before acting on it? Any slot not yet visited
                # this round keeps its existing runtime state (locked
                # slots stay locked; anything else is picked up again on
                # the next cycle) -- nothing is lost, just deferred.
                eligible_slot_index = slot_index
                break

    if runtime is not None:
        runtime.phase = "WAITING_KILL_PROGRESS"

    # --- Kill-progress: bounded polling, per LOCKED slot. -----------------
    # COMPLETE-SLOT-TRACKING-001: a single full-screen check here cannot
    # tell WHICH of the (up to 5) locked slots became eligible -- the
    # completion badge/counter is only visible in a slot's OWN opened
    # detail view (the list rows themselves carry no per-row completion
    # indicator; confirmed from real customer captures). Each poll
    # attempt therefore visits every still-candidate LOCKED slot in turn
    # (a plain select/navigation tap -- never complete/claim) and checks
    # THAT slot's own detail for completion, remembering exactly which
    # slot_index qualified. 0-199/200 still never taps complete/claim;
    # only a real, per-slot-verified completion proceeds past this loop,
    # and the completion step below acts on that SAME verified slot
    # (never a different, still-incomplete one -- the real customer bug
    # this replaces: select_complete_point previously always tapped row
    # 1 regardless of which slot actually became eligible).
    #
    # EARLY-COMPLETE-CHECK-001: entirely skipped if the accept loop above
    # already found an eligible slot on the same pass -- no redundant
    # extra round of select/check taps across every locked slot.
    eligible = eligible_slot_index is not None
    progress_detail = ""
    if on_phase:
        on_phase("kill progress: observing")
    if not eligible and should_stop():
        return BountyCycleResult(BountyOutcome.STOPPED, tuple(slot_outcomes), "Stopped before kill-progress check.")

    candidate_slots = [
        i for i in range(1, config.slot_count + 1)
        if runtime is None or runtime.slots[i - 1] is SlotState.TARGET_LOCKED
    ]

    for _kp_attempt in range(1, config.max_kill_progress_poll_attempts + 1):
        if eligible:
            break
        if should_stop():
            return BountyCycleResult(BountyOutcome.STOPPED, tuple(slot_outcomes), "Stopped during kill-progress check.")
        for slot_index in candidate_slots:
            if should_stop():
                return BountyCycleResult(BountyOutcome.STOPPED, tuple(slot_outcomes), "Stopped during kill-progress check.")
            select_result = runner.run(serial, build_tap_args(config.screen_size, config.slot_select_points[slot_index - 1]))
            if not select_result.ok:
                progress_detail = f"slot {slot_index}: select tap failed (rc={select_result.returncode}, stderr={_short(select_result.stderr)})"
                continue
            if should_stop():
                return BountyCycleResult(BountyOutcome.STOPPED, tuple(slot_outcomes), "Stopped during kill-progress check.")
            progress = _recognize(runner, serial, config, recognizer, config.kill_progress_roi, config.kill_progress_complete_label)
            if progress is not None and progress.matched:
                eligible = True
                eligible_slot_index = slot_index
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
                eligible_slot_index = slot_index
                break
            progress_detail = f"slot {slot_index}: kill progress not yet complete"
        if eligible:
            break
        # RETRY-PACING-001: real kill progress advances from real
        # gameplay, not from anything this code does -- pace full
        # passes over the candidate slots rather than hammering ADB
        # continuously while waiting for it.
        if _kp_attempt < config.max_kill_progress_poll_attempts:
            sleep_fn(config.retry_delay_seconds)

    if not eligible or eligible_slot_index is None:
        return BountyCycleResult(
            BountyOutcome.KILL_PROGRESS_NOT_COMPLETE, tuple(slot_outcomes),
            f"0-199/200: not eligible yet ({progress_detail}); no complete/reward action taken.",
        )

    # --- Complete -> reward -> claim -> result -> close -> mission list. ---
    # PHASE-VISIBILITY-001: real customer debugging need -- runtime.phase
    # (the GUI's "phase:" display) was only ever set once, to
    # WAITING_KILL_PROGRESS, then never updated again for the rest of
    # the cycle -- a run stuck anywhere from here through mission-list
    # verification showed the same stale phase text regardless of how
    # far it had actually progressed, making a live log hard to read
    # at a glance during exactly this kind of remote debugging.
    if runtime is not None:
        runtime.phase = "COMPLETING"
    if on_phase:
        on_phase("completing: select + complete")
    if should_stop():
        return BountyCycleResult(BountyOutcome.STOPPED, tuple(slot_outcomes), "Stopped before completing.")

    # COMPLETE-RETRY-001: real customer question -- if the complete tap
    # doesn't confidently land (typically because select_complete_point
    # is momentarily not showing the eligible mission's detail view),
    # why give up on the first miss instead of just re-selecting and
    # trying again? Bounded retry, re-selecting the EXACT slot just
    # verified eligible above each attempt (never a fixed "always row
    # 1" point -- COMPLETE-SLOT-TRACKING-001).
    complete_ok = False
    complete_detail = ""
    for _complete_attempt in range(1, config.max_complete_verify_attempts + 1):
        if should_stop():
            return BountyCycleResult(BountyOutcome.STOPPED, tuple(slot_outcomes), "Stopped before complete button.")

        select_complete = runner.run(serial, build_tap_args(config.screen_size, config.slot_select_points[eligible_slot_index - 1]))
        if not select_complete.ok:
            complete_detail = f"select-complete tap failed (rc={select_complete.returncode}, stderr={_short(select_complete.stderr)})"
            if _complete_attempt < config.max_complete_verify_attempts:
                sleep_fn(config.retry_delay_seconds)
            continue

        if should_stop():
            return BountyCycleResult(BountyOutcome.STOPPED, tuple(slot_outcomes), "Stopped before complete button.")

        dynamic_complete = _tap_template(runner, serial, config, recognizer, "button_complete")
        if dynamic_complete is None:
            complete_tap = runner.run(serial, build_tap_args(config.screen_size, config.complete_button_point))
            complete_ok = complete_tap.ok
            complete_detail = f"rc={complete_tap.returncode}, stderr={_short(complete_tap.stderr)}"
        else:
            complete_ok = dynamic_complete
            # STDERR-DETAIL-001-adjacent: no confident "button_complete"
            # match on THIS fresh capture -- never an ADB failure.
            complete_detail = "no confident button_complete match on the current screen (select_complete_point may not be showing the eligible mission)"
        if complete_ok:
            break
        # RETRY-PACING-001: see the popup-verify loop's comment above.
        if _complete_attempt < config.max_complete_verify_attempts:
            sleep_fn(config.retry_delay_seconds)

    if not complete_ok:
        return BountyCycleResult(
            BountyOutcome.CAPTURE_UNAVAILABLE, tuple(slot_outcomes),
            f"Complete tap failed after {config.max_complete_verify_attempts} attempt(s) ({complete_detail}).",
        )

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
        # RETRY-PACING-001: see the popup-verify loop's comment above.
        if attempt < config.max_reward_verify_attempts:
            sleep_fn(config.retry_delay_seconds)
    if not reward_ok:
        return BountyCycleResult(
            BountyOutcome.REWARD_VERIFY_FAILED, tuple(slot_outcomes),
            f"Reward screen never verified within {config.max_reward_verify_attempts} attempt(s).",
        )

    if runtime is not None:
        runtime.phase = "CLAIMING"
    if on_phase:
        on_phase("claiming reward")
    if should_stop():
        return BountyCycleResult(BountyOutcome.STOPPED, tuple(slot_outcomes), "Stopped before claim.")

    dynamic_claim = _tap_template(runner, serial, config, recognizer, "button_claim_reward")
    if dynamic_claim is None:
        claim = runner.run(serial, build_tap_args(config.screen_size, config.claim_point))
        claim_ok = claim.ok
        claim_detail = f"rc={claim.returncode}, stderr={_short(claim.stderr)}"
    else:
        claim_ok = dynamic_claim
        claim_detail = "no confident button_claim_reward match on the current screen"
    if not claim_ok:
        return BountyCycleResult(BountyOutcome.CAPTURE_UNAVAILABLE, tuple(slot_outcomes), f"Claim tap failed ({claim_detail}).")

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
        # RETRY-PACING-001: see the popup-verify loop's comment above.
        if attempt < config.max_result_verify_attempts:
            sleep_fn(config.retry_delay_seconds)
    if not result_ok:
        return BountyCycleResult(
            BountyOutcome.RESULT_VERIFY_FAILED, tuple(slot_outcomes),
            f"Result screen never verified within {config.max_result_verify_attempts} attempt(s).",
        )

    if runtime is not None:
        runtime.phase = "CLOSING_RESULT"
    if on_phase:
        on_phase("closing result, returning to mission list")
    if should_stop():
        return BountyCycleResult(BountyOutcome.STOPPED, tuple(slot_outcomes), "Stopped before closing result.")

    # RESULT-CLOSE-CALIBRATION-001: always position-based, never a
    # "button_close_reward" template search. Real measurement (see
    # docs/HANDOFF_CODE.md) showed the "보상 받기"/"닫기" buttons --
    # same position, same ornate gold-button frame, only ~2 characters
    # of text differ -- cannot be reliably told apart by template
    # matching alone (a tight text-only crop still scored close enough
    # to risk a false positive against the OTHER button). The real,
    # measured fixed point is exactly as safe here as
    # slot_select_points/select_complete_point are for slot selection
    # (SLOT-SELECT-CALIBRATION-001): the preceding result_screen_label
    # check already confirmed we're on a real post-complete popup
    # before this fixed-point tap ever fires.
    close = runner.run(serial, build_tap_args(config.screen_size, config.close_result_point))
    if not close.ok:
        return BountyCycleResult(
            BountyOutcome.CAPTURE_UNAVAILABLE, tuple(slot_outcomes),
            f"Close-result tap failed (rc={close.returncode}, stderr={_short(close.stderr)}).",
        )

    if runtime is not None:
        runtime.phase = "VERIFYING_MISSION_LIST"
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
        # RETRY-PACING-001: see the popup-verify loop's comment above.
        if attempt < config.max_mission_list_verify_attempts:
            sleep_fn(config.retry_delay_seconds)
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
            config=config, should_stop=should_stop, sleep_fn=sleep_fn,
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
