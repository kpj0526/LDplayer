# Run Guide (MVP-001-CV + UI-ADB-001)

Short, practical steps to run the MVP app. For what still needs to
happen before this does anything with a *real* game, see
`docs/REAL_CAPTURE_CHECKLIST.md`. For everything this MVP intentionally
does not do, see `docs/MVP_UNVERIFIED.md`.

## 1. Install

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -e ".[dev]"
```

## 2. Configure

1. Copy `configs/config.example.yaml` → `configs/config.yaml`. You do
   **not** need to hand-fill `adb_mapping` in this file yourself as of
   UI-ADB-001 — leave it as-is (all `null`) and register LD1..LD9 from
   the GUI instead (see step 3.1 below). Editing it by hand still works
   if you prefer (see §2a).
2. Copy `configs/bounty.example.yaml` → `configs/bounty.yaml`. This is
   the file the real app actually reads (`configs/mission.example.yaml`
   / `configs/mission.yaml` belong to the earlier, simpler `mission.py`
   flow, which is kept/tested but no longer wired into `app.py`). The
   shipped values are **placeholder examples** — see
   `docs/REAL_CAPTURE_CHECKLIST.md` before expecting them to mean
   anything against a real screen. In particular, the refresh-popup
   fields are meant to be verified *structurally* (two fixed UI
   landmarks), never by the displayed (variable) refresh cost.
3. `configs/config.yaml` and `configs/bounty.yaml` (and
   `configs/mission.yaml`, if you use it) are all git-ignored — never
   committed.

### 2a. (Advanced/optional) Editing `adb_mapping` by hand instead

If you prefer not to use the GUI for this: fill in `adb_mapping` in
`configs/config.yaml` with your 9 LD1..LD9 ADB serials directly (or
leave entries `null` — an account with no serial simply shows an error
instead of running; nothing is ever guessed). The GUI flow in step 3.1
and this manual edit both end up writing/reading the exact same file
and section — use whichever you like, per account, at any time.

## 3. Run

From the repo root:

```bash
# Windows (double-click, or from a shell)
scripts\run.bat
# or
powershell -ExecutionPolicy Bypass -File scripts\run.ps1

# equivalent, any platform, inside the venv
python -m ldmanager.app
```

A window opens with one panel per account (LD1..LD9) plus **Start
All**/**Stop All**/**Refresh ADB devices** at the top. Each panel has
its own **Start**/**Stop** and shows: running/stopped, current slot,
cycle count + last outcome, last error, and the most recent log line —
plus (UI-ADB-001) an ADB-serial combobox with **Save**/**Clear** and a
live mapping-status line.

If `configs/config.yaml` or `configs/bounty.yaml` is missing/invalid,
the app prints a clear error to the console and exits (code 1) instead
of opening a broken window.

### 3.1. Register LD1..LD9 from the GUI (no YAML/terminal editing needed)

1. Start your LDPlayer instances, then click **Refresh ADB devices** at
   the top of the window. This runs `adb devices` (read-only — no tap,
   no worker started) and populates every panel's serial dropdown with
   what it found.
2. On each panel: either **pick** a discovered serial from the dropdown
   or **type** one explicitly (e.g. if the instance isn't running yet),
   then click **Save**. Nothing is ever auto-assigned — you always
   choose or type the exact value that gets saved.
3. Save persists immediately to `configs/config.yaml` (created if it
   doesn't exist yet) and reloads that panel's state from disk. A
   blank, malformed (contains whitespace), or duplicate (already used
   by another account) serial is rejected with a visible error on that
   panel — nothing is written in that case, and other accounts'
   mappings are never touched.
4. Click **Refresh ADB devices** again after saving to re-confirm the
   device is actually online. **Start stays disabled until the mapping
   cross-checks as OK** against a live refresh — saving a serial alone
   is not enough, and a stale/never-refreshed mapping can never start
   an account.
5. Click **Clear** on a panel to remove that account's mapping (its
   Start button becomes disabled again); every other account's mapping
   is preserved.

Note: comments in a hand-edited `config.yaml` are not preserved after a
GUI Save/Clear (the file is re-serialized) — see
`docs/HANDOFF_CODE.md`'s UI-ADB-001 section for details.

## 4. What clicking Start actually does right now

It starts a background worker for that account that repeatedly runs
the free-regional-bounty five-slot cycle (`bounty_mission.py`):

1. For each of 5 slots: select it, check whether its current mission
   already satisfies both acceptance conditions ('모든 몬스터 처치'
   phrase AND quantity 200). If not: open refresh, verify the
   confirmation popup *structurally* (two fixed landmarks, never the
   displayed cost), confirm, inspect the new mission, and retry
   (bounded) until both conditions match or the bound is hit.
2. After all 5 slots: poll (bounded) for kill-progress completion
   (`200/200` or an explicit complete badge). **0-199/200 never taps
   complete/reward.**
3. Only once eligible: select the mission, tap complete, verify the
   reward screen, claim, verify the result screen, close it, verify
   the mission list is showing again.
4. Re-refresh + re-accept each slot, ready to repeat.

Because recognition is a placeholder that always reports "unknown"
(see `docs/MVP_UNVERIFIED.md`), against a real screen this will reroll
until it hits its bounded retry limit and stop with a
`slot_accept_failed` status (or, if the popup itself can never be
structurally verified, `refresh_popup_not_verified`) — safely, with no
runaway input. That is expected until a real recognizer is wired in.

## 5. Stop

Click **Stop** on a panel (that account only) or **Stop All** (every
account). A stop request is checked before every capture and every
touch, so no further ADB command is issued for that account once
requested.

## 6. Logs

Per-account logs live under `logs/<LDx>/task.log` (info) and
`logs/<LDx>/error.log` (errors/exceptions), rotated/retained per
`configs/config.yaml`'s `logging` section. `logs/` is git-ignored.

## 7. Tests

```bash
pytest
```

## 8. Build a Windows executable (optional)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

Produces `dist\ldmanager\ldmanager.exe`. See `docs/HANDOFF_CODE.md` for
whether this was actually run/verified in the delivering session.
