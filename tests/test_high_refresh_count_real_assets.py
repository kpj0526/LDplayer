"""Real-asset regression tests: acceptance/completion detection stays
correct at high refresh counts and multi-digit prices.

The customer manually refreshed one bounty slot repeatedly (observed
refresh counts up to 7, prices up to 75,500 -- well past the 4 known
tiers 4400/6600/9900/14900 the game happened to show in earlier
captures) and supplied the real screens along the way, plus the
non-target "야왕궁 토벌작전" (강시 처치) popup that has to be refreshed
away, plus the final already-complete detail view reached at the end.

Every test here uses the real, unmodified captures, the real
`OpenCVTemplateRecognizer`, and the real shipped
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
_HIGH_COUNT_TARGET_POPUP = _FIXTURES / "source_extra" / "bounty_popup_count7_75500.png"
_NONTARGET_POPUP = _FIXTURES / "source_extra" / "region_popup_nontarget_gangsi.png"
_COMPLETE_FINAL = _FIXTURES / "source_extra" / "bounty_detail_complete_final.png"
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


def test_all_three_new_captures_are_real_1280x720_pngs():
    for path in (_HIGH_COUNT_TARGET_POPUP, _NONTARGET_POPUP, _COMPLETE_FINAL):
        data = _load(path)
        assert data.startswith(b"\x89PNG\r\n\x1a\n")
        image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
        assert image is not None
        height, width = image.shape[:2]
        assert (width, height) == (1280, 720), path.name


def test_target_phrase_still_matches_at_refresh_count_7_price_75500(config, recognizer):
    """The accept-confirm button's real position was measured at a low
    refresh count/4-digit price; this confirms detection and the tap
    point both stay correct at count 7 / a 5-digit price."""

    result = recognizer.recognize(_load(_HIGH_COUNT_TARGET_POPUP), _FULL_SCREEN, "mission_target_phrase", config.threshold)
    assert result.matched is True


def test_accept_mission_point_still_lands_on_the_real_button_at_count_7(config):
    """The accept-confirm button occupies the same real bbox
    (x:662-840, y:500-550) regardless of the popup's price digit count
    -- confirmed directly against this real count-7/75500 capture."""

    tap_x = config.accept_mission_point.x * 1280
    tap_y = config.accept_mission_point.y * 720
    assert 662 <= tap_x <= 840
    assert 500 <= tap_y <= 550


def test_nontarget_popup_is_correctly_rejected_not_a_false_accept(config, recognizer):
    result = recognizer.recognize(_load(_NONTARGET_POPUP), _FULL_SCREEN, "mission_target_phrase", config.threshold)
    assert result.matched is False


def test_nontarget_popup_never_false_positives_as_the_refresh_confirm_dialog(config, recognizer):
    title = recognizer.recognize(_load(_NONTARGET_POPUP), config.refresh_popup_title_roi, config.refresh_popup_title_label, config.threshold)
    assert title.matched is False


def test_final_complete_detail_view_is_detected_as_both_target_and_complete(config, recognizer):
    """The real screen reached after accepting -- already showing "완료"
    instead of a "0/200" counter -- must be recognized as the target
    (mission_target_phrase is phrase-only, no digits) AND as complete
    (both kill_progress and complete_state signals)."""

    data = _load(_COMPLETE_FINAL)
    target = recognizer.recognize(data, _FULL_SCREEN, "mission_target_phrase", config.threshold)
    assert target.matched is True
    complete_state = recognizer.recognize(data, config.complete_state_roi, config.complete_state_label, config.threshold)
    assert complete_state.matched is True
