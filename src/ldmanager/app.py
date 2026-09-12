"""ldmanager MVP application entry point (MVP-001).

Wires together: :class:`~ldmanager.config.AppConfig` (adb_mapping/
logging/diagnostics) + :class:`~ldmanager.mission_config.MissionConfig`
(ROIs/points/thresholds/retries) + a real
:class:`~ldmanager.adb.SubprocessAdbRunner` + the
:class:`~ldmanager.recognition.PlaceholderRecognizer` + one
:class:`~ldmanager.controller.AccountWorker` per account ->
:class:`~ldmanager.controller.AccountController` ->
:class:`~ldmanager.gui.LDManagerApp` (Tkinter GUI).

This is the only module that constructs a *real* SubprocessAdbRunner
and starts the Tk event loop. ``tkinter`` is imported lazily inside
:func:`main` so this module (and :func:`build_controller`) can still be
imported in a headless/test context without requiring a display.
"""

from __future__ import annotations

import sys
import time
from typing import Dict

from .adb import SubprocessAdbRunner
from .config import ConfigError, load_config
from .controller import AccountController, AccountWorker
from .logs import get_account_logger
from .mission import run_one_cycle
from .mission_config import MissionConfigError, load_mission_config
from .models import AccountId
from .recognition import PlaceholderRecognizer

#: Delay between mission cycles for one account's worker, in seconds.
#: Deliberately not zero, so a misconfigured/always-failing account
#: doesn't spin its capture/recognition loop as fast as the CPU allows.
DEFAULT_IDLE_DELAY_SECONDS = 1.0


def _make_cycle_fn(account_id, serial, runner, recognizer, mission_cfg):
    def _cycle(should_stop):
        return run_one_cycle(
            account_id=account_id,
            serial=serial,
            runner=runner,
            recognizer=recognizer,
            config=mission_cfg,
            should_stop=should_stop,
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
    mission_cfg = load_mission_config()
    runner = SubprocessAdbRunner()
    recognizer = PlaceholderRecognizer(templates_dir=mission_cfg.templates_dir)

    workers: Dict[AccountId, AccountWorker] = {}
    for account_id in AccountId:
        serial = app_config.adb_serial_for(account_id) or ""
        logger = get_account_logger(account_id, app_config.logging)
        cycle_fn = _make_cycle_fn(account_id, serial, runner, recognizer, mission_cfg)
        workers[account_id] = AccountWorker(
            account_id,
            cycle_fn,
            logger=logger,
            idle_delay_seconds=DEFAULT_IDLE_DELAY_SECONDS,
            sleep_fn=time.sleep,
        )

    return AccountController(workers)


def main() -> int:
    """Real entry point: build the controller, launch the GUI, block."""

    try:
        controller = build_controller()
    except (ConfigError, MissionConfigError) as exc:
        print(f"Cannot start ldmanager: {exc}", file=sys.stderr)
        return 1

    from .gui import LDManagerApp  # lazy: keeps this module importable headless

    app = LDManagerApp(controller)
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
