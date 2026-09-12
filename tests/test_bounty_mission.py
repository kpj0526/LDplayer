from pathlib import Path

from ldmanager.adb import AdbBinaryResult
from ldmanager.bounty_config import BountyMissionConfig
from ldmanager.bounty_mission import BountyOutcome, run_one_cycle
from ldmanager.coordinates import RelativeCoordinate, RelativeRegion, ScreenSize, build_tap_args
from ldmanager.models import AccountId
from ldmanager.recognition import PlaceholderRecognizer
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
