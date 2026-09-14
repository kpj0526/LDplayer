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


def test_negative_retry_delay_is_rejected(tmp_path):
    text = EXAMPLE_BOUNTY_CONFIG.read_text(encoding="utf-8")
    bad = text.replace("retry_delay_seconds: 1.0", "retry_delay_seconds: -1.0", 1)
    path = tmp_path / "bounty.yaml"
    path.write_text(bad, encoding="utf-8")
    with pytest.raises(BountyConfigError):
        load_bounty_config(path)
