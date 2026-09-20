"""Real-asset regression tests for REFRESH-RESULT-DISMISS-001.

A real customer live run stalled repeatedly with "Slot 3: refresh
popup never verified" -- even after REFRESH-TRIGGER-CORRECTION-001
and RETRY-BUDGET-001/002 shipped. The customer then supplied real
screenshots of the actual stuck screen: a brief acknowledgment popup
(title + "확률" odds + a single reward icon + "닫기") shown right
after confirming a mission renewal, for the newly-rolled mission --
which the refresh loop never knew to dismiss.

Every test here uses the real, unmodified captures
(tests/fixtures/game_cal_001/source_extra/refresh_result_popup_*.png),
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
_ACK_POPUP_1 = _FIXTURES / "source_extra" / "refresh_result_popup_1.png"
_ACK_POPUP_2 = _FIXTURES / "source_extra" / "refresh_result_popup_2.png"


def _load(path: Path) -> bytes:
    assert path.is_file(), f"Real fixture capture missing: {path}"
    return path.read_bytes()


@pytest.fixture(scope="module")
def config():
    return load_bounty_config(Path("configs/bounty.example.yaml"))


@pytest.fixture(scope="module")
def recognizer(config):
    return OpenCVTemplateRecognizer(templates_dir=config.templates_dir, template_map=config.template_map)


def test_both_real_ack_popup_captures_are_genuine_1280x720_pngs():
    for path in (_ACK_POPUP_1, _ACK_POPUP_2):
        data = _load(path)
        assert data.startswith(b"\x89PNG\r\n\x1a\n")
        image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
        assert image is not None
        height, width = image.shape[:2]
        assert (width, height) == (1280, 720), path.name


def test_reward_screen_label_matches_the_real_ack_popup(config, recognizer):
    """The already-calibrated reward_screen_label ("확률") anchor,
    reused here to detect this structurally-identical acknowledgment
    popup, must match both real captures with high confidence."""

    for path in (_ACK_POPUP_1, _ACK_POPUP_2):
        result = recognizer.recognize(_load(path), config.reward_screen_roi, config.reward_screen_label, config.threshold)
        assert result.matched is True, f"reward_screen_label failed to match {path.name}"


def test_close_result_point_lands_on_the_real_dismiss_button(config):
    """close_result_point's real, measured bbox for this popup's "닫기"
    button is x:552-732, y:486-537 -- confirmed to coincide with the
    already-calibrated close_result_point/claim_point value (no new
    position needed)."""

    tap_x = config.close_result_point.x * 1280
    tap_y = config.close_result_point.y * 720
    assert 552 <= tap_x <= 732
    assert 486 <= tap_y <= 537
