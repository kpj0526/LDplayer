from pathlib import Path

from ldmanager.adb import AdbBinaryResult
from ldmanager.coordinates import RelativeCoordinate, RelativeRegion, ScreenSize
from ldmanager.mission import MissionOutcome, run_one_cycle
from ldmanager.mission_config import MissionConfig
from ldmanager.models import AccountId
from ldmanager.recognition import PlaceholderRecognizer
from ldmanager.screenshot import DEFAULT_CAPTURE_ARGS
from tests.fakes import FakeAdbRunner, LabelMappingRecognizer

_VALID_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
_SERIAL = "127.0.0.1:5555"
_TARGET = "TARGET"
_KILL = "200/200"
_CLAIMED = "claimed"
_READY = "ready"


def _config(**overrides) -> MissionConfig:
    small_roi = RelativeRegion(x=0.0, y=0.0, width=0.1, height=0.1)
    defaults = dict(
        target_label=_TARGET,
        slot_rois=tuple(
            RelativeRegion(x=0.1 * i, y=0.0, width=0.05, height=0.05) for i in range(5)
        ),
        reroll_point=RelativeCoordinate(x=0.1, y=0.9),
        kill_check_roi=small_roi,
        kill_check_label=_KILL,
        claim_point=RelativeCoordinate(x=0.5, y=0.5),
        claimed_roi=small_roi,
        claimed_label=_CLAIMED,
        reset_point=RelativeCoordinate(x=0.9, y=0.9),
        ready_roi=small_roi,
        ready_label=_READY,
        screen_size=ScreenSize(width=1000, height=1000),
        templates_dir=Path("templates"),
        threshold=0.8,
        max_capture_attempts=2,
        max_reroll_attempts=3,
        max_kill_check_attempts=3,
        max_claim_verify_attempts=2,
        max_reset_verify_attempts=2,
        retry_delay_seconds=0.0,
        capture_args=DEFAULT_CAPTURE_ARGS,
    )
    defaults.update(overrides)
    return MissionConfig(**defaults)


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
        account_id=AccountId.LD1,
        serial=_SERIAL,
        runner=runner,
        recognizer=recognizer,
        config=config,
        **kwargs,
    )


# --- happy path: reaches every core state exactly once --------------------


def test_mock_cycle_reaches_all_core_states_once():
    runner = _runner_with_valid_captures()
    recognizer = LabelMappingRecognizer(
        matching_labels=frozenset({_TARGET, _KILL, _CLAIMED, _READY})
    )

    result = _run(runner, recognizer, _config())

    assert result.outcome is MissionOutcome.COMPLETED
    assert len(result.slots) == 5
    assert all(slot.matched and slot.attempts == 1 for slot in result.slots)
    # No reroll touches needed (every slot matched first try); exactly the
    # claim and reset taps were sent, each exactly once.
    assert len(runner.calls) == 2
    claim_args = tuple(runner.calls[0][1])
    reset_args = tuple(runner.calls[1][1])
    assert claim_args != reset_args


# --- bounded reroll: no infinite click when recognition never matches ----


def test_recognition_never_matching_is_bounded_not_infinite():
    runner = _runner_with_valid_captures()
    recognizer = PlaceholderRecognizer()  # always UNKNOWN -- never matches

    result = _run(runner, recognizer, _config(max_reroll_attempts=3))

    assert result.outcome is MissionOutcome.SLOT_RECOGNITION_FAILED
    assert len(result.slots) == 1
    assert result.slots[0].attempts == 3
    # Reroll touched only between attempts: attempts=3 -> 2 reroll touches.
    assert len(runner.calls) == 2
    assert len(runner.capture_calls) == 3


# --- stop: zero touches, no matter what -----------------------------------


def test_should_stop_true_from_start_sends_zero_touches():
    runner = _runner_with_valid_captures()
    recognizer = LabelMappingRecognizer(matching_labels=frozenset({_TARGET}))

    result = _run(runner, recognizer, _config(), should_stop=lambda: True)

    assert result.outcome is MissionOutcome.STOPPED
    assert result.slots == ()
    assert runner.calls == []
    assert runner.capture_calls == []


def test_stop_requested_after_first_slot_halts_with_no_touches_needed():
    stop_flag = {"stop": False}

    def should_stop():
        return stop_flag["stop"]

    def on_slot_start(index):
        if index == 2:
            stop_flag["stop"] = True

    runner = _runner_with_valid_captures()
    recognizer = LabelMappingRecognizer(matching_labels=frozenset({_TARGET}))

    result = _run(
        runner, recognizer, _config(),
        should_stop=should_stop, on_slot_start=on_slot_start,
    )

    assert result.outcome is MissionOutcome.STOPPED
    assert len(result.slots) == 1
    assert result.slots[0].matched is True
    assert runner.calls == []  # matching slots never need a touch
    assert len(runner.capture_calls) == 1


# --- kill-check: bounded, zero touches while polling ----------------------


def test_kill_check_never_matching_is_bounded_with_zero_touches():
    runner = _runner_with_valid_captures()
    recognizer = LabelMappingRecognizer(matching_labels=frozenset({_TARGET}))  # never _KILL

    result = _run(runner, recognizer, _config(max_kill_check_attempts=3))

    assert result.outcome is MissionOutcome.KILL_CHECK_FAILED
    assert len(result.slots) == 5
    assert runner.calls == []  # kill-check never touches anything


# --- claim / reset: exactly one touch each, no repeat on failure ---------


def test_claim_failure_sends_exactly_one_touch_no_repeat():
    runner = _runner_with_valid_captures()
    recognizer = LabelMappingRecognizer(matching_labels=frozenset({_TARGET, _KILL}))  # never _CLAIMED

    result = _run(runner, recognizer, _config(max_claim_verify_attempts=2))

    assert result.outcome is MissionOutcome.CLAIM_FAILED
    assert len(runner.calls) == 1  # the claim tap, sent exactly once


def test_reset_failure_sends_exactly_two_touches_no_repeat():
    runner = _runner_with_valid_captures()
    recognizer = LabelMappingRecognizer(
        matching_labels=frozenset({_TARGET, _KILL, _CLAIMED})  # never _READY
    )

    result = _run(runner, recognizer, _config(max_reset_verify_attempts=2))

    assert result.outcome is MissionOutcome.RESET_FAILED
    assert len(runner.calls) == 2  # claim + reset taps, neither repeated


# --- capture unavailable at a slot -----------------------------------------


def test_capture_failure_exhausted_is_reported_without_touching_anything():
    runner = FakeAdbRunner(
        capture_results={
            (_SERIAL, DEFAULT_CAPTURE_ARGS): AdbBinaryResult(
                serial=_SERIAL, args=DEFAULT_CAPTURE_ARGS, returncode=1,
                stdout_bytes=b"", stderr="offline",
            )
        }
    )
    recognizer = LabelMappingRecognizer(matching_labels=frozenset({_TARGET}))

    result = _run(runner, recognizer, _config(max_reroll_attempts=2))

    assert result.outcome is MissionOutcome.CAPTURE_UNAVAILABLE
    assert runner.calls == []
    assert len(runner.capture_calls) == 2
