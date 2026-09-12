# Real-Capture Checklist (MVP-001 → real gameplay)

MVP-001 is a **safe, configurable mock/foundation**: it never performs
real recognition and never fabricates a success. This checklist is
everything that still needs to happen — in order — before this project
could safely drive an actual game.

Nothing on this list is done in MVP-001. Treat every unchecked item as
a hard prerequisite, not a nice-to-have.

## 1. Real ADB connectivity

- [ ] Install a real `adb` executable and put it on `PATH` (or point
      `SubprocessAdbRunner(adb_path=...)` at it).
- [ ] Start your 9 LDPlayer instances and run `adb devices` yourself to
      confirm each shows state `device` (not `offline`/`unauthorized`).
- [ ] Fill in `configs/config.yaml`'s `adb_mapping` with the 9 real,
      distinct `host:port` serials — never guess/reuse a port.
- [ ] Run the discovery/mapping validation from TP-002
      (`ldmanager.discovery.ensure_complete_adb_mapping` +
      `build_account_connection_statuses`) against your real mapping and
      confirm every account reports `ok`.

## 2. Real screen geometry

- [ ] For each instance, run `adb -s <serial> shell wm size` and record
      the actual resolution.
- [ ] Update `configs/mission.yaml`'s `screen_size` to match (all 9
      instances should normally share one resolution if configured
      identically in LDPlayer — verify this assumption for your setup).
- [ ] Capture a handful of real screenshots via
      `ldmanager.screenshot.capture_screenshot()` (or manually via
      `adb exec-out screencap -p > frame.png`) and open them to confirm
      they look correct (not corrupted, not black/blank).

## 3. Real ROI calibration

- [ ] Using real captured frames, measure the actual pixel bounding box
      of each of the 5 slot regions, the kill-check indicator, the
      claim button, the "claimed" confirmation area, the reset button,
      and the "ready for next cycle" indicator.
- [ ] Convert each pixel box to a fraction of the real screen size
      (`x/width`, `y/height`) and replace the placeholder values in
      `configs/mission.yaml`. Every value there right now is an
      illustrative example, not a measurement.
- [ ] Re-validate with `ldmanager.coordinates.RelativeRegion`/
      `RelativeCoordinate` (already strict — invalid values will raise).

## 4. A real recognizer

- [ ] `ldmanager.recognition.PlaceholderRecognizer` must be replaced
      (or subclassed) with something that actually reads pixels — e.g.
      OCR (Tesseract via `pytesseract`) for the target phrase, and/or
      template/image matching (OpenCV `matchTemplate`, or similar) for
      the kill-check/claimed/ready indicators.
- [ ] The real recognizer must still satisfy the existing
      `Recognizer` protocol (`recognize(image_bytes, roi, expected_label,
      threshold) -> RecognitionResult`) so `mission.py` doesn't need to
      change.
- [ ] It must never fabricate a match — on any ambiguity, camera noise,
      or unexpected screen state, it must return `NO_MATCH`/`UNKNOWN`/
      `LOW_CONFIDENCE`, not `MATCH`.
- [ ] Add real dependencies properly (`pyproject.toml` — a new optional
      extra, e.g. `recognition = ["pytesseract>=...", "opencv-python>=..."]`),
      pinned, and document any external binary they require (e.g. the
      Tesseract executable itself is not a Python package).

## 5. Real template/reference assets

- [ ] Populate `templates/` with whatever the real recognizer actually
      needs (reference crops, trained data, etc.) — nothing is there
      today.
- [ ] Confirm these assets don't themselves encode anything sensitive
      (they shouldn't — screenshots of UI text/buttons, not credentials).

## 6. Threshold/retry/timeout tuning against real timing

- [ ] With a real recognizer wired in, tune `threshold` so it neither
      false-matches noise nor false-rejects a real match.
- [ ] Tune `max_reroll_attempts`/`max_kill_check_attempts`/
      `max_claim_verify_attempts`/`max_reset_verify_attempts`/
      `retry_delay_seconds` against how long the real game actually
      takes to respond to a reroll/claim/reset tap.

## 7. Supervised trial run

- [ ] Run against exactly **one** real account first, supervised, with
      the GUI open, before enabling more.
- [ ] Watch the per-account log (`logs/<LDx>/task.log` /
      `logs/<LDx>/error.log`) and GUI status live during the trial.
- [ ] Confirm Stop (individual and global) actually halts input
      immediately when you click it during a real run.

## 8. Operational readiness

- [ ] Confirm log rotation/retention (`logging.max_bytes`/
      `backup_count`/`retention_days`) is reasonable for real, continuous
      run volume.
- [ ] Decide on and implement a real screenshot-retention policy if
      diagnostic captures are added later (MVP-001 only plans
      paths/metadata for diagnostics — see `diagnostics.py`; no capture
      call is wired to it yet).
- [ ] Re-run the full automated test suite (`pytest`) after any of the
      above changes, and re-review `docs/HANDOFF_CODE.md`'s limitations
      list for anything still open.

None of the above is implemented or verified by MVP-001. Do not enable
this against a real account/game until every relevant item here is
actually checked off by a human who watched it happen.
