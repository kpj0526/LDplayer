"""GUI construction tests (MVP-001).

Only construction + widget/status wiring is tested here -- no
``mainloop()`` is ever called, and no real ADB/device is involved
(workers use trivial fake cycle functions and are never started).
"""

import pytest

tk = pytest.importorskip("tkinter")

from ldmanager.controller import AccountController, AccountWorker
from ldmanager.gui import LDManagerApp
from ldmanager.models import AccountId


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
def app():
    # Module-scoped: tkinter's Tk() is meant to be used as a per-process
    # singleton-ish root. Constructing/destroying many separate Tk()
    # roots in quick succession within one pytest process is flaky (Tcl/
    # ttk theme re-init races), so this file builds exactly one root and
    # shares it read-mostly across its tests instead.
    application = LDManagerApp(_build_controller(), auto_refresh=False)
    yield application
    application.destroy()


def test_app_constructs_without_starting_mainloop(app):
    assert isinstance(app, tk.Tk)


def test_app_has_a_panel_for_every_account(app):
    assert set(app._panels.keys()) == set(AccountId)
    for account_id, panel in app._panels.items():
        assert panel.cget("text") == account_id.value


def test_panel_start_stop_buttons_call_controller(monkeypatch, app):
    calls = []
    controller = app._controller
    monkeypatch.setattr(controller, "start_account", lambda aid: calls.append(("start", aid)))
    monkeypatch.setattr(controller, "stop_account", lambda aid: calls.append(("stop", aid)))

    panel = app._panels[AccountId.LD1]
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
