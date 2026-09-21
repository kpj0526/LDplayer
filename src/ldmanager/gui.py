"""Basic native GUI (MVP-001 / UI-ADB-001).

Tkinter (Python's bundled, native-widget toolkit — no extra dependency)
showing LD1..LD9 with per-account status/current-slot/targets-
found/error/recent-log and Start/Stop buttons, plus a global Start
All/Stop All pair. Construction (``LDManagerApp(controller)``) never
starts the Tk event loop by itself — call :meth:`LDManagerApp.run` for
that — so the app object can be built and inspected in a test without
blocking.

As of UI-ADB-001, each panel also lets the customer **register or
clear that account's ADB serial from the GUI** — never by hand-editing
YAML/terminal — via a global "Refresh ADB devices" button (reads
`adb devices`, never taps anything) plus a per-account combobox
(pick a discovered serial, or type one explicitly) with Save/Clear.
Saving/clearing is pure config file I/O
(:mod:`ldmanager.config_mapping`) — it never touches ADB and never
starts a worker. A mapping must cross-check as
:attr:`~ldmanager.discovery.ConnectionStatus.OK` (a fresh "Refresh ADB
devices" click, after a successful save) before that account's Start
button is enabled; discovered devices are never auto-assigned to an
account — the user always picks or types the value that gets saved.

As of ADB-PATH-001, a global row also shows the **configured vs.
effective ADB executable path** (what's in ``configs/config.yaml`` vs.
what :func:`ldmanager.adb.resolve_adb_path` actually resolved to, and
whether that file exists right now) plus **Browse/Save/Clear**
controls — a customer whose `adb.exe` isn't on `PATH`/in a standard
LDPlayer install location can now point at it directly, without
terminal/YAML editing, without needing to guess the correct YAML
escaping for a Windows path. Saving a valid path immediately updates
the live runner (no restart) and re-runs discovery; saving an
invalid/missing path is rejected visibly and changes nothing.

As of LIVE-SERIAL-001, a successful Save/Clear also updates the
optional injected ``serial_registry`` (duck-typed: only ``.set(account_id,
serial)`` is called) so an already-built -- and possibly already
running -- worker's very next mission cycle sees the new value
immediately, with no restart. Fixes a real customer crash: previously,
Save only ever updated the config *file* on disk; a worker's cycle
function had already captured its serial as a plain string once, at
``build_controller()`` time (usually blank, since bootstrap creates a
null mapping), and never learned about a later Save at all.

This module only renders controller/mapping status snapshots and
forwards button clicks to the controller/config-mapping/discovery
helpers; it contains no recognition/mission logic of its own and never
constructs an :class:`~ldmanager.adb.AdbRunner` itself (one is injected
by the caller, e.g. ``app.py``, for the Refresh button only).
"""

from __future__ import annotations

import tkinter as tk
import time
import os
from pathlib import Path
from tkinter import filedialog, ttk
from typing import Callable, Optional

from .adb import AdbRunner, resolve_adb_path
from .calibration import TEMPLATE_SLOTS, crop_template
from .capture_backends import WindowCaptureError, WindowsGraphicsCaptureProvider, align_game_viewport
from .window_targets import list_ld_windows, suggested_window
from .config import ConfigError
from .config_mapping import (
    load_current_adb_mapping,
    load_current_adb_path,
    save_account_serial,
    save_adb_path,
)
from .controller import AccountController, AccountWorkerStatus
from .discovery import ConnectionStatus, compute_account_connection_statuses, discover_devices
from .models import AccountId
from .screenshot import capture_screenshot

#: How often the GUI polls the controller for fresh status, in ms.
DEFAULT_REFRESH_INTERVAL_MS = 500

_NOT_YET_REFRESHED_DETAIL = "ADB devices not yet refreshed — click 'Refresh ADB devices'."


class AccountPanel(ttk.LabelFrame):
    """One LDx panel: worker status/controls + ADB mapping registration."""

    def __init__(
        self,
        parent: tk.Widget,
        controller: AccountController,
        account_id: AccountId,
        *,
        on_save_mapping: Callable[[AccountId, str], None],
        on_clear_mapping: Callable[[AccountId], None],
        on_capture_test: Callable[[AccountId, str], None],
    ) -> None:
        super().__init__(parent, text=account_id.value)
        self._controller = controller
        self._account_id = account_id
        self._on_save_mapping_cb = on_save_mapping
        self._on_clear_mapping_cb = on_clear_mapping
        self._on_capture_test_cb = on_capture_test
        self._connection_status: Optional[ConnectionStatus] = None
        self._capture_ready = False
        self._mapped_serial = ""
        self._window_targets = {}

        self.status_var = tk.StringVar(value="stopped")
        self.slot_var = tk.StringVar(value="slot: -")
        self.progress_var = tk.StringVar(value="cycles: 0")
        self.error_var = tk.StringVar(value="")
        self.log_var = tk.StringVar(value="")
        self.phase_var = tk.StringVar(value="phase: IDLE  locked: 0/5")

        ttk.Label(self, textvariable=self.status_var).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(self, textvariable=self.slot_var).grid(row=1, column=0, sticky="w")
        ttk.Label(self, textvariable=self.progress_var).grid(row=1, column=1, sticky="w")
        ttk.Label(self, textvariable=self.error_var, foreground="red").grid(
            row=2, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(self, textvariable=self.log_var, foreground="gray30").grid(
            row=3, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(self, textvariable=self.phase_var).grid(row=10, column=0, columnspan=2, sticky="w")

        button_row = ttk.Frame(self)
        button_row.grid(row=4, column=0, columnspan=2, sticky="we")
        self.start_button = ttk.Button(button_row, text="Start", command=self._on_start)
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(button_row, text="Stop", command=self._on_stop)
        self.stop_button.pack(side="left")
        # Safe default: disabled until a Refresh confirms this account's
        # mapping is actually OK (never enabled just because a serial
        # string was saved).
        self.start_button.state(["disabled"])

        ttk.Separator(self, orient="horizontal").grid(row=5, column=0, columnspan=2, sticky="we", pady=4)

        ttk.Label(self, text="ADB serial:").grid(row=6, column=0, sticky="w")
        self.serial_var = tk.StringVar(value="")
        self.serial_combo = ttk.Combobox(self, textvariable=self.serial_var, values=[])
        self.serial_combo.grid(row=6, column=1, sticky="we")

        self.mapping_status_var = tk.StringVar(value="unmapped")
        ttk.Label(self, textvariable=self.mapping_status_var).grid(row=7, column=0, columnspan=2, sticky="w")
        self.mapping_error_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.mapping_error_var, foreground="red", wraplength=330).grid(
            row=8, column=0, columnspan=2, sticky="w"
        )

        mapping_button_row = ttk.Frame(self)
        mapping_button_row.grid(row=9, column=0, columnspan=2, sticky="we")
        self.save_button = ttk.Button(mapping_button_row, text="Save", command=self._on_save_clicked)
        self.save_button.pack(side="left")
        self.clear_button = ttk.Button(mapping_button_row, text="Clear", command=self._on_clear_clicked)
        self.clear_button.pack(side="left")
        self.capture_button = ttk.Button(mapping_button_row, text="Test capture", command=self._on_capture_clicked)
        self.capture_button.pack(side="left")
        self.window_var = tk.StringVar(value="")
        ttk.Label(self, text="LD window:").grid(row=11, column=0, sticky="w")
        self.window_combo = ttk.Combobox(self, textvariable=self.window_var, state="readonly", width=30)
        self.window_combo.grid(row=11, column=1, sticky="we")
        self.window_combo.bind("<<ComboboxSelected>>", lambda _event: self.set_capture_ready(False))

    def set_window_targets(self, targets):
        self._window_targets = {target.display: target for target in targets}
        self.window_combo["values"] = list(self._window_targets)
        if self.window_var.get() not in self._window_targets:
            choice = suggested_window(self._account_id.value, targets)
            self.window_var.set(choice.display if choice else "")
            self.set_capture_ready(False)

    def selected_window(self):
        return self._window_targets.get(self.window_var.get())

    def _on_start(self) -> None:
        if self._connection_status is not ConnectionStatus.OK or not self._capture_ready:
            self.mapping_error_var.set(
                "Cannot start: confirm ADB mapping and run a successful Test capture first."
            )
            return
        self._controller.start_account(self._account_id)

    def _on_stop(self) -> None:
        self._controller.stop_account(self._account_id)

    def _on_save_clicked(self) -> None:
        self._on_save_mapping_cb(self._account_id, self.serial_var.get())

    def _on_clear_clicked(self) -> None:
        self._on_clear_mapping_cb(self._account_id)

    def _on_capture_clicked(self) -> None:
        if self._connection_status is not ConnectionStatus.OK:
            self.mapping_error_var.set("Cannot capture: mapping is not confirmed OK.")
            return
        self._on_capture_test_cb(self._account_id, self._mapped_serial)

    def refresh(self, status: AccountWorkerStatus) -> None:
        for control in (self.capture_button, self.save_button, self.clear_button):
            control.state(["disabled"] if status.running else ["!disabled"])
        self.window_combo.configure(state="disabled" if status.running else "readonly")
        self.status_var.set("running" if status.running else ("ERROR" if status.errored else "stopped"))
        self.slot_var.set(f"slot: {status.current_slot if status.current_slot is not None else '-'}")
        self.progress_var.set(f"cycles: {status.cycles_completed} last: {status.last_outcome or '-'}")
        self.error_var.set(status.last_error or "")
        self.log_var.set(status.recent_log[-1] if status.recent_log else "")
        self.phase_var.set(
            f"phase: {status.phase}  locked: {status.locked_slots}/5  "
            f"slots: {'/'.join(status.slot_states) or '-'}"
        )

    def set_discovered_serials(self, serials: list[str]) -> None:
        self.serial_combo["values"] = serials

    def set_mapping_status(
        self, serial: Optional[str], status: Optional[ConnectionStatus], detail: str
    ) -> None:
        """Reflect the persisted serial + live cross-check status.

        Gates the Start button: only :attr:`ConnectionStatus.OK` enables
        it — everything else (unmapped, not found, offline, unauthorized,
        unknown state, discovery unavailable, or not-yet-refreshed)
        leaves it disabled, so an account can never be started on an
        unverified mapping.
        """

        if self._mapped_serial != (serial or "") or status is not ConnectionStatus.OK:
            self._capture_ready = False
        self._mapped_serial = serial or ""
        self.serial_var.set(serial or "")
        status_label = status.value if status is not None else "unknown"
        self.mapping_status_var.set(f"mapping: {serial or '(unmapped)'}  [{status_label}]  {detail}")
        self._connection_status = status
        if status is ConnectionStatus.OK and self._capture_ready:
            self.start_button.state(["!disabled"])
        else:
            self.start_button.state(["disabled"])

    def set_capture_ready(self, ready: bool) -> None:
        self._capture_ready = ready
        if ready and self._connection_status is ConnectionStatus.OK:
            self.start_button.state(["!disabled"])
        elif not ready:
            self.start_button.state(["disabled"])

    def show_save_result(self, ok: bool, message: str) -> None:
        self.mapping_error_var.set("" if ok else message)


class LDManagerApp(tk.Tk):
    """Root window: global controls + one :class:`AccountPanel` per account."""

    def __init__(
        self,
        controller: AccountController,
        *,
        adb_runner: Optional[AdbRunner] = None,
        config_path: Optional[Path] = None,
        refresh_interval_ms: int = DEFAULT_REFRESH_INTERVAL_MS,
        auto_refresh: bool = True,
        readiness_check=None,
        serial_registry=None,
        window_capture_router=None,
        memory_monitor=None,
    ) -> None:
        super().__init__()
        self.title("ldmanager v1.0.3-rc.34 - Windows capture / memory TEST")
        self._controller = controller
        self._adb_runner = adb_runner
        self._config_path = config_path
        self._refresh_interval_ms = refresh_interval_ms
        self._panels: dict[AccountId, AccountPanel] = {}
        self._discovered_devices: list = []
        self._has_refreshed_once = False
        self._readiness_check = readiness_check
        # LIVE-SERIAL-001: duck-typed (needs only .set(account_id, serial))
        # so tests can inject a minimal fake without importing
        # ldmanager.app.LiveSerialRegistry. None (e.g. an older/minimal
        # caller) is a safe no-op -- see _on_save_mapping/_on_clear_mapping.
        self._serial_registry = serial_registry
        # Optional HybridCaptureAdbRunner.  It remains optional so the GUI
        # is still usable with lightweight test runners and older callers.
        self._window_capture_router = window_capture_router
        self._memory_monitor = memory_monitor

        self.global_error_var = tk.StringVar(value="")
        try:
            self._current_mapping = load_current_adb_mapping(config_path)
        except ConfigError as exc:
            self._current_mapping = {account_id.value: None for account_id in AccountId}
            self.global_error_var.set(f"Config error: {exc}")
        self._configured_adb_path: Optional[str] = load_current_adb_path(config_path)

        global_row = ttk.Frame(self)
        global_row.pack(fill="x", padx=8, pady=8)
        ttk.Button(global_row, text="Start All", command=self._on_start_all).pack(side="left")
        ttk.Button(global_row, text="Stop All", command=self._on_stop_all).pack(side="left")
        ttk.Button(global_row, text="Refresh ADB devices", command=self._on_refresh_devices).pack(
            side="left", padx=(12, 0)
        )
        ttk.Button(global_row, text="Refresh LD windows", command=self._on_refresh_windows).pack(side="left", padx=8)
        if os.environ.get("LDMANAGER_DEVELOPER_MODE") == "1":
            ttk.Button(global_row, text="Template calibration", command=self._open_calibration).pack(
                side="left", padx=(12, 0)
            )
        ttk.Label(global_row, textvariable=self.global_error_var, foreground="red").pack(
            side="left", padx=(12, 0)
        )

        # ADB-PATH-001: configured/effective ADB executable path + Browse/Save/Clear.
        adb_path_row = ttk.Frame(self)
        adb_path_row.pack(fill="x", padx=8, pady=(0, 4))
        ttk.Label(adb_path_row, text="ADB executable:").pack(side="left")
        self.adb_path_var = tk.StringVar(value=self._configured_adb_path or "")
        self.adb_path_entry = ttk.Entry(adb_path_row, textvariable=self.adb_path_var, width=50)
        self.adb_path_entry.pack(side="left", padx=(4, 4))
        ttk.Button(adb_path_row, text="Browse...", command=self._on_browse_adb_path).pack(side="left")
        ttk.Button(adb_path_row, text="Save", command=self._on_save_adb_path).pack(side="left")
        ttk.Button(adb_path_row, text="Clear", command=self._on_clear_adb_path).pack(side="left")

        self.adb_path_status_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.adb_path_status_var).pack(anchor="w", padx=8)
        self.adb_path_error_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.adb_path_error_var, foreground="red").pack(anchor="w", padx=8)
        self._update_adb_path_status()
        self.diagnostic_var = tk.StringVar(value="TEST: Windows capture only. Failure pauses that LD; no ADB screenshot fallback.")
        ttk.Label(self, textvariable=self.diagnostic_var, wraplength=1100).pack(anchor="w", padx=8)
        if memory_monitor is not None:
            ttk.Label(self, text=f"Memory/call logs (every 30s): {memory_monitor.directory}").pack(anchor="w", padx=8)

        grid = ttk.Frame(self)
        grid.pack(fill="both", expand=True, padx=8, pady=8)
        for index, account_id in enumerate(AccountId):
            panel = AccountPanel(
                grid, controller, account_id,
                on_save_mapping=self._on_save_mapping,
                on_clear_mapping=self._on_clear_mapping,
                on_capture_test=self._on_capture_test,
            )
            panel.grid(row=index // 3, column=index % 3, padx=4, pady=4, sticky="nsew")
            self._panels[account_id] = panel

        self._apply_current_mapping_to_panels()

        if auto_refresh:
            self.after(0, self._refresh)

    def _on_start_all(self) -> None:
        for panel in self._panels.values():
            if panel._connection_status is ConnectionStatus.OK and panel._capture_ready:
                panel._on_start()

    def _on_stop_all(self) -> None:
        self._controller.stop_all()

    def _on_refresh_windows(self):
        try:
            targets = list_ld_windows()
            for panel in self._panels.values():
                panel.set_window_targets(targets)
            if not targets:
                self.global_error_var.set("No LDPlayer windows found. Open an LD window, then Refresh LD windows.")
            else:
                self.global_error_var.set("")
        except Exception as exc:
            self.global_error_var.set(f"Cannot list LD windows: {exc}")

    # --- ADB-PATH-001: configured/effective ADB executable path ---------

    def _update_adb_path_status(self) -> None:
        effective = resolve_adb_path(self._configured_adb_path)
        exists = Path(effective).is_file()
        configured_display = self._configured_adb_path or "(auto-detect)"
        found_display = "found" if exists else "NOT FOUND"
        self.adb_path_status_var.set(
            f"configured: {configured_display}   effective: {effective}   [{found_display}]"
        )

    def _on_browse_adb_path(self) -> None:
        """Opens a native file picker; never touches ADB, never writes
        anything by itself -- only fills the Entry, Save still required."""

        selected = filedialog.askopenfilename(
            title="Select adb executable",
            filetypes=[("adb executable", "*.exe"), ("All files", "*.*")],
        )
        if selected:
            self.adb_path_var.set(selected)

    def _on_save_adb_path(self) -> None:
        """Persists the typed/picked ADB path -- fail-closed: rejected
        visibly (nothing written) unless the file actually exists.
        On success, updates the live runner in place (no restart) and
        re-runs discovery immediately so the effect is visible right
        away; that re-run is still read-only (list_devices only)."""

        if any(self._controller.worker(aid).is_running for aid in AccountId):
            self.adb_path_error_var.set("Stop all LD accounts before changing the ADB executable.")
            return
        typed = self.adb_path_var.get().strip()
        result = save_adb_path(typed or None, self._config_path)
        if not result.ok:
            self.adb_path_error_var.set(result.detail)
            return
        self.adb_path_error_var.set("")
        self._configured_adb_path = result.adb_path
        self.adb_path_var.set(result.adb_path or "")
        if self._adb_runner is not None:
            self._adb_runner.set_adb_path(result.adb_path)
        self._update_adb_path_status()
        self._on_refresh_devices()

    def _on_clear_adb_path(self) -> None:
        """Clears back to auto-detect. Always succeeds (never deletes
        any file -- only ever writes the YAML value to null) and
        re-initializes the live runner + discovery the same way Save does."""

        if any(self._controller.worker(aid).is_running for aid in AccountId):
            self.adb_path_error_var.set("Stop all LD accounts before changing the ADB executable.")
            return
        result = save_adb_path(None, self._config_path)
        if not result.ok:
            self.adb_path_error_var.set(result.detail)
            return
        self.adb_path_error_var.set("")
        self._configured_adb_path = None
        self.adb_path_var.set("")
        if self._adb_runner is not None:
            self._adb_runner.set_adb_path(None)
        self._update_adb_path_status()
        self._on_refresh_devices()

    def _confirm_window_pair(self, account_id, serial, target, adb_png, window_png):
        """A picture match cannot identify two accounts with identical UI."""
        import base64
        dialog = tk.Toplevel(self)
        dialog.title(f"{account_id.value}: confirm ADB / Windows pair")
        accepted = [False]
        ttk.Label(dialog, text=f"{account_id.value} / ADB {serial}\nWindow: {target.display}\n"
                  "Confirm BOTH images belong to the SAME LD instance.\n"
                  "같은 LD 계정의 화면이 맞는지 확인하세요.").pack(padx=12, pady=8)
        row = ttk.Frame(dialog)
        row.pack()
        images = []
        for title, png in (("ADB reference (one-time probe)", adb_png), ("Windows game area", window_png)):
            column = ttk.Frame(row)
            column.pack(side="left", padx=4)
            ttk.Label(column, text=title).pack()
            photo = tk.PhotoImage(data=base64.b64encode(png)).subsample(3)
            images.append(photo)
            ttk.Label(column, image=photo).pack()
        def approve():
            accepted[0] = True
            dialog.destroy()
        ttk.Button(dialog, text="Same LD - enable Windows capture", command=approve).pack(pady=8)
        ttk.Button(dialog, text="Cancel / different LD", command=dialog.destroy).pack(pady=4)
        dialog.transient(self)
        dialog.grab_set()
        self.wait_window(dialog)
        return accepted[0]

    def _on_capture_test(self, account_id: AccountId, serial: str) -> None:
        panel = self._panels[account_id]
        if self._controller.worker(account_id).is_running:
            panel.mapping_error_var.set("Stop this LD before Test capture.")
            return
        panel.set_capture_ready(False)
        router = self._window_capture_router
        if router is not None:
            router.unregister_window(serial)
        if self._adb_runner is None:
            panel.mapping_error_var.set("No ADB runner configured; cannot capture.")
            return
        provider = None
        try:
            if router is not None:
                target = panel.selected_window()
                if target is None:
                    raise WindowCaptureError("Select the exact LD window using Refresh LD windows first.")
                # Bypass runtime routing explicitly: every test uses real ADB.
                # This is the only screenshot exception to Windows-only mode.
                from types import SimpleNamespace
                probe_runner = SimpleNamespace(capture_binary=router.preflight_capture_binary)
            else:
                probe_runner = self._adb_runner
            result = capture_screenshot(probe_runner, serial)
            if not result.ok:
                raise WindowCaptureError(result.detail)
            output_dir = Path("diagnostics") / "captures" / account_id.value
            output_dir.mkdir(parents=True, exist_ok=True)
            stamp = time.time_ns()
            output_path = output_dir / f"adb-capture-{stamp}.png"
            output_path.write_bytes(result.image_bytes)
            if self._readiness_check is None:
                panel.mapping_error_var.set(f"Capture saved (not verified): {output_path}")
                return
            ready, detail = self._readiness_check(result.image_bytes)
            if not ready:
                raise WindowCaptureError(f"{detail} ADB: {output_path}")
            if router is None:
                panel.set_capture_ready(True)
                panel.mapping_error_var.set(f"{detail} Capture: {output_path}")
                return
            provider = WindowsGraphicsCaptureProvider(target)
            window_png = provider.capture_native_png()
            # Preserve failed comparisons too; support needs the actual raw frame.
            window_path = output_dir / f"window-raw-{stamp}.png"
            window_path.write_bytes(window_png)
            viewport, normalized = align_game_viewport(result.image_bytes, window_png)
            normalized_path = output_dir / f"window-game-{stamp}.png"
            normalized_path.write_bytes(normalized)
            window_ready, window_detail = self._readiness_check(normalized)
            if not window_ready:
                raise WindowCaptureError(f"Windows screen check failed: {window_detail}; {window_path}")
            if not self._confirm_window_pair(account_id, serial, target, result.image_bytes, normalized):
                raise WindowCaptureError("Window/ADB pair not confirmed. Start remains blocked.")
            provider.viewport = viewport
            # Re-check after the user spent time looking at the comparison.
            final_ready, final_detail = self._readiness_check(provider.capture_png())
            if not final_ready:
                raise WindowCaptureError(f"Screen changed during confirmation: {final_detail}")
            router.register_verified_window(serial, provider)
            provider = None  # ownership transferred to router
            panel.set_capture_ready(True)
            panel.mapping_error_var.set(
                f"Windows capture verified (Windows ONLY; similarity {viewport.score:.3f}). "
                f"Runtime ADB screenshots: 0. Captures: {output_dir}")
        except Exception as exc:
            panel.set_capture_ready(False)
            panel.mapping_error_var.set(f"Capture verification failed: {exc} (Start blocked; no ADB fallback.)")
        finally:
            if provider is not None:
                provider.close()

    def _open_calibration(self) -> None:
        """Open a small real-PNG crop tool. Captures are first made with each
        panel's Test capture button, then their pixel crop becomes a template."""
        window = tk.Toplevel(self)
        window.title("Template calibration")
        values = {name: tk.StringVar() for name in ("source", "slot", "output", "x", "y", "width", "height")}
        values["slot"].set(TEMPLATE_SLOTS[0])
        values["output"].set(f"{TEMPLATE_SLOTS[0]}.png")
        for row, key in enumerate(("source", "slot", "output", "x", "y", "width", "height")):
            ttk.Label(window, text=key).grid(row=row, column=0, sticky="w", padx=6, pady=3)
            if key == "slot":
                widget = ttk.Combobox(window, textvariable=values[key], values=TEMPLATE_SLOTS)
            else:
                widget = ttk.Entry(window, textvariable=values[key], width=48)
            widget.grid(row=row, column=1, sticky="we", padx=6, pady=3)
        result = tk.StringVar(value="Use a saved Test capture PNG; coordinates are pixels in that image.")
        ttk.Label(window, textvariable=result, foreground="gray30").grid(row=8, column=0, columnspan=2, sticky="w", padx=6)

        def save_crop() -> None:
            try:
                source = Path(values["source"].get())
                output = Path("templates") / values["output"].get()
                crop_template(source, output, *(int(values[k].get()) for k in ("x", "y", "width", "height")))
            except Exception as exc:
                result.set(f"Template not saved: {exc}")
            else:
                result.set(f"Saved {output}; map this filename in bounty.yaml template_map.")

        ttk.Button(window, text="Crop and save template", command=save_crop).grid(row=9, column=0, columnspan=2, pady=6)
        window.columnconfigure(1, weight=1)

    def _apply_current_mapping_to_panels(self) -> None:
        statuses = compute_account_connection_statuses(self._current_mapping, self._discovered_devices)
        discovered_serials = sorted({device.serial for device in self._discovered_devices})
        for status in statuses:
            panel = self._panels[status.account_id]
            panel.set_discovered_serials(discovered_serials)
            detail = status.detail
            if not self._has_refreshed_once and status.status is ConnectionStatus.DEVICE_NOT_FOUND:
                detail = _NOT_YET_REFRESHED_DETAIL
            panel.set_mapping_status(
                self._current_mapping.get(status.account_id.value), status.status, detail
            )

    def _on_refresh_devices(self) -> None:
        """Reads `adb devices` (via the injected runner) and re-checks
        every account's mapping against it. Issues no tap, starts no
        worker — read-only device discovery only."""

        if self._adb_runner is None:
            self.global_error_var.set("No ADB runner configured; cannot refresh.")
            return

        devices, error = discover_devices(self._adb_runner)
        self._discovered_devices = devices
        self._has_refreshed_once = True
        self.global_error_var.set(f"Device discovery failed: {error}" if error else "")
        self._apply_current_mapping_to_panels()

    def _on_save_mapping(self, account_id: AccountId, serial_text: str) -> None:
        """Persists exactly one account's typed/picked serial. Never
        touches ADB, never starts a worker, never auto-assigns a
        discovered device -- ``serial_text`` is always whatever the
        user put in that account's combobox."""

        if self._controller.worker(account_id).is_running:
            self._panels[account_id].mapping_error_var.set("Stop this LD before changing its mapping.")
            return
        result = save_account_serial(account_id, serial_text, self._config_path)
        panel = self._panels[account_id]
        panel.show_save_result(result.ok, result.detail)
        if result.ok:
            old_serial = self._current_mapping.get(account_id.value)
            if old_serial and old_serial != result.adb_mapping.get(account_id.value) and self._window_capture_router is not None:
                self._window_capture_router.unregister_window(old_serial)
            panel.set_capture_ready(False)
            self._current_mapping = result.adb_mapping
            # LIVE-SERIAL-001: propagate to an already-built (possibly
            # already-running) worker's next cycle -- fixes the real
            # customer crash where a worker kept using the blank serial
            # it was built with, never learning about this Save. Scoped
            # to this one account_id only; every other account's live
            # serial is untouched.
            if self._serial_registry is not None:
                self._serial_registry.set(account_id, result.adb_mapping.get(account_id.value))
        self._apply_current_mapping_to_panels()

    def _on_clear_mapping(self, account_id: AccountId) -> None:
        """Clears exactly one account's mapping. Never touches ADB,
        never starts a worker, never affects any other account."""

        if self._controller.worker(account_id).is_running:
            self._panels[account_id].mapping_error_var.set("Stop this LD before clearing its mapping.")
            return
        result = save_account_serial(account_id, None, self._config_path)
        panel = self._panels[account_id]
        panel.show_save_result(result.ok, result.detail)
        if result.ok:
            old_serial = self._current_mapping.get(account_id.value)
            if old_serial and self._window_capture_router is not None:
                self._window_capture_router.unregister_window(old_serial)
            panel.set_capture_ready(False)
            self._current_mapping = result.adb_mapping
            # LIVE-SERIAL-001: same live propagation as Save, above --
            # a cleared account's next cycle must see "" immediately,
            # not the previously-saved serial.
            if self._serial_registry is not None:
                self._serial_registry.set(account_id, None)
        self._apply_current_mapping_to_panels()

    def _refresh(self) -> None:
        statuses = self._controller.all_statuses()
        for account_id, panel in self._panels.items():
            status = statuses.get(account_id)
            if status is not None:
                panel.refresh(status)
            if self._window_capture_router is not None:
                serial = self._current_mapping.get(account_id.value)
                if not serial or not self._window_capture_router.is_verified(serial):
                    panel.set_capture_ready(False)
        if self._memory_monitor is not None:
            latest = self._memory_monitor.latest
            if self._memory_monitor.error:
                self.diagnostic_var.set(self._memory_monitor.error)
            elif latest:
                commit, limit = latest.get("commit_bytes"), latest.get("commit_limit_bytes")
                memory = f"Commit: {commit / 2**30:.2f}/{limit / 2**30:.2f} GiB" if commit is not None and limit else "Commit unavailable"
                self.diagnostic_var.set(
                    f"Windows ONLY | {memory} | ADB probes: {latest['adb_preflight_captures']} | "
                    f"Runtime ADB captures: {latest['adb_runtime_captures']} | "
                    f"Windows frames: {latest['window_capture_calls']} | Taps: {latest['adb_tap_calls']}")
        self.after(self._refresh_interval_ms, self._refresh)

    def run(self) -> None:
        """Start the Tk event loop (blocks). Not called by construction
        or by any test — only the real entry point calls this."""

        self.mainloop()
