"""Real-asset regression tests for RESULT-CLOSE-CALIBRATION-001.

A real customer live run repeatedly stalled on the post-claim "결과"
(result)/"닫기" (close) screen -- result_screen_roi/label/close_result_point/
button_close_reward had never been calibrated against any real capture.
The customer supplied a real 1280x720 Test-capture of that exact
screen.

Every test here uses the real, unmodified capture
(tests/fixtures/game_cal_001/source_extra/result_close_screen.png),
the real `OpenCVTemplateRecognizer`, and the real shipped
`configs/bounty.example.yaml` -- never a fake always-match recognizer.
Skipped (not failed) if OpenCV/numpy aren't installed.
"""

from pathlib import Path

import pytest

cv2 = pytest.importorskip("cv2")
np = pytest.importorskip("numpy")

from ldmanager.bounty_config import load_bounty_config
from ldmanager.recognition import OpenCVTemplateRecognizer

_FIXTURES = Path(__file__).parent / "fixtures" / "game_cal_001"
_RESULT_CLOSE_SCREEN = _FIXTURES / "source_extra" / "result_close_screen.png"
_OTHER_REAL_CAPTURES = (
    _FIXTURES / "source" / "completed_target.png",
    _FIXTURES / "source" / "in_progress_target.png",
    _FIXTURES / "source" / "non_target.png",
    _FIXTURES / "source_extra" / "mission_list_row1_completed.png",
)


def _load(path: Path) -> bytes:
    assert path.is_file(), f"Real fixture capture missing: {path}"
    return path.read_bytes()


@pytest.fixture(scope="module")
def config():
    return load_bounty_config(Path("configs/bounty.example.yaml"))


@pytest.fixture(scope="module")
def recognizer(config):
    return OpenCVTemplateRecognizer(templates_dir=config.templates_dir, template_map=config.template_map)


def test_real_result_close_capture_is_present_and_a_real_1280x720_png():
    data = _load(_RESULT_CLOSE_SCREEN)
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
    encoded = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    assert image is not None
    height, width = image.shape[:2]
    assert (width, height) == (1280, 720)


def test_result_screen_label_matches_the_real_result_close_screen(config, recognizer):
    result = recognizer.recognize(_load(_RESULT_CLOSE_SCREEN), config.result_screen_roi, config.result_screen_label, config.threshold)
    assert result.matched is True


def test_result_screen_label_never_matches_a_plain_detail_or_list_real_capture(config, recognizer):
    for path in _OTHER_REAL_CAPTURES:
        result = recognizer.recognize(_load(path), config.result_screen_roi, config.result_screen_label, config.threshold)
        assert result.matched is False, f"False positive result-screen match on {path.name}"


def test_mission_list_label_never_matches_the_real_result_close_screen(config, recognizer):
    """mission_list_label ("임무 목표") must confirm we've actually LEFT
    the popup and returned to a normal detail/list view -- it must
    never match while the result/close popup is still showing."""

    result = recognizer.recognize(_load(_RESULT_CLOSE_SCREEN), config.mission_list_roi, config.mission_list_label, config.threshold)
    assert result.matched is False


def test_mission_list_label_matches_every_plain_detail_or_list_real_capture(config, recognizer):
    for path in _OTHER_REAL_CAPTURES:
        result = recognizer.recognize(_load(path), config.mission_list_roi, config.mission_list_label, config.threshold)
        assert result.matched is True, f"mission_list_label unexpectedly failed to match {path.name}"


def test_button_close_reward_is_deliberately_not_configured():
    """RESULT-CLOSE-CALIBRATION-001: the "보상 받기"/"닫기" buttons share
    the same frame graphic and are too visually similar to reliably
    tell apart by template matching -- close always uses the real,
    measured close_result_point instead (see bounty_mission.py)."""

    config = load_bounty_config(Path("configs/bounty.example.yaml"))
    assert "button_close_reward" not in config.template_map
