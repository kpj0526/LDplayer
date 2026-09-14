"""GUI construction + ADB-mapping-registration tests (MVP-001 / UI-ADB-001).

Only construction + widget/status wiring is tested here -- no
``mainloop()`` is ever called, and no real ADB/device is involved
(workers use trivial fake cycle functions and are never started; ADB
discovery uses ``FakeAdbRunner``, and mapping persistence writes to a
throwaway ``tmp_path``-based config file, never the real repo config).
"""

import pytest

tk = pytest.importorskip("tkinter")

from ldmanager.config_mapping import load_current_adb_mapping
from ldmanager.controller import AccountController, AccountWorker
from ldmanager.discovery import ConnectionStatus
from ldmanager.gui import LDManagerApp
from ldmanager.models import AccountId
from tests.fakes import FakeAdbRunner


class _DummyOutcome:
    outcome = "ok"


def _noop_cycle(should_stop):
    return _DummyOutcome()


def _build_controller() -> AccountController:
    workers = {
        aid: AccountWorker(aid, _noop_cycle, sleep_fn=lambda s: None) for aid in AccountId
    }
    return AccountController(workers)


@pytest.fixture(scope="module")
def config_path(tmp_path_factory):
    base = tmp_path_factory.mktemp("gui_config")
    return base / "config.yaml"


@pytest.fixture(scope="module")
def fake_runner():
    return FakeAdbRunner()


@pytest.fixture(scope="module")
def app(config_path, fake_runner):
    # Module-scoped: tkinter's Tk() is meant to be used as a per-process
    # singleton-ish root. Constructing/destroying many separate Tk()
    # roots in quick succession within one pytest process is flaky (Tcl/
    # ttk theme re-init races), so this file builds exactly one root and
    # shares it read-mostly across its tests instead. Each mapping test
    # below uses a distinct account (LD1..LD9) so tests stay independent
    # despite sharing one app instance.
    application = LDManagerApp(
        _build_controller(), adb_runner=fake_runner, config_path=config_path, auto_refresh=False
    )
    yield application
    application.destroy()


# --- construction ------------------------------------------------------


def test_app_constructs_without_starting_mainloop(app):
    assert isinstance(app, tk.Tk)


def test_app_has_a_panel_for_every_account(app):
    assert set(app._panels.keys()) == set(AccountId)
    for account_id, panel in app._panels.items():
        assert panel.cget("text") == account_id.value


# --- Start is gated on a verified (OK) mapping --------------------------


def test_start_is_blocked_before_mapping_verified_ok(monkeypatch, app):
    calls = []
    monkeypatch.setattr(app._controller, "start_account", lambda aid: calls.append(aid))

    panel = app._panels[AccountId.LD4]
    # ttk disables invoke() entirely on a disabled button -- the
    # strongest guarantee (unclickable), which is what set_mapping_status
    # already applied by default at construction (no OK status yet).
    assert "disabled" in panel.start_button.state()
    panel.start_button.invoke()
    assert calls == []

    # Calling the handler directly (bypassing ttk's own disabled-click
    # guard) still independently refuses to start and surfaces why.
    panel._on_start()
    assert calls == []
    assert "confirm ADB mapping" in panel.mapping_error_var.get()


def test_panel_start_stop_buttons_call_controller_once_verified_ok(monkeypatch, app):
    calls = []
    monkeypatch.setattr(app._controller, "start_account", lambda aid: calls.append(("start", aid)))
    monkeypatch.setattr(app._controller, "stop_account", lambda aid: calls.append(("stop", aid)))

    panel = app._panels[AccountId.LD1]
    panel.set_mapping_status("127.0.0.1:5555", ConnectionStatus.OK, "Device present and authorized.")
    panel.set_capture_ready(True)

    panel.start_button.invoke()
    panel.stop_button.invoke()

    assert calls == [("start", AccountId.LD1), ("stop", AccountId.LD1)]


def test_global_start_all_stop_all_call_controller(monkeypatch, app):
    calls = []
    monkeypatch.setattr(app._controller, "start_all", lambda: calls.append("start_all"))
    monkeypatch.setattr(app._controller, "stop_all", lambda: calls.append("stop_all"))

    app._on_start_all()
    app._on_stop_all()

    assert calls == ["start_all", "stop_all"]


def test_refresh_updates_panel_from_status_snapshot(app):
    status = app._controller.status(AccountId.LD1)
    status.running = True
    status.current_slot = 3
    status.last_error = "boom"
    status.recent_log.append("cycle result: ok")

    panel = app._panels[AccountId.LD1]
    panel.refresh(status)

    assert panel.status_var.get() == "running"
    assert "3" in panel.slot_var.get()
    assert panel.error_var.get() == "boom"
    assert "cycle result: ok" in panel.log_var.get()


def test_capture_readiness_is_account_local(app):
    first = app._panels[AccountId.LD1]
    second = app._panels[AccountId.LD2]
    first.set_mapping_status("127.0.0.1:5555", ConnectionStatus.OK, "ok")
    second.set_mapping_status("127.0.0.1:5557", ConnectionStatus.OK, "ok")
    first.set_capture_ready(True)
    assert "disabled" not in first.start_button.state()
    assert "disabled" in second.start_button.state()


def test_serial_save_clears_capture_readiness(app):
    panel = app._panels[AccountId.LD1]
    panel.set_mapping_status("127.0.0.1:5555", ConnectionStatus.OK, "ok")
    panel.set_capture_ready(True)
    app._on_save_mapping(AccountId.LD1, "127.0.0.1:6000")
    assert panel._capture_ready is False
    assert "disabled" in panel.start_button.state()


# --- Refresh ADB devices: no tap, no worker started ---------------------


def test_refresh_devices_updates_serial_choices_with_no_tap_or_worker(app, fake_runner):
    fake_runner.devices_output = "List of devices attached\n127.0.0.1:6000\tdevice\n"

    app._on_refresh_devices()

    panel = app._panels[AccountId.LD9]
    assert "127.0.0.1:6000" in panel.serial_combo["values"]
    assert fake_runner.calls == []  # no tap (run()) ever issued
    assert app._controller.worker(AccountId.LD9).is_running is False


# --- Save: persists, reloads panel state, gates Start on next refresh ---


def test_save_persists_mapping_and_start_stays_blocked_until_next_refresh(app, fake_runner, config_path):
    panel = app._panels[AccountId.LD7]
    panel.serial_var.set("127.0.0.1:7000")
    panel.save_button.invoke()

    assert panel.mapping_error_var.get() == ""
    assert load_current_adb_mapping(config_path)["LD7"] == "127.0.0.1:7000"
    # Saving alone must not fabricate a live OK -- it's not yet
    # cross-checked against a fresh device list.
    assert panel._connection_status is not ConnectionStatus.OK
    assert "disabled" in panel.start_button.state()

    fake_runner.devices_output = "List of devices attached\n127.0.0.1:7000\tdevice\n"
    app._on_refresh_devices()

    assert panel._connection_status is ConnectionStatus.OK
    # A successful Test capture/template preflight is now also required.
    assert "disabled" in panel.start_button.state()


def test_save_rejects_blank_serial_and_shows_error_on_panel(app):
    panel = app._panels[AccountId.LD8]
    panel.serial_var.set("")

    panel.save_button.invoke()

    assert panel.mapping_error_var.get() != ""


def test_save_rejects_duplicate_and_does_not_overwrite_other_account(app, config_path):
    panel_a = app._panels[AccountId.LD2]
    panel_a.serial_var.set("dup-serial")
    panel_a.save_button.invoke()
    assert panel_a.mapping_error_var.get() == ""

    panel_b = app._panels[AccountId.LD5]
    panel_b.serial_var.set("dup-serial")
    panel_b.save_button.invoke()

    assert panel_b.mapping_error_var.get() != ""
    assert load_current_adb_mapping(config_path)["LD5"] is None
    assert load_current_adb_mapping(config_path)["LD2"] == "dup-serial"


# --- Clear: removes one account's mapping, preserves the rest -----------


def test_clear_removes_mapping_and_preserves_other_accounts(app, config_path):
    panel_ld6 = app._panels[AccountId.LD6]
    panel_ld6.serial_var.set("127.0.0.1:9000")
    panel_ld6.save_button.invoke()
    assert load_current_adb_mapping(config_path)["LD6"] == "127.0.0.1:9000"

    panel_ld6.clear_button.invoke()

    assert load_current_adb_mapping(config_path)["LD6"] is None
    # LD7's mapping (saved by an earlier test) is untouched.
    assert load_current_adb_mapping(config_path)["LD7"] == "127.0.0.1:7000"


# --- Save/Clear never tap and never start a worker -----------------------


def test_save_and_clear_never_tap_or_start_a_worker(app, fake_runner):
    calls_before = list(fake_runner.calls)
    running_before = {aid: app._controller.worker(aid).is_running for aid in AccountId}

    panel = app._panels[AccountId.LD3]
    panel.serial_var.set("127.0.0.1:8000")
    panel.save_button.invoke()
    panel.clear_button.invoke()

    assert fake_runner.calls == calls_before
    assert {aid: app._controller.worker(aid).is_running for aid in AccountId} == running_before


# --- ADB executable path: Browse/Save/Clear (ADB-PATH-001) --------------


def test_browse_adb_path_fills_entry_without_touching_adb(monkeypatch, app, fake_runner):
    calls_before = list(fake_runner.calls)
    monkeypatch.setattr(
        "ldmanager.gui.filedialog.askopenfilename", lambda **kwargs: "C:/picked/adb.exe"
    )

    app._on_browse_adb_path()

    assert app.adb_path_var.get() == "C:/picked/adb.exe"
    assert fake_runner.calls == calls_before  # Browse alone never taps


def test_save_adb_path_rejects_missing_file_and_does_not_persist(app, fake_runner, config_path):
    from ldmanager.config_mapping import load_current_adb_path

    calls_before = list(fake_runner.calls)
    configured_before = app._configured_adb_path

    app.adb_path_var.set("C:/does/not/exist/adb.exe")
    app._on_save_adb_path()

    assert app.adb_path_error_var.get() != ""
    assert app._configured_adb_path == configured_before
    assert load_current_adb_path(config_path) == configured_before
    assert fake_runner.calls == calls_before  # rejected save never taps


def test_save_adb_path_persists_reinitializes_runner_and_refreshes(app, fake_runner, config_path, tmp_path_factory):
    from ldmanager.config_mapping import load_current_adb_path

    real_exe = tmp_path_factory.mktemp("adb_bin") / "adb.exe"
    real_exe.write_bytes(b"")
    calls_before = list(fake_runner.calls)

    app.adb_path_var.set(str(real_exe))
    app._on_save_adb_path()

    assert app.adb_path_error_var.get() == ""
    assert app._configured_adb_path == str(real_exe)
    assert load_current_adb_path(config_path) == str(real_exe)  # persists
    assert fake_runner.adb_path == str(real_exe)  # runner reinitialized, no restart
    assert "found" in app.adb_path_status_var.get()
    assert fake_runner.calls == calls_before  # Save/refresh is still read-only, never a tap


def test_clear_adb_path_resets_to_auto_detect_and_refreshes(app, fake_runner, config_path):
    from ldmanager.config_mapping import load_current_adb_path

    calls_before = list(fake_runner.calls)

    app._on_clear_adb_path()

    assert app.adb_path_error_var.get() == ""
    assert app._configured_adb_path is None
    assert app.adb_path_var.get() == ""
    assert load_current_adb_path(config_path) is None
    assert fake_runner.adb_path is None
    assert fake_runner.calls == calls_before  # Clear is still read-only, never a tap
