from pathlib import Path

import pytest

from ldmanager.mission_config import (
    DEFAULT_MISSION_CONFIG_RELPATH,
    MissionConfigError,
    load_mission_config,
    resolve_mission_config_path,
)

EXAMPLE_MISSION_CONFIG = (
    Path(__file__).resolve().parents[1] / "configs" / "mission.example.yaml"
)


def test_resolve_mission_config_path_explicit_wins(tmp_path):
    explicit = tmp_path / "explicit.yaml"
    assert resolve_mission_config_path(explicit) == explicit


def test_resolve_mission_config_path_env_var(monkeypatch, tmp_path):
    env_path = tmp_path / "from_env.yaml"
    monkeypatch.setenv("LDMANAGER_MISSION_CONFIG", str(env_path))
    assert resolve_mission_config_path() == env_path


def test_resolve_mission_config_path_default(monkeypatch, tmp_path):
    monkeypatch.delenv("LDMANAGER_MISSION_CONFIG", raising=False)
    monkeypatch.chdir(tmp_path)
    assert resolve_mission_config_path() == tmp_path / DEFAULT_MISSION_CONFIG_RELPATH


def test_missing_mission_config_file_raises_clear_error(tmp_path):
    missing = tmp_path / "does_not_exist.yaml"
    with pytest.raises(MissionConfigError):
        load_mission_config(missing)


def test_example_mission_config_loads_successfully():
    config = load_mission_config(EXAMPLE_MISSION_CONFIG)
    assert config.slot_count == 5
    assert config.screen_size.width == 960
    assert config.screen_size.height == 540
    assert 0.0 <= config.threshold <= 1.0
    assert config.templates_dir == Path("templates")
    assert config.max_reroll_attempts >= 1


_MINIMAL_VALID_YAML = """
target_label: "X"
templates_dir: templates
threshold: 0.8
screen_size: {width: 960, height: 540}
slot_rois:
  - {x: 0.0, y: 0.0, width: 0.1, height: 0.1}
reroll_point: {x: 0.5, y: 0.9}
kill_check_roi: {x: 0.0, y: 0.0, width: 0.1, height: 0.1}
claim_point: {x: 0.5, y: 0.7}
claimed_roi: {x: 0.0, y: 0.0, width: 0.1, height: 0.1}
reset_point: {x: 0.5, y: 0.95}
ready_roi: {x: 0.0, y: 0.0, width: 0.1, height: 0.1}
"""


def test_empty_slot_rois_list_is_rejected(tmp_path):
    bad = _MINIMAL_VALID_YAML.replace(
        "slot_rois:\n  - {x: 0.0, y: 0.0, width: 0.1, height: 0.1}\n",
        "slot_rois: []\n",
    )
    path = tmp_path / "mission.yaml"
    path.write_text(bad, encoding="utf-8")
    with pytest.raises(MissionConfigError):
        load_mission_config(path)


def test_single_slot_roi_is_accepted_slot_count_reflects_it(tmp_path):
    path = tmp_path / "mission.yaml"
    path.write_text(_MINIMAL_VALID_YAML, encoding="utf-8")
    config = load_mission_config(path)
    assert config.slot_count == 1


def test_missing_required_key_is_rejected(tmp_path):
    path = tmp_path / "mission.yaml"
    path.write_text("target_label: 'X'\n", encoding="utf-8")
    with pytest.raises(MissionConfigError):
        load_mission_config(path)


def test_invalid_roi_bounds_is_rejected(tmp_path):
    text = EXAMPLE_MISSION_CONFIG.read_text(encoding="utf-8")
    # Push a slot ROI past the right edge of the screen.
    bad = text.replace(
        "- {x: 0.05, y: 0.10, width: 0.15, height: 0.08}",
        "- {x: 0.95, y: 0.10, width: 0.50, height: 0.08}",
        1,
    )
    path = tmp_path / "mission.yaml"
    path.write_text(bad, encoding="utf-8")
    with pytest.raises(MissionConfigError):
        load_mission_config(path)


def test_invalid_threshold_is_rejected(tmp_path):
    text = EXAMPLE_MISSION_CONFIG.read_text(encoding="utf-8")
    bad = text.replace("threshold: 0.8", "threshold: 1.5", 1)
    path = tmp_path / "mission.yaml"
    path.write_text(bad, encoding="utf-8")
    with pytest.raises(MissionConfigError):
        load_mission_config(path)


def test_invalid_screen_size_is_rejected(tmp_path):
    text = EXAMPLE_MISSION_CONFIG.read_text(encoding="utf-8")
    bad = text.replace("width: 960", "width: -1", 1)
    path = tmp_path / "mission.yaml"
    path.write_text(bad, encoding="utf-8")
    with pytest.raises(MissionConfigError):
        load_mission_config(path)


def test_negative_retry_delay_is_rejected(tmp_path):
    text = EXAMPLE_MISSION_CONFIG.read_text(encoding="utf-8")
    bad = text.replace("retry_delay_seconds: 1.0", "retry_delay_seconds: -1.0", 1)
    path = tmp_path / "mission.yaml"
    path.write_text(bad, encoding="utf-8")
    with pytest.raises(MissionConfigError):
        load_mission_config(path)


def test_non_positive_retry_bound_is_rejected(tmp_path):
    text = EXAMPLE_MISSION_CONFIG.read_text(encoding="utf-8")
    bad = text.replace("max_reroll_attempts: 5", "max_reroll_attempts: 0", 1)
    path = tmp_path / "mission.yaml"
    path.write_text(bad, encoding="utf-8")
    with pytest.raises(MissionConfigError):
        load_mission_config(path)
