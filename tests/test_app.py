"""App wiring tests (MVP-001 / MVP-001-CV / REL-0.1.0-PKG-01).

Exercises ``build_controller()``/``main()`` against temp config files
only -- no real ADB, no GUI mainloop, no network. ``ldmanager.app`` must
remain importable without a display (tkinter is imported lazily inside
``main()``, never at module load time).

Every test here changes into ``tmp_path`` (``monkeypatch.chdir``) before
touching config resolution: ``main()`` now runs first-run bootstrap
(``ldmanager.bootstrap``), which -- when unfrozen -- looks for bundled
``*.example.yaml`` files relative to the current working directory. Not
isolating CWD would let a test's bootstrap find and copy this
project's own real ``configs/*.example.yaml`` into the *real repo*
`configs/` directory (a genuine side effect observed once during
development of this test file -- see docs/HANDOFF_CODE.md's
REL-0.1.0-PKG-01 section).
"""

from pathlib import Path

from ldmanager.app import _make_cycle_fn, build_controller, main
from ldmanager.bootstrap import bootstrap_default_configs
from ldmanager.controller import AccountController
from ldmanager.models import AccountId

REPO_ROOT = Path(__file__).resolve().parents[1]

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
    monkeypatch.chdir(tmp_path)
    config_path, bounty_path = _write_configs(tmp_path, _nine_null_mapping_yaml())
    monkeypatch.setenv("LDMANAGER_CONFIG", str(config_path))
    monkeypatch.setenv("LDMANAGER_BOUNTY_CONFIG", str(bounty_path))

    controller = build_controller()

    assert isinstance(controller, AccountController)
    assert set(controller.account_ids()) == set(AccountId)
    # Nothing was started -- construction alone must not touch ADB/GUI.
    for aid in AccountId:
        assert controller.worker(aid).is_running is False


# --- REL-UPDATE-003: InputGateAdbRunner wiring (real taps opt-in only) -----


def test_build_controller_wires_input_gate_blocking_taps_by_default(tmp_path, monkeypatch):
    """build_controller() previously wired the raw SubprocessAdbRunner
    directly (a gap found while integrating the v1.0.1 candidate: its
    InputGateAdbRunner class existed but was never actually used). Fixed
    as part of REL-UPDATE-003 -- verify the real runner is always the
    gate, and defaults closed (no LDMANAGER_LIVE_MODE set)."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LDMANAGER_LIVE_MODE", raising=False)
    config_path, bounty_path = _write_configs(tmp_path, _nine_null_mapping_yaml())
    monkeypatch.setenv("LDMANAGER_CONFIG", str(config_path))
    monkeypatch.setenv("LDMANAGER_BOUNTY_CONFIG", str(bounty_path))

    controller = build_controller()

    from ldmanager.adb import InputGateAdbRunner

    assert isinstance(controller.adb_runner, InputGateAdbRunner)
    assert controller.adb_runner.live_enabled is False


def test_build_controller_honors_live_mode_env_var(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LDMANAGER_LIVE_MODE", "1")
    config_path, bounty_path = _write_configs(tmp_path, _nine_null_mapping_yaml())
    monkeypatch.setenv("LDMANAGER_CONFIG", str(config_path))
    monkeypatch.setenv("LDMANAGER_BOUNTY_CONFIG", str(bounty_path))

    controller = build_controller()

    assert controller.adb_runner.live_enabled is True


def test_build_controller_live_mode_env_var_requires_exact_value(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LDMANAGER_LIVE_MODE", "true")  # not the exact "1"
    config_path, bounty_path = _write_configs(tmp_path, _nine_null_mapping_yaml())
    monkeypatch.setenv("LDMANAGER_CONFIG", str(config_path))
    monkeypatch.setenv("LDMANAGER_BOUNTY_CONFIG", str(bounty_path))

    controller = build_controller()

    assert controller.adb_runner.live_enabled is False


def test_cycle_uses_latest_saved_serial_not_the_startup_blank_value(monkeypatch):
    """Regression for the customer LD1 crash: workers used to close over
    the blank serial present at application startup, so clicking Save in
    the GUI did not affect a later Start.  The cycle must resolve its
    serial at execution time from the shared, per-account mapping."""
    captured = {}

    def fake_cycle(**kwargs):
        captured["serial"] = kwargs["serial"]
        return object()

    monkeypatch.setattr("ldmanager.app.run_one_cycle", fake_cycle)
    mapping = {AccountId.LD1: ""}
    cycle = _make_cycle_fn(
        AccountId.LD1,
        lambda account_id: mapping[account_id],
        runner=object(), recognizer=object(), bounty_cfg=object(), runtime=object(),
    )

    # This is exactly what GUI Save does before the user presses Start.
    mapping[AccountId.LD1] = "emulator-5554"
    cycle(lambda: False)

    assert captured["serial"] == "emulator-5554"


def test_main_returns_error_code_and_does_not_raise_when_config_missing(
    tmp_path, monkeypatch, capsys
):
    # Isolated, empty tmp_path CWD: no *.example.yaml anywhere nearby,
    # so bootstrap correctly finds nothing to create and the original
    # "config not found" error path still fires.
    monkeypatch.chdir(tmp_path)
    missing_config = tmp_path / "does_not_exist.yaml"
    monkeypatch.setenv("LDMANAGER_CONFIG", str(missing_config))

    exit_code = main()

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Cannot start ldmanager" in captured.err


def test_main_returns_error_code_when_bounty_config_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path, _ = _write_configs(tmp_path, _nine_null_mapping_yaml())
    monkeypatch.setenv("LDMANAGER_CONFIG", str(config_path))
    monkeypatch.setenv("LDMANAGER_BOUNTY_CONFIG", str(tmp_path / "missing_bounty.yaml"))

    assert main() == 1


# --- first-run bootstrap integration (REL-0.1.0-PKG-01) -------------------


def test_first_run_bootstrap_then_build_controller_succeeds(tmp_path, monkeypatch):
    """Simulates exactly what a freshly extracted ZIP + first launch
    does: only configs/*.example.yaml present (as
    scripts/build_windows.ps1 packages them), no real config yet."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LDMANAGER_CONFIG", raising=False)
    monkeypatch.delenv("LDMANAGER_BOUNTY_CONFIG", raising=False)

    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    (configs_dir / "config.example.yaml").write_bytes(
        (REPO_ROOT / "configs" / "config.example.yaml").read_bytes()
    )
    (configs_dir / "bounty.example.yaml").write_bytes(
        (REPO_ROOT / "configs" / "bounty.example.yaml").read_bytes()
    )

    messages = bootstrap_default_configs()
    assert len(messages) == 2  # both config.yaml and bounty.yaml created

    controller = build_controller()

    assert isinstance(controller, AccountController)
    for aid in AccountId:
        assert controller.worker(aid).is_running is False


def test_bootstrap_does_not_disturb_an_already_registered_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LDMANAGER_CONFIG", raising=False)
    monkeypatch.delenv("LDMANAGER_BOUNTY_CONFIG", raising=False)

    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    (configs_dir / "config.example.yaml").write_bytes(
        (REPO_ROOT / "configs" / "config.example.yaml").read_bytes()
    )
    (configs_dir / "bounty.example.yaml").write_bytes(
        (REPO_ROOT / "configs" / "bounty.example.yaml").read_bytes()
    )
    # The user already registered LD1 by hand (or via the GUI) before.
    existing_config = "adb_mapping:\n  LD1: my-already-registered-serial\n"
    (configs_dir / "config.yaml").write_text(existing_config, encoding="utf-8")

    bootstrap_default_configs()

    assert (configs_dir / "config.yaml").read_text(encoding="utf-8") == existing_config
