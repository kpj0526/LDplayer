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

As of LIVE-SERIAL-001, each worker's serial is resolved **live**, via
:class:`LiveSerialRegistry`, instead of once at :func:`build_controller`
time. A real customer reproduction: the GUI showed LD1 mapped to
``emulator-5554`` and Start succeeded, yet the worker crashed with
``ValueError: Invalid ADB serial: ''``. Root cause: :func:`_make_cycle_fn`
previously closed over a plain ``serial`` string captured **once**, when
``build_controller()`` first ran (typically before any mapping existed,
since bootstrap creates a null mapping) — a later GUI Save
(:mod:`ldmanager.config_mapping`) correctly persists the new serial to
``configs/config.yaml``, but that config file is never re-read by an
already-running worker, so its cycle kept using the original, blank
value. :class:`LiveSerialRegistry` is the single shared, per-account,
thread-safe source of truth both the GUI (after a successful Save/Clear)
and every cycle (on every single call, never cached) read from — no
serial is ever captured once and reused stale. A blank/absent serial
now fails **before** any capture/ADB/touch call, as a contained,
structured :class:`~ldmanager.bounty_mission.BountyCycleResult`
(``CAPTURE_UNAVAILABLE``) — never an uncaught ``ValueError`` bubbling up
through capture/recognize/tap helpers.
"""

from __future__ import annotations

import os
import sys
import threading
import time
from typing import Dict, Optional

from .adb import InputGateAdbRunner, SubprocessAdbRunner
from .bootstrap import bootstrap_default_configs
from .bounty_config import BountyConfigError, load_bounty_config
from .bounty_mission import BountyCycleResult, BountyOutcome, run_one_cycle
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


class LiveSerialRegistry:
    """Thread-safe, per-account, LIVE ADB serial store (LIVE-SERIAL-001).

    The single shared source of truth for "what serial should THIS
    account's next mission cycle use" -- read fresh by
    :func:`_make_cycle_fn`'s closure on every single call, never cached.
    :meth:`set` is called by the GUI immediately after a successful
    mapping Save/Clear (mirroring the existing
    ``InputGateAdbRunner.set_adb_path`` live-update pattern from
    ADB-PATH-001), so a worker started before a Save picks up the new
    value on its very next cycle -- no restart needed, and no window
    where a stale value could still be used, since :meth:`get` always
    reads the current value at call time.

    Strictly keyed by :class:`~ldmanager.models.AccountId`: one
    account's :meth:`set` can never be observed by another account's
    :meth:`get` -- there is no shared/default/"current" slot. A never-
    set or cleared account reads back as ``""`` (never ``None``, never
    guessed, never another account's value).
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._serials: Dict[AccountId, str] = {}

    def set(self, account_id: AccountId, serial: Optional[str]) -> None:
        with self._lock:
            self._serials[account_id] = (serial or "").strip()

    def get(self, account_id: AccountId) -> str:
        with self._lock:
            return self._serials.get(account_id, "")


def _make_cycle_fn(account_id, serial_registry: LiveSerialRegistry, runner, recognizer, bounty_cfg, runtime):
    def _cycle(should_stop):
        # LIVE-SERIAL-001: resolved fresh on EVERY call -- never a value
        # captured once at build_controller() time. A blank/absent
        # serial fails right here, account-locally, as a contained,
        # structured result -- before capture_screenshot/_recognize/
        # _tap_template/runner.run are ever reached, never as an
        # uncaught ValueError from deep inside validate_serial().
        serial = serial_registry.get(account_id)
        if not serial:
            return BountyCycleResult(
                BountyOutcome.CAPTURE_UNAVAILABLE, (),
                f"{account_id.value}: no ADB serial configured (or not yet saved) -- "
                "no capture/ADB/touch attempted.",
            )
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
    ``adb_mapping`` entry (at build time, or still unmapped later) gets
    a cycle that refuses to capture/ADB/touch at all, contained as a
    structured ``CAPTURE_UNAVAILABLE`` result -- never an uncaught
    exception, never a guessed/default/another-account's serial. Each
    worker's serial is resolved **live** via the returned controller's
    ``serial_registry`` (:class:`LiveSerialRegistry`) on every cycle,
    not just once here at construction time -- see LIVE-SERIAL-001 in
    the module docstring for exactly why that distinction matters.
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

    serial_registry = LiveSerialRegistry()
    workers: Dict[AccountId, AccountWorker] = {}
    for account_id in AccountId:
        # Seeds the registry from whatever's on disk right now -- the
        # GUI's Save/Clear handler (gui.py) keeps this current from
        # here on, for the lifetime of this controller.
        serial_registry.set(account_id, app_config.adb_serial_for(account_id))
        logger = get_account_logger(account_id, app_config.logging)
        runtime = AccountMissionRuntime()
        cycle_fn = _make_cycle_fn(account_id, serial_registry, runner, recognizer, bounty_cfg, runtime)
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
    # LIVE-SERIAL-001: the GUI calls serial_registry.set(...) right after
    # every successful mapping Save/Clear so an already-running (or not
    # yet started) worker's very next cycle sees the new value.
    controller.serial_registry = serial_registry  # type: ignore[attr-defined]
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
        serial_registry=controller.serial_registry,  # type: ignore[attr-defined]
    )
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
