"""LIVE-SERIAL-001 regression tests: live per-account serial propagation.

Real customer reproduction: the GUI displayed LD1 mapped to
``emulator-5554`` and Start succeeded, yet the worker crashed with
``ValueError: Invalid ADB serial: ''``. Root cause: ``app.py``'s
``_make_cycle_fn`` closed over a plain ``serial`` string captured ONCE,
at ``build_controller()`` time (typically before any real mapping
existed) -- a later GUI Save correctly persisted the new serial to
``configs/config.yaml``, but the already-built cycle function never
re-read it, so it kept using the stale blank value.

This file exercises the fix (``ldmanager.app.LiveSerialRegistry`` +
``_make_cycle_fn`` reading it fresh on every call) at three levels:
the registry itself, the cycle function in isolation (no thread), and
the full ``AccountWorker`` thread -- reproducing the exact customer
timeline (build with a blank mapping, THEN a GUI-equivalent Save,
THEN Start) end to end. No real ADB, no GUI, no real device anywhere.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

from ldmanager.adb import AdbBinaryResult
from ldmanager.app import LiveSerialRegistry, _make_cycle_fn
from ldmanager.bounty_config import BountyMissionConfig
from ldmanager.bounty_mission import BountyOutcome
from ldmanager.controller import AccountController, AccountWorker
from ldmanager.coordinates import RelativeCoordinate, RelativeRegion, ScreenSize
from ldmanager.models import AccountId
from ldmanager.screenshot import DEFAULT_CAPTURE_ARGS
from tests.fakes import FakeAdbRunner, LabelMappingRecognizer

_VALID_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
_CUSTOMER_SERIAL = "emulator-5554"

_PHRASE = "PHRASE"
_QTY = "QTY"
_POPUP_ANCHOR = "POPUP_ANCHOR"
_POPUP_TITLE = "POPUP_TITLE"
_KILL_PROGRESS = "200/200"
_REWARD = "REWARD"
_RESULT = "RESULT"
_MISSION_LIST = "MISSION_LIST"

_ALL_LABELS = frozenset({_PHRASE, _QTY, _POPUP_ANCHOR, _POPUP_TITLE, _KILL_PROGRESS, _REWARD, _RESULT, _MISSION_LIST})


def _roi(x=0.0, y=0.0, w=0.1, h=0.1):
    return RelativeRegion(x=x, y=y, width=w, height=h)


def _bounty_config() -> BountyMissionConfig:
    return BountyMissionConfig(
        slot_select_points=tuple(RelativeCoordinate(x=0.1, y=0.1 * i) for i in range(1, 6)),
        mission_phrase_roi=_roi(), mission_phrase_label=_PHRASE,
        mission_quantity_roi=_roi(0.2), mission_quantity_label=_QTY,
        refresh_button_point=RelativeCoordinate(x=0.9, y=0.9),
        refresh_popup_anchor_roi=_roi(0.3), refresh_popup_anchor_label=_POPUP_ANCHOR,
        refresh_popup_title_roi=_roi(0.4), refresh_popup_title_label=_POPUP_TITLE,
        refresh_confirm_point=RelativeCoordinate(x=0.5, y=0.6),
        kill_progress_roi=_roi(0.5), kill_progress_complete_label=_KILL_PROGRESS,
        complete_state_roi=_roi(0.6), complete_state_label="COMPLETE_BADGE",
        select_complete_point=RelativeCoordinate(x=0.1, y=0.2),
        complete_button_point=RelativeCoordinate(x=0.85, y=0.9),
        reward_screen_roi=_roi(0.7), reward_screen_label=_REWARD,
        claim_point=RelativeCoordinate(x=0.5, y=0.7),
        result_screen_roi=_roi(0.8), result_screen_label=_RESULT,
        close_result_point=RelativeCoordinate(x=0.9, y=0.1),
        mission_list_roi=_roi(0.05, 0.05), mission_list_label=_MISSION_LIST,
        screen_size=ScreenSize(width=1000, height=1000),
        templates_dir=Path("templates"),
        threshold=0.8,
        max_kill_progress_poll_attempts=2,
    )


def _runner_with_valid_capture(serial: str) -> FakeAdbRunner:
    return FakeAdbRunner(
        capture_results={
            (serial, DEFAULT_CAPTURE_ARGS): AdbBinaryResult(
                serial=serial, args=DEFAULT_CAPTURE_ARGS, returncode=0, stdout_bytes=_VALID_PNG, stderr="",
            )
        }
    )


# --- LiveSerialRegistry: isolated unit behavior -----------------------------


def test_registry_get_defaults_to_blank_string_never_none_for_an_unset_account():
    registry = LiveSerialRegistry()
    assert registry.get(AccountId.LD1) == ""


def test_registry_set_then_get_round_trips():
    registry = LiveSerialRegistry()
    registry.set(AccountId.LD1, _CUSTOMER_SERIAL)
    assert registry.get(AccountId.LD1) == _CUSTOMER_SERIAL


def test_registry_set_none_or_blank_normalizes_to_empty_string():
    registry = LiveSerialRegistry()
    registry.set(AccountId.LD1, _CUSTOMER_SERIAL)
    registry.set(AccountId.LD1, None)
    assert registry.get(AccountId.LD1) == ""

    registry.set(AccountId.LD2, "   ")
    assert registry.get(AccountId.LD2) == ""


def test_registry_is_strictly_per_account_no_cross_account_use():
    registry = LiveSerialRegistry()
    registry.set(AccountId.LD1, "serial-for-ld1")
    registry.set(AccountId.LD9, "serial-for-ld9")

    assert registry.get(AccountId.LD1) == "serial-for-ld1"
    assert registry.get(AccountId.LD9) == "serial-for-ld9"
    # Every other, never-set account remains blank -- LD1's/LD9's value
    # never leaks anywhere else, and there is no "default"/"current" slot.
    for aid in AccountId:
        if aid not in (AccountId.LD1, AccountId.LD9):
            assert registry.get(aid) == ""


# --- _make_cycle_fn: blank serial fails BEFORE any capture/ADB/touch -------


def test_blank_registry_entry_causes_zero_adb_calls_and_a_contained_error():
    registry = LiveSerialRegistry()  # LD1 never set -- exactly the real
    # customer's pre-fix scenario: the cycle_fn's serial source is blank.
    runner = FakeAdbRunner()
    recognizer = LabelMappingRecognizer(matching_labels=_ALL_LABELS)
    cycle_fn = _make_cycle_fn(AccountId.LD1, registry, runner, recognizer, _bounty_config(), None)

    result = cycle_fn(lambda: False)

    assert result.outcome is BountyOutcome.CAPTURE_UNAVAILABLE
    assert "no ADB serial configured" in result.detail
    assert "LD1" in result.detail
    # The core requirement: zero ADB calls of any kind, not even a capture.
    assert runner.calls == []
    assert runner.capture_calls == []


def test_omitted_serial_after_explicit_clear_also_causes_zero_calls():
    registry = LiveSerialRegistry()
    registry.set(AccountId.LD1, _CUSTOMER_SERIAL)
    registry.set(AccountId.LD1, None)  # GUI Clear
    runner = FakeAdbRunner()
    recognizer = LabelMappingRecognizer(matching_labels=_ALL_LABELS)
    cycle_fn = _make_cycle_fn(AccountId.LD1, registry, runner, recognizer, _bounty_config(), None)

    result = cycle_fn(lambda: False)

    assert result.outcome is BountyOutcome.CAPTURE_UNAVAILABLE
    assert runner.calls == []
    assert runner.capture_calls == []


# --- _make_cycle_fn: a configured serial reaches every helper/capture/tap --


def test_configured_serial_reaches_every_capture_and_tap_argv():
    """Reproduces the customer's exact serial (emulator-5554) flowing
    through the whole real chain: _make_cycle_fn -> run_one_cycle ->
    _accept_or_refresh_slot -> _tap_template/_recognize ->
    capture_screenshot -- every single recorded ADB call (capture AND
    tap) must be scoped to exactly this serial, never blank, never a
    different one."""

    registry = LiveSerialRegistry()
    registry.set(AccountId.LD1, _CUSTOMER_SERIAL)
    runner = _runner_with_valid_capture(_CUSTOMER_SERIAL)
    recognizer = LabelMappingRecognizer(matching_labels=_ALL_LABELS)
    cycle_fn = _make_cycle_fn(AccountId.LD1, registry, runner, recognizer, _bounty_config(), None)

    result = cycle_fn(lambda: False)

    # The mock five-slot flow reaches real completion with this config.
    assert result.outcome is BountyOutcome.COMPLETED_CYCLE
    assert len(runner.calls) > 0  # real tap argv was issued
    assert len(runner.capture_calls) > 0  # real capture argv was issued
    # EVERY recorded call (tap and capture) used exactly the configured
    # serial -- never blank, never a placeholder, never another account's.
    assert all(serial == _CUSTOMER_SERIAL for serial, _args in runner.calls)
    assert all(serial == _CUSTOMER_SERIAL for serial, _args in runner.capture_calls)


def test_configured_serial_is_read_fresh_not_captured_once():
    """The crux of LIVE-SERIAL-001: build the cycle function while the
    registry is still blank (matching build_controller() running before
    any real mapping exists), THEN set the registry (matching a later
    GUI Save) -- the SAME already-built cycle_fn must pick up the new
    value on its next call, with no rebuild/restart."""

    registry = LiveSerialRegistry()  # blank at cycle_fn construction time
    runner = _runner_with_valid_capture(_CUSTOMER_SERIAL)
    recognizer = LabelMappingRecognizer(matching_labels=_ALL_LABELS)
    cycle_fn = _make_cycle_fn(AccountId.LD1, registry, runner, recognizer, _bounty_config(), None)

    first = cycle_fn(lambda: False)
    assert first.outcome is BountyOutcome.CAPTURE_UNAVAILABLE  # blank -> contained, zero calls
    assert runner.calls == []

    registry.set(AccountId.LD1, _CUSTOMER_SERIAL)  # the GUI Save, live
    second = cycle_fn(lambda: False)  # same cycle_fn object, no rebuild

    assert second.outcome is BountyOutcome.COMPLETED_CYCLE
    assert all(serial == _CUSTOMER_SERIAL for serial, _args in runner.calls)


# --- no cross-account use at the cycle_fn/worker level ----------------------


def test_two_accounts_share_one_registry_but_never_cross_use_serials():
    registry = LiveSerialRegistry()
    registry.set(AccountId.LD1, "serial-for-ld1")
    registry.set(AccountId.LD2, "serial-for-ld2")
    runner_1 = _runner_with_valid_capture("serial-for-ld1")
    runner_2 = _runner_with_valid_capture("serial-for-ld2")
    recognizer = LabelMappingRecognizer(matching_labels=_ALL_LABELS)

    cycle_1 = _make_cycle_fn(AccountId.LD1, registry, runner_1, recognizer, _bounty_config(), None)
    cycle_2 = _make_cycle_fn(AccountId.LD2, registry, runner_2, recognizer, _bounty_config(), None)

    result_1 = cycle_1(lambda: False)
    result_2 = cycle_2(lambda: False)

    assert result_1.outcome is BountyOutcome.COMPLETED_CYCLE
    assert result_2.outcome is BountyOutcome.COMPLETED_CYCLE
    assert all(serial == "serial-for-ld1" for serial, _args in runner_1.calls)
    assert all(serial == "serial-for-ld2" for serial, _args in runner_2.calls)
    assert not any(serial == "serial-for-ld2" for serial, _args in runner_1.calls)
    assert not any(serial == "serial-for-ld1" for serial, _args in runner_2.calls)


# --- full AccountWorker thread: exact customer timeline, contained + live --


def test_worker_started_with_blank_serial_is_contained_never_crashes_the_app():
    """Matches the pre-fix customer crash's IMMEDIATE symptom: starting a
    worker whose account has no live serial yet must not raise/crash --
    it must self-stop with a contained, structured error."""

    registry = LiveSerialRegistry()
    runner = FakeAdbRunner()
    recognizer = LabelMappingRecognizer(matching_labels=_ALL_LABELS)
    cycle_fn = _make_cycle_fn(AccountId.LD1, registry, runner, recognizer, _bounty_config(), None)
    worker = AccountWorker(AccountId.LD1, cycle_fn, sleep_fn=lambda s: None)

    worker.start()
    time.sleep(0.05)
    worker.stop(join_timeout=1.0)

    status = worker.status()
    assert status.running is False
    assert status.errored is True
    assert status.last_error is not None
    assert runner.calls == []
    assert runner.capture_calls == []


def test_gui_save_after_build_lets_a_fresh_start_use_the_new_serial_no_restart():
    """The exact customer timeline: build_controller() ran while LD1 was
    unmapped (blank registry entry) -- matching the real bootstrap
    default -- THEN the GUI Save happens (registry.set, live, no
    rebuild) -- THEN the user clicks Start. Before the fix, Start would
    have used the ORIGINAL closure-captured blank serial and crashed
    with ValueError: Invalid ADB serial: ''. After the fix, Start uses
    the live, just-saved serial."""

    registry = LiveSerialRegistry()  # build_controller()'s initial state
    runner = _runner_with_valid_capture(_CUSTOMER_SERIAL)
    recognizer = LabelMappingRecognizer(matching_labels=_ALL_LABELS)
    cycle_fn = _make_cycle_fn(AccountId.LD1, registry, runner, recognizer, _bounty_config(), None)

    # Deterministic single-cycle completion: request stop from INSIDE the
    # worker thread itself, right after the first cycle returns and
    # BEFORE AccountWorker._loop re-checks its while condition -- avoids
    # a race against a second cycle starting (and being interrupted
    # mid-way, which would overwrite last_outcome with "stopped") that a
    # plain sleep-then-stop from the test thread cannot reliably avoid.
    cycle_done = threading.Event()
    worker_box: dict = {}

    def _cycle_then_stop(should_stop):
        try:
            return cycle_fn(should_stop)
        finally:
            cycle_done.set()
            worker_box["worker"].stop()

    worker = AccountWorker(AccountId.LD1, _cycle_then_stop, sleep_fn=lambda s: None)
    worker_box["worker"] = worker

    # GUI Save (this is exactly what LDManagerApp._on_save_mapping now
    # does after a successful save_account_serial() -- see gui.py).
    registry.set(AccountId.LD1, _CUSTOMER_SERIAL)

    worker.start()
    assert cycle_done.wait(timeout=5.0), "first cycle never completed"
    worker.stop(join_timeout=1.0)  # idempotent; joins the now-exiting thread

    status = worker.status()
    assert status.errored is False
    assert status.last_error is None
    assert status.last_outcome == BountyOutcome.COMPLETED_CYCLE.value
    assert len(runner.calls) > 0
    assert all(serial == _CUSTOMER_SERIAL for serial, _args in runner.calls)


# --- individual/global stop behavior preserved (unaffected by this fix) ----


def test_stopping_one_account_does_not_affect_another_with_live_registries():
    registry = LiveSerialRegistry()
    registry.set(AccountId.LD1, "serial-a")
    registry.set(AccountId.LD2, "serial-b")
    recognizer = LabelMappingRecognizer(matching_labels=frozenset())  # never completes -> loops

    def make_looping_cycle(account_id, serial):
        def cycle(should_stop):
            while not should_stop():
                time.sleep(0.005)
            return type("R", (), {"outcome": "stopped"})()
        return cycle

    worker_a = AccountWorker(AccountId.LD1, make_looping_cycle(AccountId.LD1, "serial-a"), sleep_fn=lambda s: None)
    worker_b = AccountWorker(AccountId.LD2, make_looping_cycle(AccountId.LD2, "serial-b"), sleep_fn=lambda s: None)
    controller = AccountController({AccountId.LD1: worker_a, AccountId.LD2: worker_b})

    controller.start_account(AccountId.LD1)
    controller.start_account(AccountId.LD2)
    time.sleep(0.05)

    controller.stop_account(AccountId.LD1, join_timeout=1.0)

    assert controller.worker(AccountId.LD1).is_running is False
    assert controller.worker(AccountId.LD2).is_running is True

    controller.stop_account(AccountId.LD2, join_timeout=1.0)
    assert controller.worker(AccountId.LD2).is_running is False


def test_global_stop_all_still_sends_no_further_calls_with_a_live_registry():
    registry = LiveSerialRegistry()
    registry.set(AccountId.LD1, _CUSTOMER_SERIAL)
    runner = _runner_with_valid_capture(_CUSTOMER_SERIAL)
    recognizer = LabelMappingRecognizer(matching_labels=frozenset())  # never target-confirmed -> just polls/loops safely

    call_marker: list = []

    def cycle(should_stop):
        if not should_stop():
            call_marker.append(1)
        time.sleep(0.005)
        return type("R", (), {"outcome": "tick"})()

    worker = AccountWorker(AccountId.LD1, cycle, sleep_fn=lambda s: None)
    controller = AccountController({AccountId.LD1: worker})

    controller.start_all()
    time.sleep(0.05)
    controller.stop_all(join_timeout=1.0)

    assert controller.worker(AccountId.LD1).is_running is False
    count_at_stop = len(call_marker)
    time.sleep(0.05)
    assert len(call_marker) == count_at_stop  # no growth after the joined stop
    assert runner.calls == []  # this fake cycle never touches the runner at all
