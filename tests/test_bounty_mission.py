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
    # 10 slot outcomes: 5 initial accepts + 5 re-accepts after claim.
    assert len(result.slots) == 10
    assert all(s.accepted for s in result.slots)
    # No slot needed a refresh (already acceptable): only select taps
    # for 10 slot-visits + select-complete + complete + claim + close = 14.
    assert len(runner.calls) == 5 + 5 + 4


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
    # Only the 5 slot-select taps happened; nothing for complete/reward/claim.
    assert len(runner.calls) == 5


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

    assert result.outcome is BountyOutcome.CAPTURE_UNAVAILABLE
    assert "select tap failed" not in result.detail
    # Reached (and failed at) the NEXT step instead -- proof slot
    # selection itself was never the blocker here.
    assert "refresh-open tap failed" in result.detail


def test_slot_select_tap_uses_the_exact_configured_slot_select_point():
    """Direct proof the select tap argv matches slot_select_points[N-1]
    -- never a template-derived coordinate, never another slot's point."""

    runner = _runner_with_valid_captures()
    recognizer = LabelMappingRecognizer(matching_labels=_ALL_LABELS)  # slot 1 accepted immediately
    cfg = _config()

    _run(runner, recognizer, cfg)

    expected_args = tuple(build_tap_args(cfg.screen_size, cfg.slot_select_points[0]))
    assert (_SERIAL, expected_args) in runner.calls


def test_refresh_open_dynamic_template_no_match_is_a_structured_error_not_a_crash():
    """Same bug class, second occurrence: a real 'button_refresh_4400'
    (etc.) template configured but not confidently matching previously
    raised UnboundLocalError('open_popup')."""

    runner = _runner_with_valid_captures()
    # Selects successfully (mission_slot_unselected matches) but is
    # confidently non-target (so the refresh loop is reached) -- never
    # matches the phrase/quantity, nor any refresh-cost variant.
    recognizer = _ConfidentNoMatchRecognizer(matching_labels={"mission_slot_unselected"})
    cfg = _config(
        template_map={
            "mission_slot_unselected": "mission_slot_unselected.png",
            "button_refresh_4400": "button_refresh_4400.png",
        },
        max_refresh_attempts=1,
    )

    result = _run(runner, recognizer, cfg)  # must not raise

    assert result.outcome is BountyOutcome.CAPTURE_UNAVAILABLE
    assert "refresh-open tap failed" in result.detail
    assert "template-based tap" in result.detail


def test_refresh_confirm_dynamic_template_no_match_is_a_structured_error_not_a_crash():
    """Same bug class, third occurrence: a real 'button_refresh_confirm'
    template configured but not confidently matching previously raised
    UnboundLocalError('confirm'). Select and refresh-open both succeed
    via a CONFIDENT dynamic match (a non-empty template_map makes any
    *unconfigured* asset a hard False, never a silent fixed-point
    fallback -- see _tap_template/_tap_any_template), and the popup IS
    verified (anchor/title both match) -- isolating the failure to the
    confirm tap alone."""

    runner = _runner_with_valid_captures()
    recognizer = _ConfidentNoMatchRecognizer(
        matching_labels={"mission_slot_unselected", "button_refresh_4400", _POPUP_ANCHOR, _POPUP_TITLE}
    )
    cfg = _config(
        template_map={
            "mission_slot_unselected": "mission_slot_unselected.png",
            "button_refresh_4400": "button_refresh_4400.png",
            "button_refresh_confirm": "button_refresh_confirm.png",
        },
        max_refresh_attempts=1, max_popup_verify_attempts=1,
    )

    result = _run(runner, recognizer, cfg)  # must not raise

    assert result.outcome is BountyOutcome.CAPTURE_UNAVAILABLE
    assert "refresh-confirm tap failed" in result.detail
    assert "template-based tap" in result.detail
