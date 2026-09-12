# Run Guide (MVP-001)

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

1. Copy `configs/config.example.yaml` → `configs/config.yaml`.
   Fill in `adb_mapping` with your 9 LD1..LD9 ADB serials (or leave
   entries `null` — an account with no serial simply shows an error in
   the GUI instead of running, it never guesses one).
2. Copy `configs/mission.example.yaml` → `configs/mission.yaml`.
   The shipped values are **placeholder examples** — see
   `docs/REAL_CAPTURE_CHECKLIST.md` before expecting them to mean
   anything against a real screen.
3. Both `configs/config.yaml` and `configs/mission.yaml` are
   git-ignored — they're never committed.

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
All**/**Stop All** at the top. Each panel has its own **Start**/**Stop**
and shows: running/stopped, current slot, cycle count + last outcome,
last error, and the most recent log line.

If `configs/config.yaml` or `configs/mission.yaml` is missing/invalid,
the app prints a clear error to the console and exits (code 1) instead
of opening a broken window.

## 4. What clicking Start actually does right now

It starts a background worker for that account that repeatedly:

1. Captures a screenshot from that account's ADB serial only.
2. Tries to recognize a target phrase in each of 5 slots (rerolling,
   bounded, if missing).
3. Polls (bounded) for a "200 kills" indicator.
4. Taps "claim" once, verifies it (bounded), taps "reset" once,
   verifies it (bounded).
5. Repeats.

Because recognition is a placeholder that always reports "unknown"
(see `docs/MVP_UNVERIFIED.md`), against a real screen this will reroll
until it hits its bounded retry limit and stop with a
`slot_recognition_failed` status — safely, with no runaway input. That
is expected until a real recognizer is wired in.

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
