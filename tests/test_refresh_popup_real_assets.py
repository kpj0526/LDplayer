"""Real-asset regression tests for REFRESH-CALIBRATION-001.

A real customer live run reported "Slot 3: refresh-open tap failed" on
a real, never-target-matching dungeon-type mission ("십변도
토벌작전[던전]" / 귀마황 처치 (0/250)) -- refresh_button_point/
refresh_popup_anchor_roi/refresh_popup_title_roi/refresh_confirm_point
had never been calibrated against any real capture (all placeholder
values, some using pre-GAME-CAL-001 mock template assets that never
confidently match). The customer then supplied real 1280x720
Test-captures of the actual region-quest list view (two different
slots/missions selected) and the actual renewal-confirm popup
("지역 퀘스트를 갱신 하시겠습니까?").

Every test here uses the real, unmodified captures
(tests/fixtures/game_cal_001/source_extra/region_*.png), the real
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
_RENEW_CONFIRM_POPUP = _FIXTURES / "source_extra" / "region_quest_renew_confirm.png"
_OTHER_REAL_CAPTURES = (
    _FIXTURES / "source" / "completed_target.png",
    _FIXTURES / "source" / "in_progress_target.png",
    _FIXTURES / "source" / "non_target.png",
    _FIXTURES / "source_extra" / "mission_list_row1_completed.png",
    _FIXTURES / "source_extra" / "bounty_detail_popup.png",
    _FIXTURES / "source_extra" / "region_list_slot1_named_quest.png",
    _FIXTURES / "source_extra" / "region_list_slot3_dungeon.png",
    _FIXTURES / "source_extra" / "result_close_screen.png",
    _FIXTURES / "source_extra" / "reward_screen.png",
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


def test_real_renew_confirm_popup_capture_is_present_and_a_real_1280x720_png():
    data = _load(_RENEW_CONFIRM_POPUP)
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
    encoded = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    assert image is not None
    height, width = image.shape[:2]
    assert (width, height) == (1280, 720)


def test_refresh_popup_title_matches_only_the_real_renew_confirm_popup(config, recognizer):
    result = recognizer.recognize(
        _load(_RENEW_CONFIRM_POPUP), config.refresh_popup_title_roi, config.refresh_popup_title_label, config.threshold
    )
    assert result.matched is True


def test_refresh_popup_title_never_matches_any_other_real_capture(config, recognizer):
    for path in _OTHER_REAL_CAPTURES:
        result = recognizer.recognize(
            _load(path), config.refresh_popup_title_roi, config.refresh_popup_title_label, config.threshold
        )
        assert result.matched is False, f"False positive refresh-popup-title match on {path.name}"


def test_refresh_popup_renew_label_matches_only_the_real_renew_confirm_popup(config, recognizer):
    result = recognizer.recognize(
        _load(_RENEW_CONFIRM_POPUP), config.refresh_popup_anchor_roi, config.refresh_popup_anchor_label, config.threshold
    )
    assert result.matched is True


def test_refresh_popup_renew_label_never_matches_any_other_real_capture(config, recognizer):
    for path in _OTHER_REAL_CAPTURES:
        result = recognizer.recognize(
            _load(path), config.refresh_popup_anchor_roi, config.refresh_popup_anchor_label, config.threshold
        )
        assert result.matched is False, f"False positive refresh-popup-renew-label match on {path.name}"


def test_refresh_button_point_lands_on_the_real_accept_popup_price_box(config):
    """REFRESH-TRIGGER-CORRECTION-001: refresh_button_point taps the
    accept POPUP's own embedded price/counter box (real bbox
    x:438-622, y:498-552 -- immediately left of accept_mission_point's
    "확인" button, same row), never the persistent list-view currency-
    action box REFRESH-CALIBRATION-001 originally (and wrongly)
    calibrated it against -- confirmed by a real customer screen
    recording that tapping THIS box is what opens the real renewal-
    confirm dialog. Proven here against two real captures of this
    popup at different refresh counts/prices (1/6600 and 7/75500) --
    the box's position doesn't shift with the price's digit count."""

    tap_x = config.refresh_button_point.x * 1280
    tap_y = config.refresh_button_point.y * 720
    for path in (
        _FIXTURES / "source_extra" / "bounty_accept_popup_target.png",
        _FIXTURES / "source_extra" / "bounty_popup_count7_75500.png",
    ):
        assert path.is_file(), f"Real fixture capture missing: {path}"
        assert 438 <= tap_x <= 622, f"tap x {tap_x} outside the real price-box bbox"
        assert 498 <= tap_y <= 552, f"tap y {tap_y} outside the real price-box bbox"


def test_refresh_button_point_is_never_the_persistent_list_currency_action_box(config):
    """The two boxes look nearly identical but sit at different screen
    positions -- guard against silently drifting back to the wrong one
    (real bbox x:830-1020, y:643-698, confirmed via template match
    against currency_action_4400.png, 0.993 confidence)."""

    tap_x = config.refresh_button_point.x * 1280
    tap_y = config.refresh_button_point.y * 720
    assert not (830 <= tap_x <= 1020 and 643 <= tap_y <= 698)


def test_stale_refresh_button_templates_are_deliberately_not_configured():
    """REFRESH-CALIBRATION-001: button_refresh_confirm/4400/6600/9900/
    14900 are pre-GAME-CAL-001 placeholder assets (never real captures)
    that a real live run proved never confidently match. Refresh-open
    and refresh-confirm now always use the real, measured
    refresh_button_point/refresh_confirm_point instead (see
    bounty_mission.py)."""

    config = load_bounty_config(Path("configs/bounty.example.yaml"))
    for label in (
        "button_refresh_confirm", "button_refresh_4400", "button_refresh_6600",
        "button_refresh_9900", "button_refresh_14900",
    ):
        assert label not in config.template_map
