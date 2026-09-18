from pathlib import Path

from ldmanager.adb import AdbBinaryResult, AdbCommandResult
from ldmanager.bounty_config import BountyMissionConfig
from ldmanager.bounty_mission import BountyOutcome, run_one_cycle
from ldmanager.coordinates import RelativeCoordinate, RelativeRegion, ScreenSize, build_tap_args
from ldmanager.models import AccountId
from ldmanager.recognition import PlaceholderRecognizer, RecognitionResult, RecognitionStatus
from ldmanager.screenshot import DEFAULT_CAPTURE_ARGS
from tests.fakes import FakeAdbRunner, LabelMappingRecognizer

_VALID_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
_SERIAL = "127.0.0.1:5555"

_PHRASE = "모든 몬스터 처치"
_QTY = "200"
_POPUP_ANCHOR = "popup-anchor"
_POPUP_TITLE = "popup-title"
_KILL_PROGRESS = "200/200"
_COMPLETE_BADGE = "완료-badge"
_REWARD = "reward-screen"
_RESULT = "result-screen"
_MISSION_LIST = "mission-list"

_ALL_LABELS = frozenset(
    {_PHRASE, _QTY, _POPUP_ANCHOR, _POPUP_TITLE, _KILL_PROGRESS, _REWARD, _RESULT, _MISSION_LIST}
)


def _roi(x=0.0, y=0.0, w=0.1, h=0.1):
    return RelativeRegion(x=x, y=y, width=w, height=h)


def _config(**overrides) -> BountyMissionConfig:
    defaults = dict(
        slot_select_points=tuple(RelativeCoordinate(x=0.1, y=0.1 * i) for i in range(1, 6)),
        mission_phrase_roi=_roi(),
        mission_phrase_label=_PHRASE,
        mission_quantity_roi=_roi(0.2),
        mission_quantity_label=_QTY,
        accept_mission_point=RelativeCoordinate(x=0.55, y=0.72),
        refresh_button_point=RelativeCoordinate(x=0.9, y=0.9),
        refresh_popup_anchor_roi=_roi(0.3),
        refresh_popup_anchor_label=_POPUP_ANCHOR,
        refresh_popup_title_roi=_roi(0.4),
        refresh_popup_title_label=_POPUP_TITLE,
        refresh_confirm_point=RelativeCoordinate(x=0.5, y=0.6),
        kill_progress_roi=_roi(0.5),
        kill_progress_complete_label=_KILL_PROGRESS,
        complete_state_roi=_roi(0.6),
        complete_state_label=_COMPLETE_BADGE,
        select_complete_point=RelativeCoordinate(x=0.1, y=0.2),
        complete_button_point=RelativeCoordinate(x=0.85, y=0.9),
        reward_screen_roi=_roi(0.7),
        reward_screen_label=_REWARD,
        claim_point=RelativeCoordinate(x=0.5, y=0.7),
        result_screen_roi=_roi(0.8),
        result_screen_label=_RESULT,
        close_result_point=RelativeCoordinate(x=0.9, y=0.1),
        mission_list_roi=_roi(0.05, 0.05),
        mission_list_label=_MISSION_LIST,
        screen_size=ScreenSize(width=1000, height=1000),
        templates_dir=Path("templates"),
        threshold=0.8,
        max_capture_attempts=2,
        max_refresh_attempts=3,
        max_popup_verify_attempts=2,
        max_kill_progress_poll_attempts=3,
        max_reward_verify_attempts=2,
        max_result_verify_attempts=2,
        max_mission_list_verify_attempts=2,
        retry_delay_seconds=0.0,
        capture_args=DEFAULT_CAPTURE_ARGS,
    )
    defaults.update(overrides)
    return BountyMissionConfig(**defaults)


def _runner_with_valid_captures() -> FakeAdbRunner:
    return FakeAdbRunner(
        capture_results={
            (_SERIAL, DEFAULT_CAPTURE_ARGS): AdbBinaryResult(
                serial=_SERIAL, args=DEFAULT_CAPTURE_ARGS, returncode=0,
                stdout_bytes=_VALID_PNG, stderr="",
            )
        }
    )


def _run(runner, recognizer, config, **kwargs):
    return run_one_cycle(
        account_id=AccountId.LD1, serial=_SERIAL, runner=runner,
        recognizer=recognizer, config=config, **kwargs,
    )


# --- full one-cycle state flow --------------------------------------------


def test_full_cycle_reaches_completed_state_once():
    runner = _runner_with_valid_captures()
    recognizer = LabelMappingRecognizer(matching_labels=_ALL_LABELS)

    result = _run(runner, recognizer, _config())

    assert result.outcome is BountyOutcome.COMPLETED_CYCLE
    # 6 slot outcomes: 1 initial accept (EARLY-COMPLETE-JUMP-001: every
    # label matches here, so slot 1 is found complete on its own accept
    # check and the loop jumps straight to claiming it -- slots 2-5
    # are never visited this pass) + 5 re-accepts after claim.
    assert len(result.slots) == 6
    assert all(s.accepted for s in result.slots)
    # 1 initial accept select + 1 accept-confirm tap (ACCEPT-CONFIRM-001)
    # + (EARLY-COMPLETE-CHECK-001/EARLY-COMPLETE-JUMP-001: slot 1's
    # completion is detected and acted on immediately, no kill-progress-
    # phase taps and no slots 2-5 accept taps at all) select-complete +
    # complete + claim + close (4) + 5 re-accept selects + 5 more
    # accept-confirm taps (legacy stateless path, since no runtime is
    # passed here) = 16.
    assert len(runner.calls) == (1 + 1) + 4 + (5 + 5)


# --- phrase-only / quantity-only must reject (never one signal alone) ----


def test_phrase_only_match_is_rejected_bounded_reroll():
    runner = _runner_with_valid_captures()
    # Popup structural labels match (so refresh actually proceeds each
    # attempt), but only the phrase matches -- quantity never does.
    recognizer = LabelMappingRecognizer(
        matching_labels=frozenset({_PHRASE, _POPUP_ANCHOR, _POPUP_TITLE})
    )

    result = _run(runner, recognizer, _config(max_refresh_attempts=3))

    assert result.outcome is BountyOutcome.SLOT_ACCEPT_FAILED
    assert len(result.slots) == 1
    assert result.slots[0].accepted is False
    assert result.slots[0].refresh_attempts == 3


def test_quantity_only_match_is_rejected_bounded_reroll():
    runner = _runner_with_valid_captures()
    recognizer = LabelMappingRecognizer(
        matching_labels=frozenset({_QTY, _POPUP_ANCHOR, _POPUP_TITLE})
    )

    result = _run(runner, recognizer, _config(max_refresh_attempts=3))

    assert result.outcome is BountyOutcome.SLOT_ACCEPT_FAILED
    assert result.slots[0].refresh_attempts == 3


# --- variable refresh cost must not affect popup detection ---------------


def test_popup_detection_is_unaffected_by_variable_cost_signal():
    """The recognizer never sees a "cost" label at all in this mock --
    proving popup verification/confirm depends only on the two
    structural labels, regardless of what a (hypothetical, varying)
    cost display shows. No "cost" label exists anywhere in
    matching_labels, yet refresh still proceeds every bounded attempt
    (popup verified + confirmed each time) purely on structural
    grounds."""

    runner = _runner_with_valid_captures()
    recognizer = LabelMappingRecognizer(
        matching_labels=frozenset({_POPUP_ANCHOR, _POPUP_TITLE})
    )

    result = _run(runner, recognizer, _config(max_refresh_attempts=3, max_popup_verify_attempts=1))

    # Mission itself never becomes acceptable (phrase/quantity absent),
    # so the cycle bounds out -- but every one of the 3 refresh attempts
    # got past a verified popup + a confirm tap, proving detection
    # worked purely structurally regardless of any cost value.
    assert result.outcome is BountyOutcome.SLOT_ACCEPT_FAILED
    assert result.slots[0].refresh_attempts == 3
    # 1 select + 3 * (refresh-open + confirm) = 7 touches.
    assert len(runner.calls) == 1 + 3 * 2


def test_popup_not_structurally_verified_never_confirms():
    runner = _runner_with_valid_captures()
    # Only the anchor matches, not the title -- popup must NOT be
    # considered verified, and confirm must never be tapped.
    recognizer = LabelMappingRecognizer(matching_labels=frozenset({_POPUP_ANCHOR}))

    result = _run(runner, recognizer, _config(max_refresh_attempts=1, max_popup_verify_attempts=2))

    assert result.outcome is BountyOutcome.REFRESH_POPUP_NOT_VERIFIED
    # Only the select tap and the refresh-open tap should have happened
    # -- confirm_point's tap must never appear.
    cfg = _config()
    confirm_args = tuple(build_tap_args(cfg.screen_size, cfg.refresh_confirm_point))
    assert (_SERIAL, confirm_args) not in runner.calls


# --- 0-199/200 never taps complete/reward ---------------------------------


def test_kill_progress_incomplete_never_taps_complete_or_reward():
    runner = _runner_with_valid_captures()
    # Slots accept fine, but neither kill-progress nor complete-badge
    # ever matches.
    recognizer = LabelMappingRecognizer(matching_labels=frozenset({_PHRASE, _QTY}))

    result = _run(runner, recognizer, _config(max_kill_progress_poll_attempts=3))

    assert result.outcome is BountyOutcome.KILL_PROGRESS_NOT_COMPLETE
    assert len(result.slots) == 5
    # 5 initial accept selects + 5 accept-confirm taps (ACCEPT-CONFIRM-
    # 001: every already-acceptable slot also taps accept_mission_point),
    # then COMPLETE-SLOT-TRACKING-001's per-slot polling visits all 5
    # candidate slots on each of the 3 bounded poll attempts (never
    # finding a match) = (5+5) + 3*5 = 25; nothing for complete/reward/
    # claim.
    assert len(runner.calls) == (5 + 5) + 3 * 5


def test_kill_progress_via_explicit_complete_badge_is_also_eligible():
    runner = _runner_with_valid_captures()
    recognizer = LabelMappingRecognizer(
        matching_labels=frozenset({_PHRASE, _QTY, _COMPLETE_BADGE, _REWARD, _RESULT, _MISSION_LIST})
    )

    result = _run(runner, recognizer, _config())

    # Eligible via the complete-state badge (not the 200/200 counter),
    # and the full completion flow proceeds.
    assert result.outcome is BountyOutcome.COMPLETED_CYCLE


# --- bounded reroll (no infinite click) ------------------------------------


def test_slot_refresh_is_bounded_when_never_acceptable():
    runner = _runner_with_valid_captures()
    recognizer = PlaceholderRecognizer()  # always UNKNOWN

    result = _run(runner, recognizer, _config(max_refresh_attempts=3, max_popup_verify_attempts=1))

    assert result.outcome is BountyOutcome.REFRESH_POPUP_NOT_VERIFIED
    # Bounded: exactly one select + one refresh-open touch (popup never
    # verified, so confirm never sent, and no further reroll attempted
    # since popup verification itself already failed conclusively).
    assert len(runner.calls) == 2


# --- account isolation / no cross-serial commands -------------------------


def test_two_accounts_use_independent_runners_and_serials():
    runner_a = _runner_with_valid_captures()
    runner_b = FakeAdbRunner(
        capture_results={
            ("127.0.0.1:5557", DEFAULT_CAPTURE_ARGS): AdbBinaryResult(
                serial="127.0.0.1:5557", args=DEFAULT_CAPTURE_ARGS, returncode=1,
                stdout_bytes=b"", stderr="offline",
            )
        }
    )
    recognizer = LabelMappingRecognizer(matching_labels=_ALL_LABELS)

    result_a = run_one_cycle(
        account_id=AccountId.LD1, serial=_SERIAL, runner=runner_a,
        recognizer=recognizer, config=_config(),
    )
    result_b = run_one_cycle(
        account_id=AccountId.LD2, serial="127.0.0.1:5557", runner=runner_b,
        recognizer=recognizer, config=_config(),
    )

    assert result_a.outcome is BountyOutcome.COMPLETED_CYCLE
    assert result_b.outcome is BountyOutcome.CAPTURE_UNAVAILABLE
    # Every call recorded on runner_a used _SERIAL; every call on
    # runner_b used its own, different serial -- no cross-contamination
    # between the two independent runners/accounts.
    assert all(call[0] == _SERIAL for call in runner_a.calls)
    assert all(call[0] == "127.0.0.1:5557" for call in runner_b.calls)
    assert not any(call[0] == _SERIAL for call in runner_b.calls)
    # Only the slot-1 select tap happened on runner_b before its
    # capture failure aborted the cycle (select itself is unconditional;
    # capture is checked right after).
    assert len(runner_b.calls) == 1


# --- safe error / stop handling --------------------------------------------


def test_should_stop_true_from_start_sends_zero_touches():
    runner = _runner_with_valid_captures()
    recognizer = LabelMappingRecognizer(matching_labels=_ALL_LABELS)

    result = _run(runner, recognizer, _config(), should_stop=lambda: True)

    assert result.outcome is BountyOutcome.STOPPED
    assert runner.calls == []
    assert runner.capture_calls == []


def test_capture_unavailable_mid_slot_is_reported_without_crashing():
    runner = FakeAdbRunner(
        capture_results={
            (_SERIAL, DEFAULT_CAPTURE_ARGS): AdbBinaryResult(
                serial=_SERIAL, args=DEFAULT_CAPTURE_ARGS, returncode=1,
                stdout_bytes=b"", stderr="offline",
            )
        }
    )
    recognizer = LabelMappingRecognizer(matching_labels=_ALL_LABELS)

    result = _run(runner, recognizer, _config())

    assert result.outcome is BountyOutcome.CAPTURE_UNAVAILABLE
    # Only the slot-1 select tap happened before capture failure aborted.
    assert len(runner.calls) == 1


def test_select_tap_failure_detail_includes_the_real_adb_stderr():
    """Real customer report: a bare 'rc=125' with no further context was
    impossible to diagnose. The actual adb stderr text must reach the
    result detail too, not just the numeric return code."""

    cfg = _config()
    select_args = tuple(build_tap_args(cfg.screen_size, cfg.slot_select_points[0]))
    runner = FakeAdbRunner(
        command_results={
            (_SERIAL, select_args): AdbCommandResult(
                serial=_SERIAL, args=select_args, returncode=125,
                stdout="", stderr="error: device offline",
            )
        }
    )
    recognizer = LabelMappingRecognizer(matching_labels=_ALL_LABELS)

    result = _run(runner, recognizer, cfg)

    assert result.outcome is BountyOutcome.CAPTURE_UNAVAILABLE
    assert "rc=125" in result.detail
    assert "error: device offline" in result.detail


def test_complete_tap_no_confident_match_gives_an_actionable_reason_not_a_bare_failure():
    """Real customer report (a KNOWN, documented limitation manifesting
    live): select_complete_point always taps slot 1's position, so if a
    DIFFERENT locked slot was the one that actually became eligible, the
    screen showing after select-complete won't have a real "button_complete"
    to find -- a safe refusal (no unsafe tap), but the old bare "Complete
    tap failed." gave no hint why. Must now explain a template search
    found no confident match, not just fail silently."""

    runner = _runner_with_valid_captures()
    # Eligible via the kill-progress counter (so the flow reaches the
    # complete-tap step at all), but "button_complete" itself never
    # confidently matches on this frame -- the real-world shape of the
    # "wrong slot selected" scenario.
    recognizer = LabelMappingRecognizer(matching_labels=frozenset({_PHRASE, _QTY, _KILL_PROGRESS}))
    cfg = _config(template_map={"button_complete": "button_complete.png"})

    result = _run(runner, recognizer, cfg)

    assert result.outcome is BountyOutcome.CAPTURE_UNAVAILABLE
    assert "Complete tap failed" in result.detail
    assert "no confident button_complete match" in result.detail


# --- real customer crash: dynamic-tap "no confident match" must never ------
# --- raise UnboundLocalError, only ever a structured, contained result -----


class _ConfidentNoMatchRecognizer:
    """Like LabelMappingRecognizer, but reports a genuinely CONFIDENT
    non-match (RecognitionStatus.NO_MATCH) for anything not in
    ``matching_labels``, rather than UNKNOWN. Needed to reach
    NON_TARGET_CONFIRMED deterministically: with a real (non-empty)
    template_map, _mission_is_acceptable treats an UNCERTAIN (UNKNOWN/
    LOW_CONFIDENCE) phrase/quantity as RECOGNITION_FAILED, which would
    short-circuit before ever reaching the refresh-open/confirm steps
    these regression tests target."""

    def __init__(self, matching_labels=frozenset()):
        self.matching_labels = frozenset(matching_labels)
        self.calls: list = []

    def recognize(self, image_bytes, roi, expected_label, threshold):
        self.calls.append(expected_label)
        if expected_label in self.matching_labels:
            return RecognitionResult(RecognitionStatus.MATCH, expected_label, 1.0, "test: matched", (0.5, 0.5))
        return RecognitionResult(RecognitionStatus.NO_MATCH, None, 0.05, "test: confidently absent")


def test_slot_select_is_always_position_based_never_template_matched():
    """SLOT-SELECT-CALIBRATION-001 (follow-up to the same real customer
    crash): a real 'mission_slot_unselected' template configured but not
    confidently matching the current frame used to raise
    UnboundLocalError('select') -- see TAP-FALLBACK-CRASH-001. Root
    cause traced further: template matching structurally cannot tell
    slot 1 apart from slot 3 when both show identical unselected
    styling. Fix: slot selection no longer attempts template matching
    at all -- it always taps config.slot_select_points[slot_index-1]
    directly. Proven here by configuring a 'mission_slot_unselected'
    template that a confidently-non-matching recognizer would have
    rejected under the old behavior, yet the select tap still succeeds
    (using the real, calibrated fixed point) and the cycle proceeds
    past slot selection entirely -- reaching the refresh loop instead
    of failing at select."""

    runner = _runner_with_valid_captures()
    recognizer = _ConfidentNoMatchRecognizer()  # would have failed a template search
    cfg = _config(template_map={"mission_slot_unselected": "mission_slot_unselected.png"})

    result = _run(runner, recognizer, cfg)  # must not raise, must not fail at "select"

    assert result.outcome is BountyOutcome.REFRESH_POPUP_NOT_VERIFIED
    assert "select tap failed" not in result.detail
    # Reached (and failed at) the NEXT step instead -- proof slot
    # selection itself was never the blocker here. REFRESH-CALIBRATION-001:
    # refresh-open itself is also always position-based now (never a
    # template search), so it succeeds unconditionally here too -- the
    # cycle proceeds all the way to the popup's own structural
    # verification (anchor/title), which is what finally, correctly,
    # fails given this confidently-non-matching recognizer.
    assert "refresh popup never verified structurally" in result.detail


def test_slot_select_tap_uses_the_exact_configured_slot_select_point():
    """Direct proof the select tap argv matches slot_select_points[N-1]
    -- never a template-derived coordinate, never another slot's point."""

    runner = _runner_with_valid_captures()
    recognizer = LabelMappingRecognizer(matching_labels=_ALL_LABELS)  # slot 1 accepted immediately
    cfg = _config()

    _run(runner, recognizer, cfg)

    expected_args = tuple(build_tap_args(cfg.screen_size, cfg.slot_select_points[0]))
    assert (_SERIAL, expected_args) in runner.calls


def test_already_acceptable_slot_still_taps_the_accept_mission_confirm_button():
    """ACCEPT-CONFIRM-001: real customer report -- a live run got stuck
    on the mission-detail popup that opens after selecting a slot whose
    target phrase/quantity was ALREADY matched (no refresh needed). The
    old code returned "accepted" without ever tapping that popup's
    "확인" button, leaving it open on screen and blocking every
    subsequent slot's select tap. Direct proof the fast path (no
    refresh) still taps accept_mission_point, exactly like the
    post-refresh path already did."""

    runner = _runner_with_valid_captures()
    recognizer = LabelMappingRecognizer(matching_labels=_ALL_LABELS)  # slot 1 accepted immediately, no refresh
    cfg = _config()

    _run(runner, recognizer, cfg)

    expected_args = tuple(build_tap_args(cfg.screen_size, cfg.accept_mission_point))
    assert (_SERIAL, expected_args) in runner.calls


def test_accept_mission_tap_failure_detail_includes_the_real_adb_stderr():
    """Same STDERR-DETAIL-001 guarantee for the new accept-confirm tap."""

    cfg = _config()
    select_args = tuple(build_tap_args(cfg.screen_size, cfg.slot_select_points[0]))
    accept_args = tuple(build_tap_args(cfg.screen_size, cfg.accept_mission_point))
    runner = FakeAdbRunner(
        capture_results={
            (_SERIAL, DEFAULT_CAPTURE_ARGS): AdbBinaryResult(
                serial=_SERIAL, args=DEFAULT_CAPTURE_ARGS, returncode=0,
                stdout_bytes=_VALID_PNG, stderr="",
            )
        },
        command_results={
            (_SERIAL, select_args): AdbCommandResult(
                serial=_SERIAL, args=select_args, returncode=0, stdout="", stderr="",
            ),
            (_SERIAL, accept_args): AdbCommandResult(
                serial=_SERIAL, args=accept_args, returncode=125,
                stdout="", stderr="error: device offline",
            ),
        },
    )
    recognizer = LabelMappingRecognizer(matching_labels=_ALL_LABELS)  # target already matched, no refresh

    result = _run(runner, recognizer, cfg)

    assert result.outcome is BountyOutcome.CAPTURE_UNAVAILABLE
    assert "accept-mission tap failed" in result.detail
    assert "rc=125" in result.detail
    assert "error: device offline" in result.detail


def test_refresh_open_is_always_position_based_never_template_matched():
    """REFRESH-CALIBRATION-001: a real customer capture proved
    button_refresh_4400/6600/9900/14900 (pre-GAME-CAL-001 placeholder
    assets) never confidently match, and because a non-empty
    template_map makes _tap_any_template() return a hard False (not
    None), this silently blocked the fixed-point fallback from ever
    running -- reported live as "Slot N: refresh-open tap failed" on a
    real, never-target-matching dungeon-type mission. Fix: refresh-open
    no longer attempts template matching at all -- it always taps
    config.refresh_button_point directly. Proven here by configuring a
    'button_refresh_4400' template that a confidently-non-matching
    recognizer would have rejected under the old behavior, yet the
    refresh-open tap still succeeds (using the real, calibrated fixed
    point) and the cycle proceeds to the popup's own structural
    verification instead of failing at "refresh-open"."""

    runner = _runner_with_valid_captures()
    recognizer = _ConfidentNoMatchRecognizer(matching_labels={"mission_slot_unselected"})
    cfg = _config(
        template_map={
            "mission_slot_unselected": "mission_slot_unselected.png",
            "button_refresh_4400": "button_refresh_4400.png",
        },
    )

    result = _run(runner, recognizer, cfg)  # must not raise

    assert result.outcome is BountyOutcome.REFRESH_POPUP_NOT_VERIFIED
    assert "refresh-open tap failed" not in result.detail
    expected_args = tuple(build_tap_args(cfg.screen_size, cfg.refresh_button_point))
    assert (_SERIAL, expected_args) in runner.calls


def test_refresh_open_tap_failure_detail_includes_the_real_adb_stderr():
    """Real ADB rc/stderr failure (device offline, etc.) on the
    refresh-open tap must still surface as a diagnosable detail -- the
    same STDERR-DETAIL-001 guarantee already given to every other tap
    in this flow."""

    cfg = _config()
    open_args = tuple(build_tap_args(cfg.screen_size, cfg.refresh_button_point))
    select_args = tuple(build_tap_args(cfg.screen_size, cfg.slot_select_points[0]))
    runner = FakeAdbRunner(
        capture_results={
            (_SERIAL, DEFAULT_CAPTURE_ARGS): AdbBinaryResult(
                serial=_SERIAL, args=DEFAULT_CAPTURE_ARGS, returncode=0,
                stdout_bytes=_VALID_PNG, stderr="",
            )
        },
        command_results={
            (_SERIAL, select_args): AdbCommandResult(
                serial=_SERIAL, args=select_args, returncode=0, stdout="", stderr="",
            ),
            (_SERIAL, open_args): AdbCommandResult(
                serial=_SERIAL, args=open_args, returncode=125,
                stdout="", stderr="error: device offline",
            ),
        },
    )
    # Confidently non-target, so the refresh loop is reached.
    recognizer = LabelMappingRecognizer(matching_labels=frozenset({_POPUP_ANCHOR, _POPUP_TITLE}))

    result = _run(runner, recognizer, cfg)

    assert result.outcome is BountyOutcome.CAPTURE_UNAVAILABLE
    assert "refresh-open tap failed" in result.detail
    assert "rc=125" in result.detail
    assert "error: device offline" in result.detail


def test_refresh_confirm_is_always_position_based_never_template_matched():
    """Same fix, applied to the confirm tap: a real
    'button_refresh_confirm' template configured but not confidently
    matching no longer blocks anything -- refresh-confirm always taps
    config.refresh_confirm_point directly once the popup is verified
    structurally (anchor/title both match), proven with a recognizer
    that only confirms the target phrase/quantity AFTER one
    refresh-open+confirm round-trip (never on the very first check),
    so a confirm tap is required to ever reach acceptance."""

    class _AcceptOnSecondCheckRecognizer:
        def __init__(self):
            self._phrase_checks = 0
            self.calls: list = []

        def recognize(self, image_bytes, roi, expected_label, threshold):
            self.calls.append(expected_label)
            if expected_label in {"mission_slot_unselected", "button_accept_mission", _POPUP_ANCHOR, _POPUP_TITLE}:
                return RecognitionResult(RecognitionStatus.MATCH, expected_label, 1.0, "test", (0.5, 0.5))
            if expected_label == _PHRASE:
                self._phrase_checks += 1
            if expected_label in (_PHRASE, _QTY) and self._phrase_checks >= 2:
                return RecognitionResult(RecognitionStatus.MATCH, expected_label, 1.0, "test", (0.5, 0.5))
            return RecognitionResult(RecognitionStatus.NO_MATCH, None, 0.05, "test")

    runner = _runner_with_valid_captures()
    recognizer = _AcceptOnSecondCheckRecognizer()
    cfg = _config(
        template_map={
            "mission_slot_unselected": "mission_slot_unselected.png",
            "button_refresh_confirm": "button_refresh_confirm.png",
            "button_accept_mission": "button_accept_mission.png",
        },
        max_kill_progress_poll_attempts=1,
    )

    result = _run(runner, recognizer, cfg)  # must not raise, must not hang

    assert result.outcome is BountyOutcome.KILL_PROGRESS_NOT_COMPLETE
    expected_args = tuple(build_tap_args(cfg.screen_size, cfg.refresh_confirm_point))
    assert (_SERIAL, expected_args) in runner.calls


# --- COMPLETE-SLOT-TRACKING-001: complete the slot that's ACTUALLY eligible


class _SlotAwareRunner:
    """Wraps a FakeAdbRunner; tracks which slot_select_points position
    was most recently tapped (state['current_slot']), so a paired
    recognizer can respond as if only ONE specific slot's own detail
    view is genuinely showing completion -- models the real UI, where
    the mission list's rows carry no per-row completion indicator and
    only an opened slot's own detail does."""

    def __init__(self, inner, state, slot_points, screen_size):
        self._inner = inner
        self._state = state
        self._slot_args = {
            i: tuple(build_tap_args(screen_size, pt)) for i, pt in enumerate(slot_points, start=1)
        }

    def list_devices(self):
        return self._inner.list_devices()

    def capture_binary(self, serial, args):
        return self._inner.capture_binary(serial, args)

    def run(self, serial, args):
        args_tuple = tuple(args)
        for slot_index, slot_args in self._slot_args.items():
            if args_tuple == slot_args:
                self._state["current_slot"] = slot_index
                break
        return self._inner.run(serial, args)

    @property
    def calls(self):
        return self._inner.calls

    @property
    def capture_calls(self):
        return self._inner.capture_calls


class _SlotAwareRecognizer:
    """The kill-progress counter only matches while state['current_slot']
    equals eligible_slot; every other configured label matches
    unconditionally (models the 5 slots all sharing the same acceptable
    phrase/quantity, and the later reward/result/list screens)."""

    def __init__(self, state, eligible_slot, always_matching):
        self._state = state
        self._eligible_slot = eligible_slot
        self._always = frozenset(always_matching)
        self.calls: list = []

    def recognize(self, image_bytes, roi, expected_label, threshold):
        self.calls.append(expected_label)
        if expected_label == _KILL_PROGRESS:
            if self._state.get("current_slot") == self._eligible_slot:
                return RecognitionResult(RecognitionStatus.MATCH, expected_label, 1.0, "test")
            return RecognitionResult(RecognitionStatus.UNKNOWN, None, 0.0, "test: not this slot")
        if expected_label in self._always:
            return RecognitionResult(RecognitionStatus.MATCH, expected_label, 1.0, "test")
        return RecognitionResult(RecognitionStatus.UNKNOWN, None, 0.0, "test: no match")


def test_completion_targets_the_slot_that_actually_became_eligible_not_row_1():
    """Real customer bug: select_complete_point always tapped row 1's
    position regardless of which slot actually became eligible -- a
    safe refusal (no wrong tap) when the eligible mission wasn't slot
    1, but never actually completed it either. Verifies slot 3
    specifically (not 1) is both detected as eligible AND the one
    re-selected for the complete tap."""

    cfg = _config()
    state: dict = {"current_slot": None}
    runner = _SlotAwareRunner(_runner_with_valid_captures(), state, cfg.slot_select_points, cfg.screen_size)
    recognizer = _SlotAwareRecognizer(
        state, eligible_slot=3,
        always_matching={_PHRASE, _QTY, _REWARD, _RESULT, _MISSION_LIST},
    )

    result = _run(runner, recognizer, cfg)

    assert result.outcome is BountyOutcome.COMPLETED_CYCLE
    slot_3_args = tuple(build_tap_args(cfg.screen_size, cfg.slot_select_points[2]))
    slot_1_args = tuple(build_tap_args(cfg.screen_size, cfg.slot_select_points[0]))
    # The re-select-for-complete tap (the one immediately followed by the
    # fixed complete_button_point tap) must be slot 3's position.
    complete_button_args = tuple(build_tap_args(cfg.screen_size, cfg.complete_button_point))
    complete_index = runner.calls.index((_SERIAL, complete_button_args))
    assert runner.calls[complete_index - 1] == (_SERIAL, slot_3_args)
    # Never blindly re-selects row 1 right before completing.
    assert runner.calls[complete_index - 1] != (_SERIAL, slot_1_args)


# --- RETRY-PACING-001: retry_delay_seconds must actually pace retries -----


def test_retry_delay_seconds_actually_paces_the_popup_verify_loop():
    """Real customer report: "refresh popup never verified" kept
    happening even after REFRESH-TRIGGER-CORRECTION-001's tap fix.
    Root cause: retry_delay_seconds was configured but never actually
    applied anywhere in this module -- every bounded verify loop fired
    its captures back-to-back with zero pause for the game's own UI
    transition to finish. Direct proof sleep_fn is called with
    retry_delay_seconds between (not after) popup-verify attempts."""

    sleep_calls: list[float] = []
    runner = _runner_with_valid_captures()
    # Popup anchor/title never match -- forces every popup-verify
    # attempt to miss, so the loop runs its full bound.
    recognizer = LabelMappingRecognizer(matching_labels=frozenset({_PHRASE}))
    cfg = _config(max_refresh_attempts=1, max_popup_verify_attempts=3, retry_delay_seconds=2.5)

    result = _run(runner, recognizer, cfg, sleep_fn=sleep_calls.append)

    assert result.outcome is BountyOutcome.REFRESH_POPUP_NOT_VERIFIED
    # 3 attempts -> exactly 2 pacing sleeps between them, never a 3rd
    # (no point pacing after the last attempt, about to give up anyway).
    assert sleep_calls == [2.5, 2.5]


def test_retry_delay_seconds_zero_is_a_real_but_instant_pace():
    """retry_delay_seconds: 0.0 (the test-harness/legacy default) must
    still invoke sleep_fn between attempts -- it's a real, valid pace
    value, not a signal to skip pacing entirely."""

    sleep_calls: list[float] = []
    runner = _runner_with_valid_captures()
    recognizer = LabelMappingRecognizer(matching_labels=frozenset({_PHRASE}))
    cfg = _config(max_refresh_attempts=1, max_popup_verify_attempts=2, retry_delay_seconds=0.0)

    _run(runner, recognizer, cfg, sleep_fn=sleep_calls.append)

    assert sleep_calls == [0.0]


# --- EARLY-COMPLETE-JUMP-001: stop touring once a slot is found complete


def test_early_complete_jump_stops_accepting_remaining_slots_once_one_is_eligible():
    """Real customer question: after finding a complete slot partway
    down the list, why keep touring/accepting the rest before acting
    on it? With slot 3 the eligible one, slots 4 and 5 must never be
    visited at all during this pass -- the accept loop jumps straight
    to completing slot 3 instead of finishing the walk first."""

    cfg = _config()
    state: dict = {"current_slot": None}
    runner = _SlotAwareRunner(_runner_with_valid_captures(), state, cfg.slot_select_points, cfg.screen_size)
    recognizer = _SlotAwareRecognizer(
        state, eligible_slot=3,
        always_matching={_PHRASE, _QTY, _REWARD, _RESULT, _MISSION_LIST},
    )

    result = _run(runner, recognizer, cfg)

    assert result.outcome is BountyOutcome.COMPLETED_CYCLE
    slot_4_args = (_SERIAL, tuple(build_tap_args(cfg.screen_size, cfg.slot_select_points[3])))
    slot_5_args = (_SERIAL, tuple(build_tap_args(cfg.screen_size, cfg.slot_select_points[4])))
    complete_button_args = (_SERIAL, tuple(build_tap_args(cfg.screen_size, cfg.complete_button_point)))
    complete_index = runner.calls.index(complete_button_args)
    calls_before_complete = runner.calls[: complete_index + 1]
    assert slot_4_args not in calls_before_complete
    assert slot_5_args not in calls_before_complete


# --- COMPLETE-RETRY-001: re-select and retry a missed complete tap --------


def test_complete_tap_retries_by_reselecting_instead_of_failing_on_first_miss():
    """Real customer question: if the complete tap doesn't confidently
    land, isn't the obvious fix to re-select and try again, instead of
    giving up immediately? First attempt's button_complete check
    misses (NO_MATCH), second attempt matches -- must still reach
    COMPLETED_CYCLE, having re-tapped the eligible slot's select point
    once per attempt."""

    class _CompleteRetryRecognizer:
        def __init__(self):
            self._complete_checks = 0
            self.calls: list = []

        def recognize(self, image_bytes, roi, expected_label, threshold):
            self.calls.append(expected_label)
            if expected_label == "button_complete":
                self._complete_checks += 1
                if self._complete_checks >= 2:
                    return RecognitionResult(RecognitionStatus.MATCH, expected_label, 1.0, "test", (0.5, 0.5))
                return RecognitionResult(RecognitionStatus.NO_MATCH, None, 0.05, "test")
            return RecognitionResult(RecognitionStatus.MATCH, expected_label, 1.0, "test", (0.5, 0.5))

    runner = _runner_with_valid_captures()
    recognizer = _CompleteRetryRecognizer()
    cfg = _config(template_map={"button_complete": "button_complete.png", "button_claim_reward": "reward_claim_button.png"})

    result = _run(runner, recognizer, cfg)

    assert result.outcome is BountyOutcome.COMPLETED_CYCLE
    # 1 initial-accept select + 2 select-complete taps (one per attempt,
    # the first of which missed and was retried) + 1 more for the
    # legacy stateless re-accept pass after claim (no runtime passed
    # here) = 4.
    slot_1_args = (_SERIAL, tuple(build_tap_args(cfg.screen_size, cfg.slot_select_points[0])))
    assert len([call for call in runner.calls if call == slot_1_args]) == 4
    assert recognizer.calls.count("button_complete") == 2


def test_complete_tap_failure_detail_reports_the_attempt_count():
    """A complete tap that never confidently lands within
    max_complete_verify_attempts must report that bound in the detail,
    not just a bare failure."""

    class _NeverCompleteRecognizer:
        def recognize(self, image_bytes, roi, expected_label, threshold):
            if expected_label == "button_complete":
                return RecognitionResult(RecognitionStatus.NO_MATCH, None, 0.05, "test")
            return RecognitionResult(RecognitionStatus.MATCH, expected_label, 1.0, "test", (0.5, 0.5))

    runner = _runner_with_valid_captures()
    recognizer = _NeverCompleteRecognizer()
    cfg = _config(template_map={"button_complete": "button_complete.png"}, max_complete_verify_attempts=2)

    result = _run(runner, recognizer, cfg)

    assert result.outcome is BountyOutcome.CAPTURE_UNAVAILABLE
    assert "Complete tap failed after 2 attempt(s)" in result.detail


# --- EARLY-COMPLETE-CHECK-001: don't re-walk slots already known complete


def test_early_complete_check_skips_the_redundant_kill_progress_reselect_pass():
    """Real reported inefficiency: after accepting a slot that's already
    complete, the old code still ran a WHOLE separate kill-progress
    polling pass that re-selected every locked slot again just to
    rediscover what the accept loop's own view already showed. With
    slot 1 the eligible one, its detail is only ever opened twice: once
    to accept it, once to re-select it right before the complete tap --
    never a third time in between for a redundant completion re-check."""

    cfg = _config()
    state: dict = {"current_slot": None}
    runner = _SlotAwareRunner(_runner_with_valid_captures(), state, cfg.slot_select_points, cfg.screen_size)
    recognizer = _SlotAwareRecognizer(
        state, eligible_slot=1,
        always_matching={_PHRASE, _QTY, _REWARD, _RESULT, _MISSION_LIST},
    )

    result = _run(runner, recognizer, cfg)

    assert result.outcome is BountyOutcome.COMPLETED_CYCLE
    # Only look at calls up to the complete tap: everything after that is
    # the separate post-claim re-accept pass (5 more selects, unrelated to
    # this check -- covered by test_full_cycle_reaches_completed_state_once).
    slot_1_args = (_SERIAL, tuple(build_tap_args(cfg.screen_size, cfg.slot_select_points[0])))
    complete_button_args = (_SERIAL, tuple(build_tap_args(cfg.screen_size, cfg.complete_button_point)))
    complete_index = runner.calls.index(complete_button_args)
    slot_1_selects_before_complete = [call for call in runner.calls[: complete_index + 1] if call == slot_1_args]
    assert len(slot_1_selects_before_complete) == 2


def test_kill_progress_polling_never_crosses_accounts_with_multiple_ld_instances():
    """LD-multi-instance safety: two independent accounts (their own
    runner/serial/recognizer), each with a DIFFERENT eligible slot,
    running concurrently in spirit (sequentially here, independent
    state) -- every select/complete/claim/close tap for each account
    must stay scoped to that account's own serial, and each completes
    its own correct slot, never the other's."""

    cfg = _config()
    serial_a, serial_b = _SERIAL, "127.0.0.1:6000"

    state_a: dict = {"current_slot": None}
    runner_a = _SlotAwareRunner(_runner_with_valid_captures(), state_a, cfg.slot_select_points, cfg.screen_size)
    recognizer_a = _SlotAwareRecognizer(state_a, eligible_slot=2, always_matching={_PHRASE, _QTY, _REWARD, _RESULT, _MISSION_LIST})

    state_b: dict = {"current_slot": None}
    inner_b = FakeAdbRunner(
        capture_results={(serial_b, DEFAULT_CAPTURE_ARGS): AdbBinaryResult(
            serial=serial_b, args=DEFAULT_CAPTURE_ARGS, returncode=0, stdout_bytes=_VALID_PNG, stderr="",
        )}
    )
    runner_b = _SlotAwareRunner(inner_b, state_b, cfg.slot_select_points, cfg.screen_size)
    recognizer_b = _SlotAwareRecognizer(state_b, eligible_slot=4, always_matching={_PHRASE, _QTY, _REWARD, _RESULT, _MISSION_LIST})

    result_a = run_one_cycle(account_id=AccountId.LD1, serial=serial_a, runner=runner_a, recognizer=recognizer_a, config=cfg)
    result_b = run_one_cycle(account_id=AccountId.LD2, serial=serial_b, runner=runner_b, recognizer=recognizer_b, config=cfg)

    assert result_a.outcome is BountyOutcome.COMPLETED_CYCLE
    assert result_b.outcome is BountyOutcome.COMPLETED_CYCLE
    # Every recorded call for each account used only that account's serial.
    assert all(call[0] == serial_a for call in runner_a.calls)
    assert all(call[0] == serial_b for call in runner_b.calls)
    # Each account's complete-tap sequence re-selected ITS OWN eligible
    # slot (2 for A, 4 for B) -- never the other account's.
    complete_button_args = tuple(build_tap_args(cfg.screen_size, cfg.complete_button_point))
    slot_2_args = tuple(build_tap_args(cfg.screen_size, cfg.slot_select_points[1]))
    slot_4_args = tuple(build_tap_args(cfg.screen_size, cfg.slot_select_points[3]))
    a_complete_index = runner_a.calls.index((serial_a, complete_button_args))
    b_complete_index = runner_b.calls.index((serial_b, complete_button_args))
    assert runner_a.calls[a_complete_index - 1] == (serial_a, slot_2_args)
    assert runner_b.calls[b_complete_index - 1] == (serial_b, slot_4_args)


# --- RESULT-CLOSE-CALIBRATION-001: close is always position-based ---------


def test_close_result_tap_uses_the_exact_configured_close_point_never_a_template():
    """The close step no longer attempts any "button_close_reward"
    template search at all (production deliberately never configures
    that key either -- the two lookalike buttons "보상 받기"/"닫기"
    cannot be told apart reliably by template matching alone, see
    RESULT-CLOSE-CALIBRATION-001) -- it always taps close_result_point
    directly."""

    runner = _runner_with_valid_captures()
    recognizer = LabelMappingRecognizer(matching_labels=_ALL_LABELS)
    cfg = _config()

    result = _run(runner, recognizer, cfg)

    assert result.outcome is BountyOutcome.COMPLETED_CYCLE
    expected_args = tuple(build_tap_args(cfg.screen_size, cfg.close_result_point))
    assert (_SERIAL, expected_args) in runner.calls
