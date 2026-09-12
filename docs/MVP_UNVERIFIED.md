# MVP-001 / MVP-001-CV: Unimplemented / Unverified List

Plain inventory of what this MVP does **not** do and has **not**
verified, kept separate from `docs/HANDOFF_CODE.md`'s narrative so it's
easy to scan. Nothing here is a secret gap — every item is either by
explicit design (safety) or an acknowledged scope cut for this MVP.

## MVP-001-CV specific

- **No real structural popup verification has ever run against a real
  popup.** `refresh_popup_anchor_*`/`refresh_popup_title_*` are
  placeholder ROI/label pairs; whether two independent, cost-
  independent landmarks are actually enough to reliably distinguish
  "popup open" from "popup closed" in the real game has not been
  checked.
- **No real dual-condition acceptance check has been run.** The rule
  "both phrase AND quantity must match" is implemented and unit-tested
  with fakes, but never against real OCR/template-matching output —
  real-world false-positive/false-negative rates for each condition are
  unknown.
- **Kill-progress vs. explicit-complete-badge priority is untested
  against a real game.** The state machine accepts either signal as
  sufficient; which one (or both) actually appears, and in what order,
  in the real UI is unverified.
- **The reward → claim → result → close → mission-list sequence has
  never been observed against a real game.** Screen names/order/timing
  are modeled from the customer-video description, not measured.
- **`mission.py`/`mission_config.py` (the earlier, simpler flow) are no
  longer wired into `app.py`.** They remain in the codebase, fully
  tested, but a user pointing only at `configs/mission.yaml` (not
  `configs/bounty.yaml`) will get a "file not found" error from the
  real app — this is intentional, not a bug, but worth knowing.

## Not implemented (by design — safety)

- **No real recognition.** `PlaceholderRecognizer` always returns
  `UNKNOWN`, confidence `0.0`. No OCR library, no template-matching
  library, no ML model of any kind is wired in.
- **No real game action.** No touch beyond the guarded single-serial
  `input tap` primitive; no swipe/drag/multi-touch/keyboard input.
- **No login/reconnect flow.** Nothing authenticates, re-authenticates,
  or manages a session with the game or LDPlayer.
- **No global desktop mouse or window control.** Every coordinate is a
  device-relative fraction, converted to a pixel only for an
  `adb -s <serial> shell input tap` call.
- **No web/DOM interaction of any kind.**
- **No credential storage or handling anywhere.** Config loading
  actively refuses a file containing a credential-shaped key (see
  `ldmanager.config`).
- **No security bypass, anti-detection, or evasion logic.**

## Not implemented (scope cut for MVP-001)

- **No automatic screen-resolution discovery.** `screen_size` is a
  config value the user must measure and enter
  (`adb shell wm size`) — nothing calls that command automatically.
- **No diagnostic screenshot capture wired to the mission cycle.**
  `ldmanager.diagnostics` (from an earlier stage) plans paths/metadata
  for a future diagnostic screenshot feature, but nothing in the
  mission cycle or GUI currently calls it — captures made during a
  cycle exist only transiently in memory for recognition, not saved.
- **No PNG structural validation beyond the magic header.** IHDR
  parsing, dimension checks, and corruption detection beyond "does it
  start with the PNG magic bytes" are not implemented.
- **No pacing/backoff policy beyond a fixed `retry_delay_seconds` and a
  fixed per-cycle idle delay.** No exponential backoff, no jitter.
- **No persistence of controller/worker status across app restarts.**
  Status lives in memory only; restarting the app resets it.
- **No multi-window/tabbed GUI, no settings editor in the GUI itself.**
  Config is edited by hand in YAML; the GUI only starts/stops/displays.
- **No CLI subcommands for the mission/controller layer.** The
  stage-1 `ldmanager.cli` module is unchanged and unrelated to this
  MVP's controller; there is no `ldmanager start LD1` style CLI yet.

## Not verified

- **No real ADB/LDPlayer integration has been exercised.** Every test
  in this project (211 as of this MVP) uses a fake/injected
  `AdbRunner` and a fake/scripted `Recognizer`. `adb` itself was never
  invoked as a real subprocess during development or testing.
- **The PyInstaller build has not been verified on a machine other than
  this dev environment**, and not verified as a fully offline/portable
  executable (see `docs/HANDOFF_CODE.md` for whether the build script
  itself was run in this session).
- **No load/soak testing.** Nine workers have been exercised briefly in
  unit tests, never for an extended run.
- **No verification that LDPlayer's actual `adb` behavior matches the
  assumptions baked into `parse_adb_devices_output`/`screenshot.py`**
  (e.g., real device state strings, real `exec-out screencap -p` output
  shape on your LDPlayer version).
- **No accessibility/usability review of the GUI.**

## Where to look for more detail

- Per-stage limitations: `docs/HANDOFF_CODE.md` (every prior TP-00x/
  RW-0x/MVP-001 section has its own "한계 (Limitations)" list; none of
  those are superseded by this MVP).
- What to actually do about the "not verified" real-ADB gap:
  `docs/REAL_CAPTURE_CHECKLIST.md`.
