"""App wiring tests (MVP-001).

Exercises ``build_controller()``/``main()`` against temp config files
only -- no real ADB, no GUI mainloop, no network. ``ldmanager.app`` must
remain importable without a display (tkinter is imported lazily inside
``main()``, never at module load time).
"""

from pathlib import Path

from ldmanager.app import build_controller, main
from ldmanager.controller import AccountController
from ldmanager.models import AccountId

_MISSION_YAML = """
target_label: "TARGET"
templates_dir: templates
threshold: 0.8
screen_size:
  width: 1000
  height: 1000
slot_rois:
  - {x: 0.0, y: 0.0, width: 0.1, height: 0.1}
  - {x: 0.1, y: 0.0, width: 0.1, height: 0.1}
  - {x: 0.2, y: 0.0, width: 0.1, height: 0.1}
  - {x: 0.3, y: 0.0, width: 0.1, height: 0.1}
  - {x: 0.4, y: 0.0, width: 0.1, height: 0.1}
reroll_point: {x: 0.1, y: 0.9}
kill_check_roi: {x: 0.0, y: 0.0, width: 0.1, height: 0.1}
kill_check_label: "200/200"
claim_point: {x: 0.5, y: 0.5}
claimed_roi: {x: 0.0, y: 0.0, width: 0.1, height: 0.1}
claimed_label: "claimed"
reset_point: {x: 0.9, y: 0.9}
ready_roi: {x: 0.0, y: 0.0, width: 0.1, height: 0.1}
ready_label: "ready"
"""


def _write_configs(tmp_path: Path, adb_mapping_yaml: str) -> tuple[Path, Path]:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(f"adb_mapping:\n{adb_mapping_yaml}\n", encoding="utf-8")
    mission_path = tmp_path / "mission.yaml"
    mission_path.write_text(_MISSION_YAML, encoding="utf-8")
    return config_path, mission_path


def _nine_null_mapping_yaml() -> str:
    return "\n".join(f"  LD{i}: null" for i in range(1, 10))


def test_build_controller_succeeds_with_valid_configs_and_covers_all_accounts(
    tmp_path, monkeypatch
):
    config_path, mission_path = _write_configs(tmp_path, _nine_null_mapping_yaml())
    monkeypatch.setenv("LDMANAGER_CONFIG", str(config_path))
    monkeypatch.setenv("LDMANAGER_MISSION_CONFIG", str(mission_path))

    controller = build_controller()

    assert isinstance(controller, AccountController)
    assert set(controller.account_ids()) == set(AccountId)
    # Nothing was started -- construction alone must not touch ADB/GUI.
    for aid in AccountId:
        assert controller.worker(aid).is_running is False


def test_main_returns_error_code_and_does_not_raise_when_config_missing(
    tmp_path, monkeypatch, capsys
):
    missing_config = tmp_path / "does_not_exist.yaml"
    monkeypatch.setenv("LDMANAGER_CONFIG", str(missing_config))

    exit_code = main()

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Cannot start ldmanager" in captured.err


def test_main_returns_error_code_when_mission_config_missing(tmp_path, monkeypatch):
    config_path, _ = _write_configs(tmp_path, _nine_null_mapping_yaml())
    monkeypatch.setenv("LDMANAGER_CONFIG", str(config_path))
    monkeypatch.setenv("LDMANAGER_MISSION_CONFIG", str(tmp_path / "missing_mission.yaml"))

    assert main() == 1
