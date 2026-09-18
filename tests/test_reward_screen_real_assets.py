"""Real-asset regression tests for REWARD-SCREEN-CALIBRATION-001.

A real customer live run reached the actual "보상 받기" (Get Reward)
screen for the first time (all 5 slots really accepted, real complete
tap sent) and then stalled with `reward_verify_failed` -- the
`reward_screen_roi`/`reward_screen_label`/`claim_point` fields had
never been calibrated against any real capture (only the initial
Mission > Region > detail screen was, in GAME-CAL-001). The customer
then supplied a real 1280x720 Test-capture of that exact screen.

Every test here uses the real, unmodified capture
(tests/fixtures/game_cal_001/source_extra/reward_screen.png), the real
`OpenCVTemplateRecognizer`, and the real shipped
`configs/bounty.example.yaml` -- never a fake always-match recognizer.
Skipped (not failed) if OpenCV/numpy aren't installed, matching this
project's existing pattern for this kind of test file.
"""

from pathlib import Path

import pytest

cv2 = pytest.importorskip("cv2")
np = pytest.importorskip("numpy")

from ldmanager.bounty_config import load_bounty_config
from ldmanager.recognition import OpenCVTemplateRecognizer

_FIXTURES = Path(__file__).parent / "fixtures" / "game_cal_001"
_REWARD_SCREEN = _FIXTURES / "source_extra" / "reward_screen.png"
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


def test_real_reward_screen_capture_is_present_and_a_real_1280x720_png():
    data = _load(_REWARD_SCREEN)
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
    encoded = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    assert image is not None
    height, width = image.shape[:2]
    assert (width, height) == (1280, 720)


def test_reward_screen_label_matches_only_the_real_reward_screen(config, recognizer):
    result = recognizer.recognize(_load(_REWARD_SCREEN), config.reward_screen_roi, config.reward_screen_label, config.threshold)
    assert result.matched is True


def test_reward_screen_label_never_matches_any_other_real_capture(config, recognizer):
    """Guards against a false positive: none of the other real, already-
    calibrated captures (mission-detail/list screens, none of which are
    the reward screen) may ever be mistaken for it."""

    for path in _OTHER_REAL_CAPTURES:
        result = recognizer.recognize(_load(path), config.reward_screen_roi, config.reward_screen_label, config.threshold)
        assert result.matched is False, f"False positive reward-screen match on {path.name}"


def test_claim_button_template_matches_only_the_real_reward_screen(config, recognizer):
    from ldmanager.coordinates import RelativeRegion

    full_screen = RelativeRegion(x=0.0, y=0.0, width=1.0, height=1.0)
    result = recognizer.recognize(_load(_REWARD_SCREEN), full_screen, "button_claim_reward", config.threshold)
    assert result.matched is True


def test_claim_button_template_never_matches_any_other_real_capture(config, recognizer):
    from ldmanager.coordinates import RelativeRegion

    full_screen = RelativeRegion(x=0.0, y=0.0, width=1.0, height=1.0)
    for path in _OTHER_REAL_CAPTURES:
        result = recognizer.recognize(_load(path), full_screen, "button_claim_reward", config.threshold)
        assert result.matched is False, f"False positive claim-button match on {path.name}"
