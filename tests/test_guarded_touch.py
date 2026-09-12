import pytest

from ldmanager.adb import AdbBinaryResult, AdbCommandResult
from ldmanager.coordinates import InvalidCoordinateError, RelativeCoordinate, ScreenSize
from ldmanager.guarded_touch import TouchOutcome, perform_guarded_touch
from ldmanager.models import AccountId
from ldmanager.screenshot import DEFAULT_CAPTURE_ARGS
from tests.fakes import FakeAdbRunner

_VALID_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
_SERIAL = "127.0.0.1:5555"
_SIZE = ScreenSize(width=1080, height=1920)
_POINT = RelativeCoordinate(x=0.5, y=0.5)
_TAP_ARGS = ("shell", "input", "tap", "540", "960")


def _ok_capture_result():
    return AdbBinaryResult(
        serial=_SERIAL, args=DEFAULT_CAPTURE_ARGS, returncode=0,
        stdout_bytes=_VALID_PNG, stderr="",
    )


def _failing_capture_result():
    return AdbBinaryResult(
        serial=_SERIAL, args=DEFAULT_CAPTURE_ARGS, returncode=1,
        stdout_bytes=b"", stderr="device offline",
    )


def _runner_with_capture(result):
    return FakeAdbRunner(capture_results={(_SERIAL, DEFAULT_CAPTURE_ARGS): result})


def _call(runner, **overrides):
    kwargs = dict(
        account_id=AccountId.LD1,
        serial=_SERIAL,
        runner=runner,
        screen_size=_SIZE,
        point=_POINT,
        precondition=lambda b: True,
        postcondition=lambda b: True,
        max_capture_attempts=3,
        max_postcondition_attempts=3,
        sleep_fn=lambda s: None,
    )
    kwargs.update(overrides)
    return perform_guarded_touch(**kwargs)


# --- happy path: exactly one touch, two captures -------------------------


def test_successful_touch_sends_exactly_one_tap_and_two_captures():
    runner = _runner_with_capture(_ok_capture_result())

    result = _call(runner)

    assert result.outcome is TouchOutcome.SUCCESS
    assert result.touched is True
    assert result.ok is True
    assert result.account_id is AccountId.LD1
    assert runner.calls == [(_SERIAL, _TAP_ARGS)]
    assert runner.capture_calls == [
        (_SERIAL, DEFAULT_CAPTURE_ARGS),
        (_SERIAL, DEFAULT_CAPTURE_ARGS),
    ]


# --- precondition: false / error -> zero touches --------------------------


def test_precondition_false_emits_zero_touches():
    runner = _runner_with_capture(_ok_capture_result())

    result = _call(runner, precondition=lambda b: False)

    assert result.outcome is TouchOutcome.PRECONDITION_REJECTED
    assert result.touched is False
    assert runner.calls == []
    assert runner.capture_calls == [(_SERIAL, DEFAULT_CAPTURE_ARGS)]  # only pre-capture


def test_precondition_raising_emits_zero_touches():
    def boom(_bytes):
        raise RuntimeError("low confidence")

    runner = _runner_with_capture(_ok_capture_result())

    result = _call(runner, precondition=boom)

    assert result.outcome is TouchOutcome.PRECONDITION_ERROR
    assert result.touched is False
    assert runner.calls == []


# --- pre-touch capture failure / invalid bytes -> zero touches, bounded --


def test_capture_failure_before_touch_emits_zero_touches_with_bounded_retries():
    runner = _runner_with_capture(_failing_capture_result())

    result = _call(runner, max_capture_attempts=3)

    assert result.outcome is TouchOutcome.CAPTURE_FAILED
    assert result.touched is False
    assert result.capture_attempts == 3
    assert runner.calls == []
    assert len(runner.capture_calls) == 3  # exactly the bound, no more


def test_invalid_image_bytes_before_touch_is_controlled_failure():
    bad = AdbBinaryResult(
        serial=_SERIAL, args=DEFAULT_CAPTURE_ARGS, returncode=0,
        stdout_bytes=b"not a png", stderr="",
    )
    runner = _runner_with_capture(bad)

    result = _call(runner, max_capture_attempts=1)

    assert result.outcome is TouchOutcome.CAPTURE_FAILED
    assert result.touched is False
    assert runner.calls == []


def test_capture_succeeding_on_a_later_attempt_still_proceeds():
    # First attempt fails, second succeeds -- within the bound, so the
    # flow proceeds normally to a single touch.
    calls = {"n": 0}
    results = [_failing_capture_result(), _ok_capture_result()]

    class FlakyOnceRunner(FakeAdbRunner):
        def capture_binary(self, serial, args):
            outcome = results[min(calls["n"], len(results) - 1)]
            calls["n"] += 1
            self.capture_calls.append((serial, tuple(args)))
            return outcome

    runner = FlakyOnceRunner()
    result = _call(runner, max_capture_attempts=3)

    assert result.outcome is TouchOutcome.SUCCESS
    assert result.capture_attempts == 2
    assert len(runner.calls) == 1


# --- touch command itself failing -> no repeat touch, no post-capture ----


def test_touch_command_failure_is_reported_without_repeat_touch():
    runner = _runner_with_capture(_ok_capture_result())
    runner.command_results[(_SERIAL, _TAP_ARGS)] = AdbCommandResult(
        serial=_SERIAL, args=_TAP_ARGS, returncode=1, stdout="", stderr="input failed"
    )

    result = _call(runner)

    assert result.outcome is TouchOutcome.TOUCH_FAILED
    assert result.touched is True
    assert len(runner.calls) == 1  # exactly one attempt, never repeated
    # Only the pre-touch capture happened; no post-capture after a failed tap.
    assert runner.capture_calls == [(_SERIAL, DEFAULT_CAPTURE_ARGS)]


# --- postcondition: false / error / capture failure -> no repeat touch --


def test_postcondition_never_satisfied_sends_no_repeated_touch():
    runner = _runner_with_capture(_ok_capture_result())

    result = _call(runner, postcondition=lambda b: False, max_postcondition_attempts=3)

    assert result.outcome is TouchOutcome.POSTCONDITION_REJECTED
    assert result.touched is True
    assert result.verify_attempts == 3
    assert len(runner.calls) == 1  # still just the one tap
    # 1 pre-capture + 3 post-capture attempts
    assert len(runner.capture_calls) == 4


def test_postcondition_raising_sends_no_repeated_touch():
    def boom(_bytes):
        raise RuntimeError("verification crashed")

    runner = _runner_with_capture(_ok_capture_result())

    result = _call(runner, postcondition=boom)

    assert result.outcome is TouchOutcome.POSTCONDITION_ERROR
    assert result.touched is True
    assert len(runner.calls) == 1


def test_post_capture_failure_sends_no_repeated_touch():
    class PrePassPostFailRunner(FakeAdbRunner):
        def capture_binary(self, serial, args):
            self.capture_calls.append((serial, tuple(args)))
            if len(self.capture_calls) == 1:
                return _ok_capture_result()
            return _failing_capture_result()

    runner = PrePassPostFailRunner()
    result = _call(runner, max_postcondition_attempts=3)

    assert result.outcome is TouchOutcome.POST_CAPTURE_FAILED
    assert result.touched is True
    assert len(runner.calls) == 1  # tap sent exactly once
    assert len(runner.capture_calls) == 1 + 3  # 1 pre + bounded 3 post attempts


# --- invalid coordinates never reach the touch flow -----------------------


def test_invalid_relative_coordinate_cannot_reach_touch_flow():
    runner = FakeAdbRunner()
    with pytest.raises(InvalidCoordinateError):
        bad_point = RelativeCoordinate(x=1.5, y=0.5)
        _call(runner, point=bad_point)  # never reached
    assert runner.calls == []
    assert runner.capture_calls == []


# --- serial validation -----------------------------------------------------


def test_blank_serial_is_rejected_before_any_capture_or_touch():
    runner = FakeAdbRunner()
    with pytest.raises(ValueError):
        _call(runner, serial="")
    assert runner.calls == []
    assert runner.capture_calls == []


def test_whitespace_only_serial_is_rejected_before_any_capture_or_touch():
    runner = FakeAdbRunner()
    with pytest.raises(ValueError):
        _call(runner, serial="   ")
    assert runner.calls == []
    assert runner.capture_calls == []


# --- per-account error containment / result identity ----------------------


def test_results_are_account_local_and_independent_across_runners():
    runner_a = _runner_with_capture(_ok_capture_result())
    runner_b = _runner_with_capture(_failing_capture_result())

    result_a = perform_guarded_touch(
        account_id=AccountId.LD1, serial=_SERIAL, runner=runner_a,
        screen_size=_SIZE, point=_POINT,
        precondition=lambda b: True, postcondition=lambda b: True,
        sleep_fn=lambda s: None,
    )
    result_b = perform_guarded_touch(
        account_id=AccountId.LD2, serial=_SERIAL, runner=runner_b,
        screen_size=_SIZE, point=_POINT,
        precondition=lambda b: True, postcondition=lambda b: True,
        max_capture_attempts=2, sleep_fn=lambda s: None,
    )

    assert result_a.account_id is AccountId.LD1
    assert result_a.outcome is TouchOutcome.SUCCESS
    assert result_b.account_id is AccountId.LD2
    assert result_b.outcome is TouchOutcome.CAPTURE_FAILED
    assert result_b.touched is False

    # Failure for LD2's runner never touched LD1's runner state.
    assert runner_a.calls == [(_SERIAL, _TAP_ARGS)]
    assert runner_b.calls == []


def test_result_detail_never_contains_image_bytes():
    runner = _runner_with_capture(_ok_capture_result())
    result = _call(runner)
    assert _VALID_PNG not in result.detail.encode("utf-8", errors="ignore")
