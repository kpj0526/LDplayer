"""Per-account worker/controller tests (MVP-001).

No real ADB/device/GUI here -- cycle functions are simple fakes. Timing
uses very short sleeps/joins so this stays fast and non-flaky while
still exercising real thread start/stop behavior for the "global stop
leaves no automatic touch" and "individual stop only local" contracts.
"""

from __future__ import annotations

import threading
import time

from ldmanager.controller import AccountController, AccountWorker
from ldmanager.models import AccountId


class _DummyOutcome:
    def __init__(self, value: str) -> None:
        self.outcome = value


class _DummyOutcomeWithDetail:
    def __init__(self, value: str, detail: str) -> None:
        self.outcome = value
        self.detail = detail


def _make_worker(account_id, cycle_fn, **kwargs) -> AccountWorker:
    return AccountWorker(account_id, cycle_fn, sleep_fn=lambda s: None, **kwargs)


# --- basic lifecycle --------------------------------------------------------


def test_worker_start_runs_cycles_until_stopped():
    call_count = {"n": 0}

    def cycle(should_stop):
        call_count["n"] += 1
        return _DummyOutcome("ok")

    worker = _make_worker(AccountId.LD1, cycle)
    assert worker.start() is True
    # Let it run a handful of iterations, then stop and join.
    time.sleep(0.05)
    worker.stop(join_timeout=1.0)

    assert worker.is_running is False
    assert call_count["n"] >= 1
    assert worker.status().running is False


def test_starting_an_already_running_worker_is_a_noop():
    ready = threading.Event()

    def cycle(should_stop):
        ready.set()
        while not should_stop():
            time.sleep(0.005)
        return _DummyOutcome("ok")

    worker = _make_worker(AccountId.LD1, cycle)
    assert worker.start() is True
    ready.wait(timeout=1.0)
    assert worker.start() is False  # already running
    worker.stop(join_timeout=1.0)


# --- individual stop is account-local --------------------------------------


def test_stopping_one_account_does_not_affect_another():
    def make_cycle(tag, calls):
        def cycle(should_stop):
            calls.append(tag)
            while not should_stop():
                time.sleep(0.005)
            return _DummyOutcome("stopped")
        return cycle

    calls_a: list = []
    calls_b: list = []
    worker_a = _make_worker(AccountId.LD1, make_cycle("A", calls_a))
    worker_b = _make_worker(AccountId.LD2, make_cycle("B", calls_b))
    controller = AccountController({AccountId.LD1: worker_a, AccountId.LD2: worker_b})

    controller.start_account(AccountId.LD1)
    controller.start_account(AccountId.LD2)
    time.sleep(0.05)

    controller.stop_account(AccountId.LD1, join_timeout=1.0)

    assert controller.worker(AccountId.LD1).is_running is False
    assert controller.worker(AccountId.LD2).is_running is True

    controller.stop_account(AccountId.LD2, join_timeout=1.0)
    assert controller.worker(AccountId.LD2).is_running is False


# --- global stop: no automatic touch after stop -----------------------------


def test_global_stop_all_sends_no_further_touch_calls_after_settling():
    """Simulates a worker whose cycle issues a 'touch' (recorded call)
    per loop iteration while respecting should_stop -- proves that once
    stop_all() returns (with a join), no further touch is recorded."""

    touches: list = []

    def cycle(should_stop):
        if not should_stop():
            touches.append(1)
        time.sleep(0.005)
        return _DummyOutcome("tick")

    worker = _make_worker(AccountId.LD1, cycle)
    controller = AccountController({AccountId.LD1: worker})

    controller.start_all()
    time.sleep(0.05)  # let a few iterations happen
    controller.stop_all(join_timeout=1.0)

    assert controller.worker(AccountId.LD1).is_running is False
    count_at_stop = len(touches)
    time.sleep(0.05)  # give a misbehaving implementation a chance to keep going
    assert len(touches) == count_at_stop  # no growth after the joined stop


def test_stop_all_only_affects_started_workers_and_never_raises():
    def cycle(should_stop):
        return _DummyOutcome("ok")

    workers = {aid: _make_worker(aid, cycle) for aid in AccountId}
    controller = AccountController(workers)
    controller.stop_all(join_timeout=0.1)  # nothing running; must not raise
    for aid in AccountId:
        assert controller.worker(aid).is_running is False


# --- worker exception containment -------------------------------------------


def test_worker_exception_is_contained_and_does_not_affect_other_workers():
    def crashing_cycle(should_stop):
        raise RuntimeError("boom")

    def normal_cycle(should_stop):
        while not should_stop():
            time.sleep(0.005)
        return _DummyOutcome("ok")

    crashing = _make_worker(AccountId.LD1, crashing_cycle)
    normal = _make_worker(AccountId.LD2, normal_cycle)
    controller = AccountController({AccountId.LD1: crashing, AccountId.LD2: normal})

    controller.start_all()
    time.sleep(0.05)

    crashing_status = controller.status(AccountId.LD1)
    assert crashing_status.running is False
    assert crashing_status.last_error is not None
    assert "boom" in crashing_status.last_error

    # The other worker is completely unaffected.
    assert controller.worker(AccountId.LD2).is_running is True
    controller.stop_account(AccountId.LD2, join_timeout=1.0)


# --- status/log bookkeeping --------------------------------------------------


def test_status_snapshot_reflects_cycles_and_recent_log():
    def cycle(should_stop):
        return _DummyOutcome("done")

    worker = _make_worker(AccountId.LD3, cycle)
    worker.start()
    time.sleep(0.05)
    worker.stop(join_timeout=1.0)

    status = worker.status()
    assert status.account_id is AccountId.LD3
    assert status.cycles_completed >= 1
    assert status.last_outcome == "done"
    assert any("done" in line for line in status.recent_log)


def test_all_statuses_covers_every_account_independently():
    def cycle(should_stop):
        return _DummyOutcome("ok")

    workers = {aid: _make_worker(aid, cycle) for aid in AccountId}
    controller = AccountController(workers)
    statuses = controller.all_statuses()
    assert set(statuses.keys()) == set(AccountId)
    for aid, status in statuses.items():
        assert status.account_id is aid
        assert status.running is False


# --- REL-UPDATE-003: runtime (phase/locked_slots/slot_states) sync ----------


class _FakeRuntime:
    """Minimal stand-in for ldmanager.runtime.AccountMissionRuntime."""

    def __init__(self) -> None:
        self.phase = "CONFIGURING"
        self.locked_count = 2

        class _Slot:
            def __init__(self, value: str) -> None:
                self.value = value

        self.slots = [_Slot("target_locked"), _Slot("target_locked"), _Slot("unknown")]


def test_runtime_status_syncs_on_a_normal_non_error_cycle():
    """Regression guard: the runtime-status sync previously sat after an
    unconditional `break` in the error branch, making it dead code -- it
    never ran on an ordinary (non-error) cycle. Import candidate fix
    (REL-UPDATE-003): verify phase/locked_slots/slot_states now reach
    AccountWorkerStatus on a ordinary successful cycle, not just never."""

    def cycle(should_stop):
        return _DummyOutcome("completed_cycle")  # not one of the error outcomes

    worker = _make_worker(AccountId.LD2, cycle)
    worker.runtime = _FakeRuntime()
    worker.start()
    time.sleep(0.05)
    worker.stop(join_timeout=1.0)

    status = worker.status()
    assert status.phase == "CONFIGURING"
    assert status.locked_slots == 2
    assert status.slot_states == ["target_locked", "target_locked", "unknown"]


def test_runtime_status_also_syncs_on_an_error_cycle():
    def cycle(should_stop):
        return _DummyOutcome("adb_error")

    worker = _make_worker(AccountId.LD4, cycle)
    worker.runtime = _FakeRuntime()
    worker.start()
    time.sleep(0.05)
    worker.stop(join_timeout=1.0)

    status = worker.status()
    assert status.errored is True
    assert status.phase == "CONFIGURING"  # synced before the error break, not lost
    assert status.locked_slots == 2


# --- DIAGNOSTIC-DETAIL-001: the cycle result's own detail is surfaced ------


def test_error_cycle_detail_reaches_last_error_and_recent_log():
    """Real customer report: a generic 'capture_unavailable' with no way
    to tell which of the many possible capture/tap steps actually
    failed. The cycle result's own specific detail string must now
    reach both last_error and the log, not just the generic outcome."""

    def cycle(should_stop):
        return _DummyOutcomeWithDetail("capture_unavailable", "Slot 1: select tap failed (rc=1).")

    worker = _make_worker(AccountId.LD1, cycle)
    worker.start()
    time.sleep(0.05)
    worker.stop(join_timeout=1.0)

    status = worker.status()
    assert status.errored is True
    assert "capture_unavailable" in status.last_error
    assert "Slot 1: select tap failed (rc=1)." in status.last_error
    assert any("Slot 1: select tap failed (rc=1)." in line for line in status.recent_log)


def test_non_error_cycle_detail_also_reaches_recent_log():
    def cycle(should_stop):
        return _DummyOutcomeWithDetail("completed_cycle", "Verified reward cycle complete; slots reset.")

    worker = _make_worker(AccountId.LD2, cycle)
    worker.start()
    time.sleep(0.05)
    worker.stop(join_timeout=1.0)

    status = worker.status()
    assert any("Verified reward cycle complete; slots reset." in line for line in status.recent_log)


def test_a_result_without_detail_is_a_safe_noop_never_raises():
    """Backward compatibility: a minimal fake result (like the plain
    _DummyOutcome used throughout the rest of this file) has no
    .detail attribute at all -- must never raise, must behave exactly
    as before this packet."""

    def cycle(should_stop):
        return _DummyOutcome("adb_error")  # no .detail attribute

    worker = _make_worker(AccountId.LD3, cycle)
    worker.start()
    time.sleep(0.05)
    worker.stop(join_timeout=1.0)

    status = worker.status()
    assert status.errored is True
    assert status.last_error == "adb_error: account worker stopped"


# --- ERROR-VISIBILITY-001: flagged-but-not-fatal outcomes -----------------


def test_flagged_non_fatal_outcome_is_visible_but_worker_keeps_going():
    """Real customer report: "refresh_popup_not_verified" kept
    recurring but "doesn't get caught in the error log" -- it was
    never in the fatal-outcome set, so it only ever reached the plain,
    scrolling "cycle result:" log line, never the GUI's red last_error/
    errored display. Now it's flagged (visible) WITHOUT stopping the
    worker -- bounty_mission.py's bounded-retry design expects the
    worker to keep calling run_one_cycle again."""

    call_count = {"n": 0}

    def cycle(should_stop):
        call_count["n"] += 1
        return _DummyOutcomeWithDetail(
            "refresh_popup_not_verified", "Slot 3: refresh popup never verified structurally."
        )

    worker = _make_worker(AccountId.LD1, cycle)
    worker.start()
    time.sleep(0.05)
    worker.stop(join_timeout=1.0)

    status = worker.status()
    assert call_count["n"] > 1, "worker must keep retrying, not stop, on this outcome"
    assert status.running is False  # stopped via worker.stop(), not via the outcome itself
    assert status.errored is True
    assert "refresh_popup_not_verified" in status.last_error
    assert "Slot 3: refresh popup never verified structurally." in status.last_error
    assert any(line.startswith("WARN:") for line in status.recent_log)
    assert not any(line.startswith("ERROR:") for line in status.recent_log)


def test_flagged_non_fatal_outcome_clears_after_a_later_successful_cycle():
    """A transient refresh_popup_not_verified must not leave the GUI
    permanently red once the flow recovers on a later cycle."""

    call_count = {"n": 0}

    def cycle(should_stop):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return _DummyOutcomeWithDetail("slot_accept_failed", "Slot 2: no acceptable target.")
        return _DummyOutcome("kill_progress_not_complete")

    worker = _make_worker(AccountId.LD2, cycle)
    worker.start()
    time.sleep(0.05)
    worker.stop(join_timeout=1.0)

    status = worker.status()
    assert call_count["n"] > 1
    assert status.errored is False
    assert status.last_error is None


def test_all_six_flagged_outcomes_are_visible_without_stopping():
    for outcome in (
        "refresh_popup_not_verified", "slot_accept_failed", "reward_verify_failed",
        "result_verify_failed", "mission_list_verify_failed", "re_accept_failed",
    ):
        call_count = {"n": 0}

        def cycle(should_stop, outcome=outcome):
            call_count["n"] += 1
            return _DummyOutcome(outcome)

        worker = _make_worker(AccountId.LD3, cycle)
        worker.start()
        time.sleep(0.05)
        worker.stop(join_timeout=1.0)

        status = worker.status()
        assert call_count["n"] > 1, f"{outcome}: worker must keep retrying"
        assert status.errored is True, f"{outcome}: must be flagged visible"
        assert outcome in status.last_error, f"{outcome}: must appear in last_error"
