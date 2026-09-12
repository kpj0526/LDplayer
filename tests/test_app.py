"""App wiring tests (MVP-001 / MVP-001-CV).

Exercises ``build_controller()``/``main()`` against temp config files
only -- no real ADB, no GUI mainloop, no network. ``ldmanager.app`` must
remain importable without a display (tkinter is imported lazily inside
``main()``, never at module load time).
"""

from pathlib import Path

from ldmanager.app import build_controller, main
from ldmanager.controller import AccountController
from ldmanager.models import AccountId

_BOUNTY_YAML = """
screen_size: {width: 1000, height: 1000}
templates_dir: templates
threshold: 0.8
slot_select_points:
  - {x: 0.1, y: 0.1}
  - {x: 0.1, y: 0.2}
  - {x: 0.1, y: 0.3}
  - {x: 0.1, y: 0.4}
  - {x: 0.1, y: 0.5}
mission_phrase_roi: {x: 0.0, y: 0.0, width: 0.1, height: 0.1}
mission_phrase_label: "TARGET_PHRASE"
mission_quantity_roi: {x: 0.2, y: 0.0, width: 0.1, height: 0.1}
mission_quantity_label: "200"
refresh_button_point: {x: 0.9, y: 0.9}
refresh_popup_anchor_roi: {x: 0.3, y: 0.0, width: 0.1, height: 0.1}
refresh_popup_anchor_label: "ANCHOR"
refresh_popup_title_roi: {x: 0.4, y: 0.0, width: 0.1, height: 0.1}
refresh_popup_title_label: "TITLE"
refresh_confirm_point: {x: 0.5, y: 0.6}
kill_progress_roi: {x: 0.5, y: 0.0, width: 0.1, height: 0.1}
kill_progress_complete_label: "200/200"
complete_state_roi: {x: 0.6, y: 0.0, width: 0.1, height: 0.1}
complete_state_label: "COMPLETE"
select_complete_point: {x: 0.1, y: 0.2}
complete_button_point: {x: 0.85, y: 0.9}
reward_screen_roi: {x: 0.7, y: 0.0, width: 0.1, height: 0.1}
reward_screen_label: "REWARD"
claim_point: {x: 0.5, y: 0.7}
result_screen_roi: {x: 0.8, y: 0.0, width: 0.1, height: 0.1}
result_screen_label: "RESULT"
close_result_point: {x: 0.9, y: 0.1}
mission_list_roi: {x: 0.05, y: 0.05, width: 0.1, height: 0.1}
mission_list_label: "LIST"
"""


def _write_configs(tmp_path: Path, adb_mapping_yaml: str) -> tuple[Path, Path]:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(f"adb_mapping:\n{adb_mapping_yaml}\n", encoding="utf-8")
    bounty_path = tmp_path / "bounty.yaml"
    bounty_path.write_text(_BOUNTY_YAML, encoding="utf-8")
    return config_path, bounty_path


def _nine_null_mapping_yaml() -> str:
    return "\n".join(f"  LD{i}: null" for i in range(1, 10))


def test_build_controller_succeeds_with_valid_configs_and_covers_all_accounts(
    tmp_path, monkeypatch
):
    config_path, bounty_path = _write_configs(tmp_path, _nine_null_mapping_yaml())
    monkeypatch.setenv("LDMANAGER_CONFIG", str(config_path))
    monkeypatch.setenv("LDMANAGER_BOUNTY_CONFIG", str(bounty_path))

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


def test_main_returns_error_code_when_bounty_config_missing(tmp_path, monkeypatch):
    config_path, _ = _write_configs(tmp_path, _nine_null_mapping_yaml())
    monkeypatch.setenv("LDMANAGER_CONFIG", str(config_path))
    monkeypatch.setenv("LDMANAGER_BOUNTY_CONFIG", str(tmp_path / "missing_bounty.yaml"))

    assert main() == 1
