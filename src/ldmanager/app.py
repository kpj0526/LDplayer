"""ldmanager MVP application entry point (MVP-001 / MVP-001-CV).

Wires together: :class:`~ldmanager.config.AppConfig` (adb_mapping/
logging/diagnostics) + :class:`~ldmanager.bounty_config.BountyMissionConfig`
(free regional-bounty ROIs/points/labels/thresholds/retries) + a real
:class:`~ldmanager.adb.SubprocessAdbRunner` + the
:class:`~ldmanager.recognition.PlaceholderRecognizer` + one
:class:`~ldmanager.controller.AccountWorker` per account ->
:class:`~ldmanager.controller.AccountController` ->
:class:`~ldmanager.gui.LDManagerApp` (Tkinter GUI).

As of MVP-001-CV, the real app drives
:func:`ldmanager.bounty_mission.run_one_cycle` (the customer-video,
free regional-bounty five-slot flow) rather than the earlier, simpler
:func:`ldmanager.mission.run_one_cycle`. The earlier generic mission
module/config are kept — unchanged, still fully tested — for backward
compatibility and as a simpler reference implementation of the same
guarded-touch contract; they are just no longer wired into this real
entry point.

This is the only module that constructs a *real* SubprocessAdbRunner
and starts the Tk event loop. ``tkinter`` is imported lazily inside
:func:`main` so this module (and :func:`build_controller`) can still be
imported in a headless/test context without requiring a display.

As of REL-0.1.0-PKG-01, :func:`main` also runs
:func:`ldmanager.bootstrap.bootstrap_default_configs` before anything
else, so a freshly extracted packaged distribution (which ships
``configs/*.example.yaml`` next to the executable but no real config)
opens the GUI on first launch instead of failing with a "config not
found" console error — see ``ldmanager/bootstrap.py`` for exactly what
it does and does not touch (never overwrites an existing config).

As of REL-UPDATE-003, the real ADB runner built here is always wrapped
in :class:`~ldmanager.adb.InputGateAdbRunner`: discovery/capture
(``list_devices``/``capture_binary`` — Refresh ADB devices, Test
capture) always work, but the gate's real ``run()`` (a tap) is refused
unless ``LDMANAGER_LIVE_MODE=1`` is explicitly set in the environment.
This closes a gap found while integrating the imported v1.0.1 tag: the
gate class existed there but was never actually wired in, so a
verified Start (mapping OK + successful Test capture) could already
issue real ADB taps with no separate, explicit opt-in. Nothing about
the Test-capture/readiness-gate feature itself needs live mode — only
an actual mission run (clicking Start) does.
"""

from __future__ import annotations

import os
import sys
import time
from typing import Dict

from .adb import InputGateAdbRunner, SubprocessAdbRunner
from .bootstrap import bootstrap_default_configs
from .bounty_config import BountyConfigError, load_bounty_config
from .bounty_mission import run_one_cycle
from .config import ConfigError, load_config, resolve_config_path
from .controller import AccountController, AccountWorker
from .logs import get_account_logger
from .models import AccountId
from .recognition import OpenCVTemplateRecognizer
from .runtime import AccountMissionRuntime
from .screen_classification import MissionScreenState, classify_screen

#: Real ADB taps are refused by InputGateAdbRunner unless this env var
#: is exactly "1" -- mirrors the existing LDMANAGER_DEVELOPER_MODE
#: pattern (gui.py) for the template-calibration UI. Unset/anything
#: else = safe mode: discovery/capture work, taps do not.
LIVE_MODE_ENV_VAR = "LDMANAGER_LIVE_MODE"

#: Delay between mission cycles for one account's worker, in seconds.
#: Deliberately not zero, so a misconfigured/always-failing account
#: doesn't spin its capture/recognition loop as fast as the CPU allows.
DEFAULT_IDLE_DELAY_SECONDS = 1.0


def _make_cycle_fn(account_id, serial, runner, recognizer, bounty_cfg, runtime):
    def _cycle(should_stop):
        return run_one_cycle(
            account_id=account_id,
            serial=serial,
            runner=runner,
            recognizer=recognizer,
            config=bounty_cfg,
            should_stop=should_stop,
            runtime=runtime,
        )

    return _cycle


def build_controller() -> AccountController:
    """Build a real (non-fake) :class:`AccountController` from config.

    Never guesses a serial: an account with no configured
    ``adb_mapping`` entry gets a worker whose first cycle call
    immediately hits the same "blank serial" guard used everywhere else
    in this project (:func:`ldmanager.adb.validate_serial`). That is
    contained by the worker's own exception handling and surfaced as
    that account's ``last_error`` — it never crashes the app or touches
    ADB for an unmapped account.
    """

    app_config = load_config()
    bounty_cfg = load_bounty_config()
    # Production always uses a subprocess-backed ADB runner, wrapped in
    # InputGateAdbRunner (safe by default -- see module docstring).
    # Discovery/capture always work; a real tap requires LDMANAGER_LIVE_MODE=1.
    runner = InputGateAdbRunner(
        SubprocessAdbRunner(adb_path=app_config.adb_path),
        live_enabled=os.environ.get(LIVE_MODE_ENV_VAR) == "1",
    )
    recognizer = OpenCVTemplateRecognizer(
        templates_dir=bounty_cfg.templates_dir,
        template_map=bounty_cfg.template_map,
    )

    workers: Dict[AccountId, AccountWorker] = {}
    for account_id in AccountId:
        serial = app_config.adb_serial_for(account_id) or ""
        logger = get_account_logger(account_id, app_config.logging)
        runtime = AccountMissionRuntime()
        cycle_fn = _make_cycle_fn(account_id, serial, runner, recognizer, bounty_cfg, runtime)
        workers[account_id] = AccountWorker(
            account_id,
            cycle_fn,
            logger=logger,
            idle_delay_seconds=DEFAULT_IDLE_DELAY_SECONDS,
            sleep_fn=time.sleep,
        )
        workers[account_id].runtime = runtime

    controller = AccountController(workers)
    # Runtime dependency exposed for GUI diagnostics/live-mode control; this
    # remains the real subprocess-backed runner behind InputGateAdbRunner.
    controller.adb_runner = runner  # type: ignore[attr-defined]
    def readiness_check(image_bytes):
        # GAME-CAL-001: previously checked four very specific sub-state-
        # only templates (a refresh-popup title, a reward-result header,
        # a fixed "0/200" quantity crop) -- none of which are present on
        # a plain mission-list/detail screen, and the quantity crop is
        # tied to one specific mission target count. That caused a real
        # customer's valid, correctly-mapped screen to report a template
        # mismatch. classify_screen() instead confirms the screen from
        # stable Mission/Region/list-or-detail layout chrome (if
        # calibrated) and separately, explicitly classifies the mission
        # sub-state -- readiness only requires the *screen* to match, not
        # any specific sub-state.
        result = classify_screen(image_bytes, bounty_cfg, recognizer)
        if result.state is MissionScreenState.MISMATCH:
            return False, f"{result.detail} Send the saved capture for template/anchor calibration."
        return True, f"Screen verified: {result.state.value} ({', '.join(result.matched_labels) or 'no specific sub-state template'})"
    controller.readiness_check = readiness_check  # type: ignore[attr-defined]
    return controller


def main() -> int:
    """Real entry point: bootstrap first-run configs, build the
    controller, launch the GUI, block."""

    for message in bootstrap_default_configs():
        print(message)

    try:
        controller = build_controller()
    except (ConfigError, BountyConfigError) as exc:
        print(f"Cannot start ldmanager: {exc}", file=sys.stderr)
        return 1

    from .gui import LDManagerApp  # lazy: keeps this module importable headless

    # Reuses the exact same InputGateAdbRunner instance build_controller()
    # gave each worker -- so the GUI's Refresh/Test-capture buttons and the
    # mission workers agree on live-mode state. Refresh/Test-capture only
    # ever call list_devices()/capture_binary(), which the gate never
    # blocks; only an actual tap (run()) is refused outside live mode.
    app = LDManagerApp(
        controller,
        adb_runner=controller.adb_runner,  # type: ignore[attr-defined]
        config_path=resolve_config_path(),
        readiness_check=controller.readiness_check,  # type: ignore[attr-defined]
    )
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
