from pathlib import Path

from ldmanager.adb import AdbBinaryResult
from ldmanager.coordinates import RelativeCoordinate, RelativeRegion, ScreenSize
from ldmanager.runtime import AccountMissionRuntime, SlotState, VerificationError, click_and_verify
from ldmanager.screenshot import DEFAULT_CAPTURE_ARGS
from tests.fakes import FakeAdbRunner, LabelMappingRecognizer


PNG = b"\x89PNG\r\n\x1a\n" + b"fixture"
SERIAL = "127.0.0.1:5555"
ROI = RelativeRegion(0, 0, 1, 1)


def _runner():
    return FakeAdbRunner(capture_results={(SERIAL, DEFAULT_CAPTURE_ARGS): AdbBinaryResult(SERIAL, DEFAULT_CAPTURE_ARGS, 0, PNG, "")})


def test_runtime_slots_are_independent_and_reset_only_when_explicit():
    one, two = AccountMissionRuntime(), AccountMissionRuntime()
    one.slots[0] = SlotState.TARGET_LOCKED
    one.slots[1] = SlotState.NON_TARGET
    assert one.locked_count == 1
    assert two.locked_count == 0
    one.reset_after_verified_return(next_slot_index=4)
    assert one.slots == [SlotState.UNKNOWN] * 5
    assert one.next_slot_index == 4


def test_click_and_verify_requires_expected_template():
    runner = _runner()
    outcome = click_and_verify(
        runner=runner, serial=SERIAL, screen=ScreenSize(100, 100), point=RelativeCoordinate(.5, .5),
        recognizer=LabelMappingRecognizer(frozenset({"next"})), expected_label="next", expected_roi=ROI,
        threshold=.8, should_stop=lambda: False,
    )
    assert outcome is None
    assert runner.calls and runner.calls[0][0] == SERIAL


def test_click_and_verify_saves_stale_screen(tmp_path: Path):
    outcome = click_and_verify(
        runner=_runner(), serial=SERIAL, screen=ScreenSize(100, 100), point=RelativeCoordinate(.5, .5),
        recognizer=LabelMappingRecognizer(), expected_label="next", expected_roi=ROI, threshold=.8,
        should_stop=lambda: False, attempts=2, diagnostics_dir=tmp_path,
    )
    assert outcome is VerificationError.STALE_SCREEN
    assert list(tmp_path.glob("*.png"))


def test_click_and_verify_honors_stop_before_tap():
    runner = _runner()
    outcome = click_and_verify(
        runner=runner, serial=SERIAL, screen=ScreenSize(100, 100), point=RelativeCoordinate(.5, .5),
        recognizer=LabelMappingRecognizer(), expected_label="next", expected_roi=ROI, threshold=.8,
        should_stop=lambda: True,
    )
    assert outcome is VerificationError.STOPPED
    assert runner.calls == []
