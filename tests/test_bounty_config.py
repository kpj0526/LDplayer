from pathlib import Path

import pytest

from ldmanager.bounty_config import (
    BountyConfigError,
    DEFAULT_BOUNTY_CONFIG_RELPATH,
    load_bounty_config,
    resolve_bounty_config_path,
)

EXAMPLE_BOUNTY_CONFIG = Path(__file__).resolve().parents[1] / "configs" / "bounty.example.yaml"


def test_resolve_bounty_config_path_explicit_wins(tmp_path):
    explicit = tmp_path / "explicit.yaml"
    assert resolve_bounty_config_path(explicit) == explicit


def test_resolve_bounty_config_path_env_var(monkeypatch, tmp_path):
    env_path = tmp_path / "from_env.yaml"
    monkeypatch.setenv("LDMANAGER_BOUNTY_CONFIG", str(env_path))
    assert resolve_bounty_config_path() == env_path


def test_resolve_bounty_config_path_default(monkeypatch, tmp_path):
    monkeypatch.delenv("LDMANAGER_BOUNTY_CONFIG", raising=False)
    monkeypatch.chdir(tmp_path)
    assert resolve_bounty_config_path() == tmp_path / DEFAULT_BOUNTY_CONFIG_RELPATH


def test_missing_bounty_config_file_raises_clear_error(tmp_path):
    missing = tmp_path / "does_not_exist.yaml"
    with pytest.raises(BountyConfigError):
        load_bounty_config(missing)


def test_example_bounty_config_loads_successfully():
    config = load_bounty_config(EXAMPLE_BOUNTY_CONFIG)
    assert config.slot_count == 5
    # GAME-CAL-001 (real-capture rework): 1280x720 matches the real
    # customer captures used to calibrate this file's screen-layout/
    # completion/currency anchors -- see tests/fixtures/game_cal_001/.
    assert config.screen_size.width == 1280
    assert config.mission_phrase_label == "모든 몬스터 처치"
    assert config.mission_quantity_label == "200"
    assert config.kill_progress_complete_label == "200/200"
    assert config.max_refresh_attempts >= 1


def test_example_bounty_config_slot_select_points_are_real_calibrated_values():
    """SLOT-SELECT-CALIBRATION-001: guards against silently drifting back
    to the old, never-validated placeholder points (evenly-spaced
    0.20/0.35/0.50/0.65/0.80) that were off by up to 0.11 from the real,
    measured row-band centers -- see configs/bounty.example.yaml's
    comments and tests/fixtures/game_cal_001/PROVENANCE.md."""

    config = load_bounty_config(EXAMPLE_BOUNTY_CONFIG)
    expected_y = (0.3069, 0.4194, 0.5333, 0.6458, 0.7597)
    assert len(config.slot_select_points) == 5
    for point, y in zip(config.slot_select_points, expected_y):
        assert point.x == pytest.approx(0.1172, abs=1e-4)
        assert point.y == pytest.approx(y, abs=1e-4)
    assert config.select_complete_point.x == pytest.approx(0.1172, abs=1e-4)
    assert config.select_complete_point.y == pytest.approx(0.3069, abs=1e-4)


def test_example_bounty_config_never_maps_the_unreliable_slot_templates():
    """SLOT-SELECT-CALIBRATION-001: mission_slot_unselected/
    mission_slot_selected must stay unmapped -- bounty_mission.py no
    longer even attempts a template search for slot selection, but this
    guards against a future edit re-adding a template_map entry that
    would now simply go unused (and could mislead someone recalibrating
    into thinking it's still consulted)."""

    config = load_bounty_config(EXAMPLE_BOUNTY_CONFIG)
    assert "mission_slot_unselected" not in config.template_map
    assert "mission_slot_selected" not in config.template_map


def test_example_bounty_config_refresh_fields_are_real_calibrated_values():
    """REFRESH-CALIBRATION-001/REFRESH-TRIGGER-CORRECTION-001: guards
    against silently drifting back to a never-validated placeholder
    value, or back to REFRESH-CALIBRATION-001's own real-but-wrong-box
    value (0.7227/0.9313, the persistent list-view currency-action box
    -- not interactive once the accept popup is already open) -- see
    configs/bounty.example.yaml's comments and
    tests/fixtures/game_cal_001/PROVENANCE.md."""

    config = load_bounty_config(EXAMPLE_BOUNTY_CONFIG)
    assert config.refresh_button_point.x == pytest.approx(0.4141, abs=1e-4)
    assert config.refresh_button_point.y == pytest.approx(0.7292, abs=1e-4)
    assert config.refresh_confirm_point.x == pytest.approx(0.5867, abs=1e-4)
    assert config.refresh_confirm_point.y == pytest.approx(0.7278, abs=1e-4)
    assert config.refresh_popup_anchor_label == "refresh_popup_renew_label"
    assert config.refresh_popup_title_label == "refresh_popup_title"


def test_example_bounty_config_never_maps_the_stale_refresh_button_templates():
    """REFRESH-CALIBRATION-001: button_refresh_confirm/4400/6600/9900/
    14900 must stay unmapped -- bounty_mission.py no longer even
    attempts a template search for refresh-open/refresh-confirm, but
    this guards against a future edit re-adding a template_map entry
    that would now simply go unused."""

    config = load_bounty_config(EXAMPLE_BOUNTY_CONFIG)
    for label in (
        "button_refresh_confirm", "button_refresh_4400", "button_refresh_6600",
        "button_refresh_9900", "button_refresh_14900",
    ):
        assert label not in config.template_map


def test_example_bounty_config_accept_mission_point_is_a_real_calibrated_value():
    """ACCEPT-CONFIRM-001: guards against silently regressing
    accept_mission_point away from the real, measured value -- see
    configs/bounty.example.yaml's comments and
    tests/fixtures/game_cal_001/PROVENANCE.md."""

    config = load_bounty_config(EXAMPLE_BOUNTY_CONFIG)
    assert config.accept_mission_point.x == pytest.approx(0.5867, abs=1e-4)
    assert config.accept_mission_point.y == pytest.approx(0.7292, abs=1e-4)
    assert "button_accept_mission" not in config.template_map


def test_refresh_popup_fields_are_not_a_cost_field_by_construction():
    # Structural anti-regression: the two popup verification fields must
    # be distinct from any notion of "cost" -- this asserts they exist
    # as their own labeled fields (anchor/title), not a cost value.
    config = load_bounty_config(EXAMPLE_BOUNTY_CONFIG)
    assert config.refresh_popup_anchor_label != config.refresh_popup_title_label
    assert "cost" not in config.refresh_popup_anchor_label.lower()
    assert "cost" not in config.refresh_popup_title_label.lower()


def test_missing_required_key_is_rejected(tmp_path):
    path = tmp_path / "bounty.yaml"
    path.write_text("screen_size: {width: 100, height: 100}\n", encoding="utf-8")
    with pytest.raises(BountyConfigError):
        load_bounty_config(path)


def test_empty_slot_select_points_is_rejected(tmp_path):
    text = EXAMPLE_BOUNTY_CONFIG.read_text(encoding="utf-8")
    lines = text.splitlines()
    out = []
    skipping = False
    for line in lines:
        if line.startswith("slot_select_points:"):
            out.append("slot_select_points: []")
            skipping = True
            continue
        if skipping and line.startswith("  - "):
            continue
        skipping = False
        out.append(line)
    path = tmp_path / "bounty.yaml"
    path.write_text("\n".join(out), encoding="utf-8")
    with pytest.raises(BountyConfigError):
        load_bounty_config(path)


def test_invalid_threshold_is_rejected(tmp_path):
    text = EXAMPLE_BOUNTY_CONFIG.read_text(encoding="utf-8")
    bad = text.replace("threshold: 0.8", "threshold: 2.0", 1)
    path = tmp_path / "bounty.yaml"
    path.write_text(bad, encoding="utf-8")
    with pytest.raises(BountyConfigError):
        load_bounty_config(path)


def test_invalid_screen_size_is_rejected(tmp_path):
    text = EXAMPLE_BOUNTY_CONFIG.read_text(encoding="utf-8")
    bad = text.replace("width: 1280", "width: 0", 1)
    path = tmp_path / "bounty.yaml"
    path.write_text(bad, encoding="utf-8")
    with pytest.raises(BountyConfigError):
        load_bounty_config(path)


def test_non_positive_retry_bound_is_rejected(tmp_path):
    text = EXAMPLE_BOUNTY_CONFIG.read_text(encoding="utf-8")
    bad = text.replace("max_refresh_attempts: 5", "max_refresh_attempts: 0", 1)
    path = tmp_path / "bounty.yaml"
    path.write_text(bad, encoding="utf-8")
    with pytest.raises(BountyConfigError):
        load_bounty_config(path)


def test_example_bounty_config_retry_budget_was_widened():
    """RETRY-BUDGET-001/RETRY-BUDGET-002: a real live run reported
    "refresh popup never verified" recurring intermittently even after
    RETRY-PACING-001 -- the timing margin was thin, not absent. The
    same symptom then recurred on mission_list_verify_failed, proving
    the thin-margin problem applies to every UI-transition-dependent
    verify loop, not just popup-verify. Guards against silently
    drifting back to the original, too-thin budget (3 attempts / 1.0s
    -- 2-3s worst case) on ANY of the five verify loops."""

    config = load_bounty_config(EXAMPLE_BOUNTY_CONFIG)
    assert config.max_popup_verify_attempts >= 5
    assert config.max_complete_verify_attempts >= 5
    assert config.max_reward_verify_attempts >= 5
    assert config.max_result_verify_attempts >= 5
    assert config.max_mission_list_verify_attempts >= 5
    assert config.retry_delay_seconds >= 0.5


def test_negative_retry_delay_is_rejected(tmp_path):
    text = EXAMPLE_BOUNTY_CONFIG.read_text(encoding="utf-8")
    bad = text.replace("retry_delay_seconds: 0.5", "retry_delay_seconds: -1.0", 1)
    assert bad != text, "retry_delay_seconds line not found in example config -- fixture drifted"
    path = tmp_path / "bounty.yaml"
    path.write_text(bad, encoding="utf-8")
    with pytest.raises(BountyConfigError):
        load_bounty_config(path)
