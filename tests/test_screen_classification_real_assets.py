"""Real-asset regression tests for GAME-CAL-001's "REAL-CAPTURE REWORK".

v1.0.3-rc.1 was withdrawn because the customer's actual Test capture
still reported "Only 0/2 stable screen anchors matched" -- a fake/mock
recognizer test suite alone cannot catch that class of defect, since a
fake recognizer is never wrong about whether a real pixel crop actually
matches a real captured frame. Every test in this file therefore uses:

  - the REAL, customer-supplied, unmodified 1280x720 source captures in
    tests/fixtures/game_cal_001/source/ (see PROVENANCE.md there for
    exactly what each one shows and where every derived crop came from);
  - the REAL :class:`~ldmanager.recognition.OpenCVTemplateRecognizer`
    (never ``LabelMappingRecognizer``/``PlaceholderRecognizer``/any
    other always-match-or-never-match fake);
  - the REAL, shipped ``configs/bounty.example.yaml`` (via
    :func:`ldmanager.bounty_config.load_bounty_config`) -- so this
    suite fails the moment that file's calibration regresses, not just
    when the classification *logic* has a bug.

Skipped entirely (not failed) if OpenCV/numpy aren't installed in this
environment -- consistent with this project's ``pytest.importorskip``
pattern used for optional-dependency test files.
"""

from pathlib import Path

import pytest

cv2 = pytest.importorskip("cv2")
np = pytest.importorskip("numpy")

from ldmanager.adb import AdbBinaryResult
from ldmanager.bounty_config import load_bounty_config
from ldmanager.recognition import OpenCVTemplateRecognizer
from ldmanager.screen_classification import (
    MissionAssessment,
    MissionScreenState,
    assess_mission_target,
    classify_screen,
    complete_mission_if_verified,
)
from ldmanager.screenshot import DEFAULT_CAPTURE_ARGS
from tests.fakes import FakeAdbRunner

_FIXTURES = Path(__file__).parent / "fixtures" / "game_cal_001" / "source"
_SERIAL = "127.0.0.1:5555"


def _load(name: str) -> bytes:
    path = _FIXTURES / name
    assert path.is_file(), f"Real fixture capture missing: {path}"
    return path.read_bytes()


@pytest.fixture(scope="module")
def config():
    return load_bounty_config(Path("configs/bounty.example.yaml"))


@pytest.fixture(scope="module")
def recognizer(config):
    return OpenCVTemplateRecognizer(templates_dir=config.templates_dir, template_map=config.template_map)


def _runner_for(name: str) -> FakeAdbRunner:
    data = _load(name)
    return FakeAdbRunner(
        capture_results={
            (_SERIAL, DEFAULT_CAPTURE_ARGS): AdbBinaryResult(
                serial=_SERIAL, args=DEFAULT_CAPTURE_ARGS, returncode=0, stdout_bytes=data, stderr="",
            )
        }
    )


# --- the real fixture files must actually exist and be real PNGs -----------


def test_real_fixture_captures_are_present_and_are_real_1280x720_pngs():
    for name in ("completed_target.png", "in_progress_target.png", "non_target.png"):
        data = _load(name)
        assert data.startswith(b"\x89PNG\r\n\x1a\n")
        encoded = np.frombuffer(data, dtype=np.uint8)
        image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        assert image is not None
        height, width = image.shape[:2]
        assert (width, height) == (1280, 720)


# --- stable_screen_anchors: real, variable-title screens never MISMATCH ----


def test_completed_real_capture_never_mismatches(config, recognizer):
    result = classify_screen(_load("completed_target.png"), config, recognizer)
    assert result.state is not MissionScreenState.MISMATCH


def test_in_progress_real_capture_never_mismatches(config, recognizer):
    """Variable mission title must not cause a MISMATCH: this capture's
    own mission-list panel title is still "자유 토벌작전" (a title,
    never a stable_screen_anchors entry -- see PROVENANCE.md)."""
    result = classify_screen(_load("in_progress_target.png"), config, recognizer)
    assert result.state is not MissionScreenState.MISMATCH


def test_non_target_real_capture_never_mismatches(config, recognizer):
    """This capture's mission title is a COMPLETELY DIFFERENT one ("야왕궁
    토벌작전") from the other two ("자유 토벌작전") -- proving the
    stable-anchor screen-layout gate really is title-independent, not
    just coincidentally reusing the same title's chrome."""
    result = classify_screen(_load("non_target.png"), config, recognizer)
    assert result.state is not MissionScreenState.MISMATCH


# --- explicit five-way classification on the real captures ------------------


def test_completed_real_capture_classifies_completed(config, recognizer):
    result = classify_screen(_load("completed_target.png"), config, recognizer)
    assert result.state is MissionScreenState.COMPLETED


def test_in_progress_real_capture_never_classifies_completed(config, recognizer):
    """The real "16/165" target-in-progress capture must never be
    treated as completed."""
    result = classify_screen(_load("in_progress_target.png"), config, recognizer)
    assert result.state is not MissionScreenState.COMPLETED


def test_non_target_real_capture_never_classifies_completed(config, recognizer):
    """The real "0/450" non-target capture must never be treated as
    completed either."""
    result = classify_screen(_load("non_target.png"), config, recognizer)
    assert result.state is not MissionScreenState.COMPLETED


# --- mission-title/target classification on the real captures --------------


def test_completed_real_capture_is_target_confirmed(config, recognizer):
    runner = _runner_for("completed_target.png")
    assert assess_mission_target(runner, _SERIAL, config, recognizer) is MissionAssessment.TARGET_CONFIRMED


def test_in_progress_real_capture_is_target_confirmed(config, recognizer):
    """Same objective phrase ("모든 몬스터 처치") as the completed
    capture, just a different mission instance/progress -- still the
    target objective, just not yet completed (so still zero-touch, see
    below)."""
    runner = _runner_for("in_progress_target.png")
    assert assess_mission_target(runner, _SERIAL, config, recognizer) is MissionAssessment.TARGET_CONFIRMED


def test_target_phrase_with_different_count_is_not_a_refresh_candidate(config, recognizer):
    """The real 16/165 target frame lacks the exact initial 0/200 crop.
    The replacement-slot assessment must still preserve its objective.
    """
    runner = _runner_for("in_progress_target.png")
    assert assess_mission_target(
        runner, _SERIAL, config, recognizer, require_initial_zero=True,
    ) is MissionAssessment.TARGET_CONFIRMED


def test_different_objective_with_different_count_stays_non_target(config, recognizer):
    runner = _runner_for("non_target.png")
    assert assess_mission_target(
        runner, _SERIAL, config, recognizer, require_initial_zero=True,
    ) is MissionAssessment.NON_TARGET_CONFIRMED


def test_non_target_real_capture_is_not_target_confirmed(config, recognizer):
    """Different objective phrase ("냉혈사 처치") -- must never be
    confused with the target."""
    runner = _runner_for("non_target.png")
    assessment = assess_mission_target(runner, _SERIAL, config, recognizer)
    assert assessment is not MissionAssessment.TARGET_CONFIRMED


# --- complete_mission_if_verified: real zero-touch guarantees --------------


def test_complete_mission_if_verified_taps_only_the_real_completed_capture(config, recognizer):
    runner = _runner_for("completed_target.png")
    result = complete_mission_if_verified(serial=_SERIAL, runner=runner, recognizer=recognizer, config=config)
    assert result.precondition is MissionScreenState.COMPLETED
    assert result.mission_target is MissionAssessment.TARGET_CONFIRMED
    assert result.tap_sent is True
    assert len(runner.calls) == 1
    assert runner.calls[0][0] == _SERIAL


def test_complete_mission_if_verified_zero_touch_for_real_in_progress_16_of_165(config, recognizer):
    """Real evidence: 16/165 target-in-progress must produce zero ADB
    taps of any kind."""
    runner = _runner_for("in_progress_target.png")
    result = complete_mission_if_verified(serial=_SERIAL, runner=runner, recognizer=recognizer, config=config)
    assert result.tap_sent is False
    assert result.ok is False
    assert runner.calls == []


def test_complete_mission_if_verified_zero_touch_for_real_non_target_0_of_450(config, recognizer):
    """Real evidence: the non-target 0/450 mission (with its own
    currency action + 순간 이동 button visible) must produce zero ADB
    taps of any kind -- 순간 이동 is never even a configured/searched
    label anywhere in this project, so it can never be tapped by this
    code path regardless."""
    runner = _runner_for("non_target.png")
    result = complete_mission_if_verified(serial=_SERIAL, runner=runner, recognizer=recognizer, config=config)
    assert result.tap_sent is False
    assert result.ok is False
    assert runner.calls == []
