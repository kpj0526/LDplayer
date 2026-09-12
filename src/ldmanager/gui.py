"""Basic native GUI (MVP-001).

Tkinter (Python's bundled, native-widget toolkit — no extra dependency)
showing LD1..LD9 with per-account status/current-slot/targets-
found/error/recent-log and Start/Stop buttons, plus a global Start
All/Stop All pair. Construction (``LDManagerApp(controller)``) never
starts the Tk event loop by itself — call :meth:`LDManagerApp.run` for
that — so the app object can be built and inspected in a test without
blocking.

This module only renders :class:`~ldmanager.controller.AccountWorkerStatus`
snapshots and forwards button clicks to the controller; it contains no
recognition/mission/ADB logic of its own.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from .controller import AccountController, AccountWorkerStatus
from .models import AccountId

#: How often the GUI polls the controller for fresh status, in ms.
DEFAULT_REFRESH_INTERVAL_MS = 500


class AccountPanel(ttk.LabelFrame):
    """One LDx panel: status line + Start/Stop buttons."""

    def __init__(self, parent: tk.Widget, controller: AccountController, account_id: AccountId) -> None:
        super().__init__(parent, text=account_id.value)
        self._controller = controller
        self._account_id = account_id

        self.status_var = tk.StringVar(value="stopped")
        self.slot_var = tk.StringVar(value="slot: -")
        self.progress_var = tk.StringVar(value="cycles: 0")
        self.error_var = tk.StringVar(value="")
        self.log_var = tk.StringVar(value="")

        ttk.Label(self, textvariable=self.status_var).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(self, textvariable=self.slot_var).grid(row=1, column=0, sticky="w")
        ttk.Label(self, textvariable=self.progress_var).grid(row=1, column=1, sticky="w")
        ttk.Label(self, textvariable=self.error_var, foreground="red").grid(
            row=2, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(self, textvariable=self.log_var, foreground="gray30").grid(
            row=3, column=0, columnspan=2, sticky="w"
        )

        button_row = ttk.Frame(self)
        button_row.grid(row=4, column=0, columnspan=2, sticky="we")
        self.start_button = ttk.Button(button_row, text="Start", command=self._on_start)
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(button_row, text="Stop", command=self._on_stop)
        self.stop_button.pack(side="left")

    def _on_start(self) -> None:
        self._controller.start_account(self._account_id)

    def _on_stop(self) -> None:
        self._controller.stop_account(self._account_id)

    def refresh(self, status: AccountWorkerStatus) -> None:
        self.status_var.set("running" if status.running else "stopped")
        self.slot_var.set(f"slot: {status.current_slot if status.current_slot is not None else '-'}")
        self.progress_var.set(f"cycles: {status.cycles_completed} last: {status.last_outcome or '-'}")
        self.error_var.set(status.last_error or "")
        self.log_var.set(status.recent_log[-1] if status.recent_log else "")


class LDManagerApp(tk.Tk):
    """Root window: global controls + one :class:`AccountPanel` per account."""

    def __init__(
        self,
        controller: AccountController,
        *,
        refresh_interval_ms: int = DEFAULT_REFRESH_INTERVAL_MS,
        auto_refresh: bool = True,
    ) -> None:
        super().__init__()
        self.title("ldmanager (MVP)")
        self._controller = controller
        self._refresh_interval_ms = refresh_interval_ms
        self._panels: dict[AccountId, AccountPanel] = {}

        global_row = ttk.Frame(self)
        global_row.pack(fill="x", padx=8, pady=8)
        ttk.Button(global_row, text="Start All", command=self._on_start_all).pack(side="left")
        ttk.Button(global_row, text="Stop All", command=self._on_stop_all).pack(side="left")

        grid = ttk.Frame(self)
        grid.pack(fill="both", expand=True, padx=8, pady=8)
        for index, account_id in enumerate(AccountId):
            panel = AccountPanel(grid, controller, account_id)
            panel.grid(row=index // 3, column=index % 3, padx=4, pady=4, sticky="nsew")
            self._panels[account_id] = panel

        if auto_refresh:
            self.after(0, self._refresh)

    def _on_start_all(self) -> None:
        self._controller.start_all()

    def _on_stop_all(self) -> None:
        self._controller.stop_all()

    def _refresh(self) -> None:
        statuses = self._controller.all_statuses()
        for account_id, panel in self._panels.items():
            status = statuses.get(account_id)
            if status is not None:
                panel.refresh(status)
        self.after(self._refresh_interval_ms, self._refresh)

    def run(self) -> None:
        """Start the Tk event loop (blocks). Not called by construction
        or by any test — only the real entry point calls this."""

        self.mainloop()
