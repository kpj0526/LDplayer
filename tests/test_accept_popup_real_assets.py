"""Real-asset regression tests for ACCEPT-CONFIRM-001.

A real customer live run got stuck on the mission-detail popup that
opens after selecting a slot whose target phrase/quantity was ALREADY
matched (no refresh needed) -- the flow never tapped that popup's
"확인" button in that case, leaving it open on screen and blocking
every subsequent slot's select tap. The customer supplied a real
1280x720 Test-capture of the exact stuck screen (the "자유 토벌작전"
mission-detail popup, showing the real target phrase "모든 몬스터
처치 (0/200)").

Every test here uses the real, unmodified capture
(tests/fixtures/game_cal_001/source_extra/bounty_accept_popup_target.png),
the real `OpenCVTemplateRecognizer`, and the real shipped
`configs/bounty.example.yaml` -- never a fake always-match recognizer.
Skipped (not failed) if OpenCV/numpy aren't installed.
"""

from pathlib import Path

import pytest

cv2 = pytest.importorskip("cv2")
np = pytest.importorskip("numpy")

from ldmanager.bounty_config import load_bounty_config
from ldmanager.coordinates import RelativeRegion
from ldmanager.recognition import OpenCVTemplateRecognizer

_FIXTURES = Path(__file__).parent / "fixtures" / "game_cal_001"
_ACCEPT_POPUP = _FIXTURES / "source_extra" / "bounty_accept_popup_target.png"
_FULL_SCREEN = RelativeRegion(x=0.0, y=0.0, width=1.0, height=1.0)


def _load(path: Path) -> bytes:
    assert path.is_file(), f"Real fixture capture missing: {path}"
    return path.read_bytes()


@pytest.fixture(scope="module")
def config():
    return load_bounty_config(Path("configs/bounty.example.yaml"))


@pytest.fixture(scope="module")
def recognizer(config):
    return OpenCVTemplateRecognizer(templates_dir=config.templates_dir, template_map=config.template_map)


def test_real_accept_popup_capture_is_present_and_a_real_1280x720_png():
    data = _load(_ACCEPT_POPUP)
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
    encoded = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    assert image is not None
    height, width = image.shape[:2]
    assert (width, height) == (1280, 720)


def test_production_target_signal_confirms_this_real_popup_is_acceptable(config, recognizer):
    """The shipped config's actual production acceptance signal
    (mission_target_phrase, an OR-matched combined phrase+quantity
    template) must recognize this real popup as the target mission --
    reproducing the exact real state where the old code got stuck."""

    result = recognizer.recognize(_load(_ACCEPT_POPUP), _FULL_SCREEN, "mission_target_phrase", config.threshold)
    assert result.matched is True


def test_stale_accept_mission_button_template_does_not_confidently_match(config):
    """ACCEPT-CONFIRM-001: button_accept_mission.png is a pre-GAME-CAL-
    001 placeholder asset (180x55) that scores below the real
    confidence threshold against the real popup it's meant to match --
    confirming it was never a reliable tap mechanism, independent of
    the accept_mission_point fixed-tap fix."""

    template = cv2.imread(str(Path("templates") / "button_accept_mission.png"))
    assert template is not None
    image = cv2.imdecode(np.frombuffer(_load(_ACCEPT_POPUP), dtype=np.uint8), cv2.IMREAD_COLOR)
    result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    _, confidence, _, _ = cv2.minMaxLoc(result)
    assert confidence < config.threshold


def test_accept_mission_point_lands_inside_the_real_confirm_button(config):
    """accept_mission_point was measured directly from the real popup's
    "확인" button bounding box (x:662-840, y:500-550) -- prove the
    configured tap point actually falls inside it."""

    tap_x = config.accept_mission_point.x * 1280
    tap_y = config.accept_mission_point.y * 720
    assert 662 <= tap_x <= 840
    assert 500 <= tap_y <= 550


def test_example_bounty_config_never_maps_the_stale_accept_mission_template():
    config = load_bounty_config(Path("configs/bounty.example.yaml"))
    assert "button_accept_mission" not in config.template_map
