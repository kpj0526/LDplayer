"""Configurable mission-screen classification + gated completion (GAME-CAL-001).

Customer evidence (1280x720 captures) showed the existing Test-capture
readiness gate (``app.py``'s ``readiness_check``) reporting a template
mismatch even for a valid, correctly-mapped Mission > Region > Free
Subjugation screen. The root problem: that gate only ever looked for
four very *specific*, sub-state-only templates (a refresh-confirmation
popup title, a reward-result header, a fixed "0/200" quantity crop) --
none of which are present on the plain mission-list/detail screen the
customer was actually looking at, and one of which (the quantity crop)
is tied to one specific mission target count and can never match a
mission with a different target (e.g. the customer's real "130/180").

This module fixes that class of problem by separating two concerns
that were previously conflated:

  1. **Is this even the right screen?** -- decided *only* from stable,
     static UI chrome (the Mission tab, the Region tab, the mission
     list/detail panel frame) that stays on screen regardless of which
     mission is selected or what its progress/reward numbers say. This
     is the ``stable_screen_anchors`` check. It is explicitly never
     satisfied by a reward amount or a dynamic progress counter alone.
  2. **What state is the selected mission in, given we ARE on the right
     screen?** -- classified as exactly one of
     :class:`MissionScreenState`: ``COMPLETED`` (an explicit complete
     badge/button, or the completion counter -- e.g. "200/200"),
     ``IN_PROGRESS`` (a generic, non-digit-specific progress indicator
     -- e.g. the customer's "130/180"), ``CURRENCY_ACTION`` (a refresh/
     reroll button showing a currency cost -- e.g. the customer's
     "6600"), or ``UNKNOWN`` (right screen, no confident sub-state
     match -- never treated as completed).

Nothing here captures a frame or sends a tap by itself except
:func:`complete_mission_if_verified`'s own single, explicitly-gated
completion tap -- and that function only ever taps after an immediately
fresh (not cached/stale) precondition capture classifies as
``COMPLETED`` *and* the currently-selected mission is independently
confirmed as the configured target objective, and only ever reports
success after a bounded, freshly re-captured postcondition confirms the
screen actually left that completed-and-untapped state. It is a *no-op*
-- zero ADB calls, not even a capture -- for ``IN_PROGRESS``,
``CURRENCY_ACTION``, ``UNKNOWN``, or ``MISMATCH`` while ``should_stop()``
is already true, and refuses to run at all for a blank/whitespace
serial.

**Customer clarification (GAME-CAL-001, follow-up):** a mission-list
panel *title* such as "자유 토벌작전" ("Free Subjugation") is **not** a
global, always-present anchor -- it only appears for that one objective
type; other mission types show other titles. It must therefore never be
used as a ``stable_screen_anchors`` entry (those are reserved for
chrome that is present regardless of which mission/objective is
selected -- e.g. the Mission tab, the Region tab, the list/detail panel
frame itself). Whether the *currently selected* mission is the required
"모든 몬스터 처치" objective is a completely separate question, answered
only by :func:`assess_mission_target` (mission-title/OCR
classification, driven by ``mission_phrase_roi``/``mission_phrase_label``
+ ``mission_quantity_roi``/``mission_quantity_label``, or the combined
``mission_target_phrase`` template) -- never by
:func:`classify_screen`'s layout gate. A screen showing a different,
non-target mission title is exactly as valid a screen (never a
``MISMATCH``) as one showing the target title; it is simply
``MissionAssessment.NON_TARGET_CONFIRMED``, and every caller in this
project already treats that as "safely do not touch" (a bounded reroll
in ``bounty_mission.run_one_cycle``, and a refused, zero-touch result in
:func:`complete_mission_if_verified`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

from .adb import AdbRunner, validate_serial
from .bounty_config import AnchorSpec, BountyMissionConfig  # noqa: F401 (AnchorSpec re-exported)
from .coordinates import RelativeCoordinate, RelativeRegion, build_tap_args
from .recognition import RecognitionStatus, Recognizer
from .screenshot import capture_screenshot

ShouldStop = Callable[[], bool]

_FULL_SCREEN = RelativeRegion(x=0.0, y=0.0, width=1.0, height=1.0)

_UNCERTAIN_STATUSES = {RecognitionStatus.UNKNOWN, RecognitionStatus.LOW_CONFIDENCE}


def _default_should_stop() -> bool:
    return False


class MissionScreenState(str, Enum):
    """Exactly one of these five, never inferred from a reward amount
    or a dynamic progress counter alone (see module docstring)."""

    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"
    CURRENCY_ACTION = "currency_action"
    UNKNOWN = "unknown"  # right screen, no confident sub-state signal
    MISMATCH = "mismatch"  # not even the configured Mission/Region screen


@dataclass(frozen=True)
class ScreenClassificationResult:
    """Outcome of classifying one already-captured frame.

    ``matched_labels`` lists every configured label that matched, for
    diagnostics -- purely informational, never itself a reason to touch
    anything. ``detail`` is a short, secret-free human-readable reason.
    """

    state: MissionScreenState
    detail: str
    matched_labels: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_completed(self) -> bool:
        return self.state is MissionScreenState.COMPLETED


def classify_screen(
    image_bytes: bytes,
    config: BountyMissionConfig,
    recognizer: Recognizer,
) -> ScreenClassificationResult:
    """Classify one already-captured frame. Never captures, never taps.

    Stage 1 -- stable screen anchors (Mission/Region/mission-list-or-
    detail layout chrome). If ``config.stable_screen_anchors`` is
    non-empty, at least ``config.min_stable_anchor_matches`` (default:
    all of them) must match, or the result is ``MISMATCH`` regardless of
    anything else on the frame. If no stable anchors are configured at
    all (legacy/minimal config), this stage is skipped entirely -- it
    can never produce a false ``MISMATCH`` against a config that simply
    hasn't been calibrated with layout anchors yet.

    Stage 2 -- sub-state, checked in a fixed, safety-ordered sequence:
    ``COMPLETED`` first (an explicit completion signal -- never
    overridden by a stale in-progress/currency template also matching),
    then ``CURRENCY_ACTION``, then ``IN_PROGRESS``, else ``UNKNOWN``.
    """

    matched_labels: list[str] = []

    if config.stable_screen_anchors:
        required = config.min_stable_anchor_matches
        if required is None:
            required = len(config.stable_screen_anchors)
        stable_hits = 0
        for anchor in config.stable_screen_anchors:
            result = recognizer.recognize(image_bytes, anchor.roi, anchor.label, config.threshold)
            if result.matched:
                stable_hits += 1
                matched_labels.append(anchor.label)
        if stable_hits < required:
            return ScreenClassificationResult(
                MissionScreenState.MISMATCH,
                f"Only {stable_hits}/{len(config.stable_screen_anchors)} stable screen anchors "
                f"matched (need {required}); this is not the configured Mission/Region screen.",
                tuple(matched_labels),
            )

    # --- COMPLETED: mirrors the existing, already-tested kill-progress/
    # complete-badge eligibility check in bounty_mission.run_one_cycle,
    # so this module's classification agrees with the live worker.
    kill_progress = recognizer.recognize(
        image_bytes, config.kill_progress_roi, config.kill_progress_complete_label, config.threshold
    )
    if kill_progress.matched:
        matched_labels.append(config.kill_progress_complete_label)
        return ScreenClassificationResult(MissionScreenState.COMPLETED, "Kill-progress complete counter matched.", tuple(matched_labels))
    if "button_complete" in config.template_map:
        complete_signal = recognizer.recognize(image_bytes, _FULL_SCREEN, "button_complete", config.threshold)
        completed_label = "button_complete"
    else:
        complete_signal = recognizer.recognize(
            image_bytes, config.complete_state_roi, config.complete_state_label, config.threshold
        )
        completed_label = config.complete_state_label
    if complete_signal.matched:
        matched_labels.append(completed_label)
        return ScreenClassificationResult(MissionScreenState.COMPLETED, "Explicit completed-state signal matched.", tuple(matched_labels))

    # --- CURRENCY_ACTION: an OR-search across configured refresh/reroll
    # button variants (each a whole-button image, never a parsed cost
    # number) -- e.g. the customer's "6600" refresh button.
    for label in config.currency_action_labels:
        if label not in config.template_map:
            continue
        currency_signal = recognizer.recognize(image_bytes, _FULL_SCREEN, label, config.threshold)
        if currency_signal.matched:
            matched_labels.append(label)
            return ScreenClassificationResult(MissionScreenState.CURRENCY_ACTION, f"Currency/refresh action button matched: {label}.", tuple(matched_labels))

    # --- IN_PROGRESS: one generic, non-digit-specific indicator (e.g. a
    # progress-bar frame graphic) -- deliberately a single configurable
    # anchor, never a fixed "x/y" digit template, so it isn't tied to
    # one specific mission's target quantity (the customer's "130/180"
    # vs. the earlier hardcoded "0/200"/"200/200" is exactly this bug).
    if config.in_progress_roi is not None and config.in_progress_label:
        progress_signal = recognizer.recognize(image_bytes, config.in_progress_roi, config.in_progress_label, config.threshold)
        if progress_signal.matched:
            matched_labels.append(config.in_progress_label)
            return ScreenClassificationResult(MissionScreenState.IN_PROGRESS, "Generic in-progress indicator matched.", tuple(matched_labels))

    return ScreenClassificationResult(
        MissionScreenState.UNKNOWN,
        "Screen layout confirmed (or unconfigured) but no completed/currency/in-progress signal matched.",
        tuple(matched_labels),
    )


def capture_and_classify(
    runner: AdbRunner,
    serial: str,
    config: BountyMissionConfig,
    recognizer: Recognizer,
) -> Optional[ScreenClassificationResult]:
    """Capture one fresh frame from exactly ``serial`` and classify it.

    ``None`` means the capture itself failed/was rejected (invalid
    serial, ADB error, non-PNG bytes) -- distinct from every
    :class:`MissionScreenState`, and callers must never treat a capture
    failure as any kind of "safe to proceed" state.
    """

    capture = capture_screenshot(runner, serial, config.capture_args)
    if not capture.ok:
        return None
    return classify_screen(capture.image_bytes, config, recognizer)


class MissionAssessment(str, Enum):
    """Mission-title/objective classification -- deliberately separate
    from both :class:`MissionScreenState` (layout + completion/progress/
    currency sub-state) and ``stable_screen_anchors`` (screen-layout
    chrome). See the module docstring's "Customer clarification"."""

    TARGET_CONFIRMED = "target_confirmed"
    NON_TARGET_CONFIRMED = "non_target_confirmed"
    RECOGNITION_FAILED = "recognition_failed"
    CAPTURE_UNAVAILABLE = "capture_unavailable"


def _recognize_in_roi(runner, serial, config, recognizer, roi, label):
    """Capture once and recognize ``roi``/``label``; ``None`` means the
    capture itself failed (never means "recognized but no match")."""

    capture = capture_screenshot(runner, serial, config.capture_args)
    if not capture.ok:
        return None
    return recognizer.recognize(capture.image_bytes, roi, label, config.threshold)


def assess_mission_target(
    runner: AdbRunner, serial: str, config: BountyMissionConfig, recognizer: Recognizer,
    *, require_initial_zero: bool = False,
) -> MissionAssessment:
    """Is the *currently selected* mission the configured target
    objective (e.g. "모든 몬스터 처치")? Both required conditions
    (phrase AND quantity, or the single combined
    ``mission_target_phrase`` production template) must
    independently match -- never one signal alone. A confidently
    non-matching title is ``NON_TARGET_CONFIRMED``, not a layout
    problem: a screen showing a different mission's title is just as
    valid a screen as one showing the target title (see
    :func:`classify_screen`, which never inspects a mission title at
    all). This is the single shared implementation behind both
    ``bounty_mission._accept_or_refresh_slot``'s per-slot acceptance
    check and :func:`complete_mission_if_verified`'s completion-target
    guard, so both agree on what counts as the target mission."""

    # The customer acceptance rule is the complete, one-line objective --
    # not a loose combination of a phrase crop and a number crop.  Prefer
    # the single real template containing exactly
    # ``모든 몬스터 처치 (0/200)`` whenever it is configured.  A match is
    # therefore sufficient only because the template itself contains both
    # required pieces in their original relationship.
    exact_target_label = "target_all_monsters_0_of_200"
    if exact_target_label in config.template_map:
        target = _recognize_in_roi(runner, serial, config, recognizer, _FULL_SCREEN, exact_target_label)
        if target is None:
            return MissionAssessment.CAPTURE_UNAVAILABLE
        if target.matched:
            return MissionAssessment.TARGET_CONFIRMED
        if target.status in _UNCERTAIN_STATUSES:
            return MissionAssessment.RECOGNITION_FAILED
        # When choosing a newly refreshed mission, only its exact initial
        # 0/200 line is acceptable.  During later progress/completion
        # checks, the same target naturally reads N/200, so use the
        # separate active-target crop rather than misclassifying it.
        if require_initial_zero:
            return MissionAssessment.NON_TARGET_CONFIRMED

    active_target_label = "target_all_monsters_active"
    # Prefer the calibrated phrase crop over the video-derived active crop:
    # the latter's surrounding chrome also matched a real non-target screen.
    if active_target_label in config.template_map and "mission_target_phrase" not in config.template_map:
        target = _recognize_in_roi(runner, serial, config, recognizer, _FULL_SCREEN, active_target_label)
        if target is None:
            return MissionAssessment.CAPTURE_UNAVAILABLE
        if target.matched:
            return MissionAssessment.TARGET_CONFIRMED
        if target.status in _UNCERTAIN_STATUSES:
            return MissionAssessment.RECOGNITION_FAILED
        return MissionAssessment.NON_TARGET_CONFIRMED

    if "mission_target_phrase" in config.template_map:
        target = _recognize_in_roi(runner, serial, config, recognizer, _FULL_SCREEN, "mission_target_phrase")
        if target is None:
            return MissionAssessment.CAPTURE_UNAVAILABLE
        if target.matched:
            return MissionAssessment.TARGET_CONFIRMED
        if target.status in _UNCERTAIN_STATUSES:
            return MissionAssessment.RECOGNITION_FAILED
        return MissionAssessment.NON_TARGET_CONFIRMED

    phrase = _recognize_in_roi(runner, serial, config, recognizer, config.mission_phrase_roi, config.mission_phrase_label)
    if phrase is None:
        return MissionAssessment.CAPTURE_UNAVAILABLE
    quantity = _recognize_in_roi(runner, serial, config, recognizer, config.mission_quantity_roi, config.mission_quantity_label)
    if quantity is None:
        return MissionAssessment.CAPTURE_UNAVAILABLE
    if phrase.matched and quantity.matched:
        return MissionAssessment.TARGET_CONFIRMED
    if config.template_map and (phrase.status in _UNCERTAIN_STATUSES or quantity.status in _UNCERTAIN_STATUSES):
        return MissionAssessment.RECOGNITION_FAILED
    return MissionAssessment.NON_TARGET_CONFIRMED


@dataclass(frozen=True)
class CompletionAttemptResult:
    """Outcome of one :func:`complete_mission_if_verified` call.

    ``ok`` is only ever ``True`` when the precondition was freshly
    verified ``COMPLETED``, the currently-selected mission was
    independently confirmed as the configured target objective, the tap
    was sent, *and* a bounded postcondition re-check confirmed the
    screen actually left that state. ``tap_sent`` distinguishes "never
    touched" from "touched but postcondition unverified" -- both are
    ``ok=False``, but only the latter performed a real ADB tap.
    ``mission_target`` is ``None`` only when the tap was already refused
    on screen-state grounds before the target check ran.
    """

    ok: bool
    tap_sent: bool
    precondition: Optional[MissionScreenState]
    postcondition: Optional[MissionScreenState]
    detail: str
    mission_target: Optional[MissionAssessment] = None


def _locate_and_tap(
    runner: AdbRunner, serial: str, config: BountyMissionConfig, recognizer: Recognizer, label: str,
) -> Optional[bool]:
    """Find ``label`` in a fresh full-screen capture and tap its matched
    center on exactly ``serial``. ``None`` = template/capture unavailable,
    ``False`` = valid frame with no confident match, ``True`` = the ADB
    tap itself returned success. Mirrors ``bounty_mission._tap_template``
    (kept as a small local copy rather than imported, so this module has
    no dependency on ``bounty_mission`` and cannot form an import cycle)."""

    if label not in config.template_map:
        return None
    capture = capture_screenshot(runner, serial, config.capture_args)
    if not capture.ok:
        return False
    match = recognizer.recognize(capture.image_bytes, _FULL_SCREEN, label, config.threshold)
    if not match.matched or match.match_center is None:
        return False
    x, y = match.match_center
    result = runner.run(serial, build_tap_args(config.screen_size, RelativeCoordinate(x=x, y=y)))
    return result.ok


def complete_mission_if_verified(
    *,
    serial: str,
    runner: AdbRunner,
    recognizer: Recognizer,
    config: BountyMissionConfig,
    should_stop: ShouldStop = _default_should_stop,
    max_postcondition_attempts: int = 3,
) -> CompletionAttemptResult:
    """Tap the completed-mission button -- but only if every guard holds.

    Guards, in order, ANY of which produces a zero-touch result:
      1. ``serial`` must be a genuine, single-token, explicit ADB serial
         (never blank, never guessed/defaulted) -- :func:`validate_serial`.
      2. ``should_stop()`` must be false right now.
      3. A **freshly captured** (this call, not cached) classification of
         the current frame must be exactly ``MissionScreenState.COMPLETED``
         -- ``IN_PROGRESS``/``CURRENCY_ACTION``/``UNKNOWN``/``MISMATCH``
         (and a capture failure) all refuse to tap, with the specific
         reason in ``detail``.
      4. A separate, freshly captured :func:`assess_mission_target` call
         must return ``MissionAssessment.TARGET_CONFIRMED`` -- a
         different, non-target mission (however completed-looking) is
         always refused (``mission_target`` names exactly which
         assessment it got instead).
      5. ``should_stop()`` is re-checked once more immediately before the
         tap itself.

    Only after all four hold is exactly one ADB tap sent (scoped to
    ``serial`` alone). A bounded (``max_postcondition_attempts``) series
    of fresh re-captures then confirms the screen actually left the
    completed-and-untapped state; if it never does, ``ok`` is ``False``
    but ``tap_sent`` stays ``True`` (the tap already happened and cannot
    be un-sent -- this is reported honestly, never hidden as a no-op).
    """

    try:
        validate_serial(serial)
    except ValueError as exc:
        return CompletionAttemptResult(False, False, None, None, f"Refused: invalid serial ({exc}).")

    if should_stop():
        return CompletionAttemptResult(False, False, None, None, "Stopped before precondition capture.")

    precondition_result = capture_and_classify(runner, serial, config, recognizer)
    if precondition_result is None:
        return CompletionAttemptResult(False, False, None, None, "Precondition capture failed; no touch sent.")
    if precondition_result.state is not MissionScreenState.COMPLETED:
        return CompletionAttemptResult(
            False, False, precondition_result.state, None,
            f"Refused: precondition state is {precondition_result.state.value}, not completed; no touch sent.",
        )

    if should_stop():
        return CompletionAttemptResult(False, False, precondition_result.state, None, "Stopped after precondition, before tap.")

    # A COMPLETED *screen* state alone is not enough: the currently
    # selected mission must also be independently confirmed as the
    # required target objective (e.g. "모든 몬스터 처치") -- a different,
    # non-target mission that also happens to show a completed badge
    # must never be tapped. See the module docstring's "Customer
    # clarification" and :func:`assess_mission_target`.
    target_assessment = assess_mission_target(runner, serial, config, recognizer)
    if target_assessment is not MissionAssessment.TARGET_CONFIRMED:
        return CompletionAttemptResult(
            False, False, precondition_result.state, None,
            f"Refused: mission target assessment is {target_assessment.value}, not target-confirmed; no touch sent.",
            target_assessment,
        )

    if should_stop():
        return CompletionAttemptResult(
            False, False, precondition_result.state, None, "Stopped after target check, before tap.", target_assessment,
        )

    # The signal that classified COMPLETED (a counter text, a badge, ...)
    # is not necessarily itself a tappable button -- mirrors
    # ``bounty_mission.run_one_cycle``'s own established pattern: try a
    # dynamic "button_complete" image match first, and fall back to the
    # configured fixed ``complete_button_point`` only when that template
    # isn't configured/found (never when it *is* configured but simply
    # doesn't match -- that stays a hard "not confidently located").
    dynamic_tap = _locate_and_tap(runner, serial, config, recognizer, "button_complete")
    if dynamic_tap is None:
        tap_result = runner.run(serial, build_tap_args(config.screen_size, config.complete_button_point))
        tapped = tap_result.ok
    else:
        tapped = dynamic_tap
    if tapped is not True:
        return CompletionAttemptResult(
            False, False, precondition_result.state, None,
            "Completed state verified, but the completed-state button was not confidently located/tapped; no touch sent.",
            target_assessment,
        )

    postcondition_result: Optional[ScreenClassificationResult] = None
    for _attempt in range(1, max_postcondition_attempts + 1):
        if should_stop():
            return CompletionAttemptResult(
                False, True, precondition_result.state,
                postcondition_result.state if postcondition_result else None,
                "Stopped during postcondition verification (tap already sent; postcondition not verified).",
                target_assessment,
            )
        postcondition_result = capture_and_classify(runner, serial, config, recognizer)
        if postcondition_result is not None and postcondition_result.state is not MissionScreenState.COMPLETED:
            return CompletionAttemptResult(
                True, True, precondition_result.state, postcondition_result.state,
                f"Verified: tap sent and postcondition left completed state (now {postcondition_result.state.value}).",
                target_assessment,
            )

    return CompletionAttemptResult(
        False, True, precondition_result.state,
        postcondition_result.state if postcondition_result else None,
        f"Tap sent, but postcondition never left completed state within {max_postcondition_attempts} attempt(s).",
        target_assessment,
    )
