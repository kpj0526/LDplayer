"""Per-account cancellable worker + controller (MVP-001).

One independent, cancellable background worker per account (LD1..LD9).
Each worker repeatedly calls an injected ``run_cycle`` function (in
production, :func:`ldmanager.mission.run_one_cycle` bound to that
account's serial/runner/recognizer/config) until told to stop. A stop
request is account-local: stopping one account's worker never touches
another account's thread, state, or ADB runner. An exception raised
inside a worker's cycle is contained — logged and recorded on that
worker's own status — and never propagates to the controller or to any
other worker.

No GUI code, no recognition/game logic, and no ADB command construction
lives here; this module only owns thread lifecycle + status bookkeeping.

As of DIAGNOSTIC-DETAIL-001, ``last_error``/the log line for an error
cycle also includes the cycle result's own specific ``detail`` string
(via ``getattr(result, "detail", "")``, duck-typed exactly like
``outcome`` already was) -- e.g. "Slot 1: select tap failed (rc=1)"
rather than just the generic "capture_unavailable: account worker
stopped". A real customer's live run previously produced only that
generic outcome with no way to tell which of the many possible
capture/tap steps actually failed short of reading source -- this
closes that gap. Every non-error cycle's log line gets the same detail
appended too, for the same reason.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field, replace
from typing import Callable, Dict, List, Optional

from .models import AccountId

#: Signature a production cycle function must have: given a ``should_stop``
#: check, run exactly one mission cycle and return some result object that
#: exposes a string-like ``outcome`` attribute (kept loose/duck-typed here
#: so tests can inject a minimal fake without importing ldmanager.mission).
CycleFn = Callable[[Callable[[], bool]], object]

_MAX_RECENT_LOG_LINES = 20

# ERROR-VISIBILITY-001: a real customer report -- "refresh_popup_not_
# verified" kept recurring but "doesn't get caught in the error log."
# Root cause: this outcome (and five siblings below) was never in the
# original fatal-outcome set, so it only ever reached the plain,
# scrolling "cycle result:" log line -- never the GUI's dedicated red
# last_error/errored display the fatal outcomes populate. These six are
# genuine "something didn't work as expected" results (not informational
# like kill_progress_not_complete/completed_cycle/stopped), but the
# whole point of bounty_mission.py's bounded-retry design is that the
# worker keeps calling run_one_cycle again afterward (retrying from
# wherever runtime left off) -- stopping the worker here would fight
# that design. So these are flagged (last_error/errored set, visible in
# red) WITHOUT stopping the worker, distinct from the fatal set below.
_FLAGGED_NON_FATAL_OUTCOMES = frozenset({
    "refresh_popup_not_verified",
    "slot_accept_failed",
    "reward_verify_failed",
    "result_verify_failed",
    "mission_list_verify_failed",
    "re_accept_failed",
})


@dataclass
class AccountWorkerStatus:
    """Account-local runtime status, safe to read from the GUI thread."""

    account_id: AccountId
    running: bool = False
    current_slot: Optional[int] = None
    cycles_completed: int = 0
    last_outcome: Optional[str] = None
    last_error: Optional[str] = None
    errored: bool = False
    recent_log: List[str] = field(default_factory=list)
    phase: str = "IDLE"
    locked_slots: int = 0
    slot_states: List[str] = field(default_factory=list)

    def snapshot(self) -> "AccountWorkerStatus":
        """A shallow copy safe to hand to a caller outside the lock."""

        return replace(self, recent_log=list(self.recent_log), slot_states=list(self.slot_states))


class AccountWorker:
    """One independent, cancellable background worker for one account."""

    def __init__(
        self,
        account_id: AccountId,
        run_cycle: CycleFn,
        *,
        logger=None,
        idle_delay_seconds: float = 0.0,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        self.account_id = account_id
        self._run_cycle = run_cycle
        self._logger = logger
        self._idle_delay_seconds = idle_delay_seconds
        self._sleep_fn = sleep_fn

        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._status = AccountWorkerStatus(account_id=account_id)
        self._thread: Optional[threading.Thread] = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def stop_requested(self) -> bool:
        return self._stop_event.is_set()

    def status(self) -> AccountWorkerStatus:
        with self._lock:
            return self._status.snapshot()

    def _append_log(self, message: str) -> None:
        with self._lock:
            self._status.recent_log.append(message)
            if len(self._status.recent_log) > _MAX_RECENT_LOG_LINES:
                del self._status.recent_log[0]

    def start(self) -> bool:
        """Start the background thread. No-op (returns False) if already running."""

        if self.is_running:
            return False
        self._stop_event.clear()
        with self._lock:
            self._status.running = True
            self._status.last_error = None
            self._status.errored = False
        self._thread = threading.Thread(
            target=self._loop, name=f"ldmanager-worker-{self.account_id.value}", daemon=True
        )
        self._thread.start()
        return True

    def stop(self, *, join_timeout: Optional[float] = None) -> None:
        """Request cancellation for THIS account only.

        Never touches any other worker's stop event, thread, or status.
        """

        self._stop_event.set()
        if join_timeout is not None and self._thread is not None:
            self._thread.join(timeout=join_timeout)

    def _loop(self) -> None:
        try:
            while not self._stop_event.is_set():
                result = self._run_cycle(lambda: self._stop_event.is_set())
                outcome = getattr(result, "outcome", result)
                outcome_str = getattr(outcome, "value", str(outcome))
                # DIAGNOSTIC-DETAIL-001: the cycle result's own rich,
                # specific reason (e.g. "Slot 1: select tap failed
                # (rc=1)") was previously computed by bounty_mission.py
                # but never surfaced anywhere -- only this generic
                # outcome_str reached the GUI/log, making a real
                # capture_unavailable/etc. impossible to diagnose without
                # reading source. Duck-typed (getattr, default "") so
                # this stays decoupled from any specific result type --
                # a fake/minimal test result with no .detail is still a
                # safe no-op here, exactly like outcome/.value above.
                # Passes through SensitiveDataRedactionFilter (logs.py)
                # exactly like every other logged message.
                detail = getattr(result, "detail", "") or ""
                # REL-UPDATE-003 fix: this runtime-status sync previously sat
                # *after* an unconditional `break` in the error branch below,
                # making it dead code -- phase/locked_slots/slot_states never
                # updated the GUI on any cycle. Moved here so it runs on
                # every cycle (error or not), atomically with the other
                # status fields.
                runtime = getattr(self, "runtime", None)
                with self._lock:
                    self._status.cycles_completed += 1
                    self._status.last_outcome = outcome_str
                    self._status.current_slot = None
                    if runtime is not None:
                        self._status.phase = runtime.phase
                        self._status.locked_slots = runtime.locked_count
                        self._status.slot_states = [item.value for item in runtime.slots]
                if outcome_str in {"recognition_failed", "capture_unavailable", "stale_screen", "unknown_screen", "adb_error"}:
                    last_error = f"{outcome_str}: account worker stopped" + (f" -- {detail}" if detail else "")
                    with self._lock:
                        self._status.errored = True
                        self._status.last_error = last_error
                    self._append_log(f"ERROR: {outcome_str}; account worker stopped" + (f" -- {detail}" if detail else ""))
                    if self._logger is not None:
                        self._logger.error("cycle error outcome=%s detail=%s", outcome_str, detail)
                    break
                if outcome_str in _FLAGGED_NON_FATAL_OUTCOMES:
                    # ERROR-VISIBILITY-001: same red last_error/errored
                    # display as the fatal set above, but the worker
                    # keeps going -- bounty_mission.py's bounded-retry
                    # design expects run_one_cycle to be called again.
                    last_error = f"{outcome_str}: retrying" + (f" -- {detail}" if detail else "")
                    with self._lock:
                        self._status.errored = True
                        self._status.last_error = last_error
                    self._append_log(f"WARN: {outcome_str}; retrying" + (f" -- {detail}" if detail else ""))
                    if self._logger is not None:
                        self._logger.warning("cycle warning outcome=%s detail=%s", outcome_str, detail)
                else:
                    with self._lock:
                        self._status.errored = False
                        self._status.last_error = None
                    self._append_log(f"cycle result: {outcome_str}" + (f" -- {detail}" if detail else ""))
                    if self._logger is not None:
                        self._logger.info("cycle result: %s detail=%s", outcome_str, detail)

                if self._stop_event.is_set():
                    break
                if self._idle_delay_seconds:
                    self._sleep_fn(self._idle_delay_seconds)
        except Exception as exc:  # worker exception containment
            if self._logger is not None:
                self._logger.exception("worker crashed")
            with self._lock:
                self._status.last_error = f"{type(exc).__name__}: {exc}"
                self._status.errored = True
            self._append_log(f"ERROR: {type(exc).__name__}: {exc}")
        finally:
            with self._lock:
                self._status.running = False


class AccountController:
    """Owns exactly one :class:`AccountWorker` per account; no shared
    mutable state between workers beyond this simple dict lookup."""

    def __init__(self, workers: Dict[AccountId, AccountWorker]) -> None:
        self._workers = dict(workers)

    def worker(self, account_id: AccountId) -> AccountWorker:
        return self._workers[account_id]

    def account_ids(self) -> List[AccountId]:
        return list(self._workers.keys())

    def start_account(self, account_id: AccountId) -> bool:
        return self._workers[account_id].start()

    def stop_account(self, account_id: AccountId, *, join_timeout: Optional[float] = None) -> None:
        self._workers[account_id].stop(join_timeout=join_timeout)

    def start_all(self) -> Dict[AccountId, bool]:
        return {account_id: worker.start() for account_id, worker in self._workers.items()}

    def stop_all(self, *, join_timeout: Optional[float] = None) -> None:
        for worker in self._workers.values():
            worker.stop(join_timeout=join_timeout)

    def status(self, account_id: AccountId) -> AccountWorkerStatus:
        return self._workers[account_id].status()

    def all_statuses(self) -> Dict[AccountId, AccountWorkerStatus]:
        return {account_id: worker.status() for account_id, worker in self._workers.items()}
