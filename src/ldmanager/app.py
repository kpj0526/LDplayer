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
"""

from __future__ import annotations

import sys
import time
from typing import Dict

from .adb import SubprocessAdbRunner
from .bootstrap import bootstrap_default_configs
from .bounty_config import BountyConfigError, load_bounty_config
from .bounty_mission import run_one_cycle
from .config import ConfigError, load_config, resolve_config_path
from .controller import AccountController, AccountWorker
from .logs import get_account_logger
from .models import AccountId
from .recognition import OpenCVTemplateRecognizer
from .runtime import AccountMissionRuntime

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
    # Production always uses a subprocess-backed ADB runner. Start in the
    # GUI therefore sends real, serial-scoped ADB input after recognition.
    runner = SubprocessAdbRunner(adb_path=app_config.adb_path)
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

    # A second SubprocessAdbRunner instance, distinct from the one(s)
    # captured in each worker's cycle closure inside build_controller()
    # -- both are stateless wrappers around the same adb_path/timeout,
    # so this is safe and keeps build_controller()'s own return type
    # (just an AccountController) unchanged. Used only for the GUI's
    # read-only "Refresh ADB devices" button (list_devices()) -- never
    # for a tap, never for starting a worker.
    app = LDManagerApp(
        controller,
        adb_runner=controller.adb_runner,  # type: ignore[attr-defined]
        config_path=resolve_config_path(),
    )
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
