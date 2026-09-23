# Changelog

## v1.0.3-rc.36 — completed target before refresh

- Recognize an already-completed target mission before the initial `0/200` acceptance check can route it into renewal.
- Keep the existing target and completed-state guards before reward input. A completed non-target mission stops without refresh or claim input.
- Add a real-capture regression using the 595x334 Windows game viewport. Customer LDPlayer verification remains `NEEDS_REAL_TEST`.

## v1.0.3-rc.35 — Windows capture viewport edge correction

- Fix `Game viewport is outside the captured window` when the game image reaches the right or bottom edge of an LDPlayer window capture.
- Convert matched rectangle edges to native pixels separately and keep the crop inside the captured frame. This shared alignment path applies to LD1–LD9.
- Add right-edge and bottom-edge regression coverage. Customer LDPlayer verification and memory improvement remain `NEEDS_REAL_TEST`.

## v1.0.3-rc.34 — Windows capture / memory diagnostic TEST

- Separate prerelease; rc.33 release/tag/ZIP are retained unchanged.
- Windows-only runtime capture. Missing, failed, stale, closed or resized capture pauses that account, latches an error and blocks further input until a new preflight. No automatic ADB screenshot fallback.
- Explicit HWND/PID window selection, game-viewport alignment against a one-time ADB reference, and side-by-side user confirmation before enabling Start. Start All obeys each account's preflight.
- Wait for a newly delivered frame on every capture, including a post-input settle barrier. Retain one raw frame and encode PNG only on demand.
- Record system commit/limit, kernel pools, per-process private bytes, per-account capture state and cumulative ADB/capture/tap counters every 30 seconds, including idle baseline time.
- Prefer the calibrated mission phrase over the legacy active-target crop, fixing a non-target false match exposed by running the real-image OpenCV regression suite.
- Isolated, fail-fast Windows packaging; includes a no-ADB packaged dependency/memory self-test.
- LDPlayer/GPU compatibility and memory improvement still require measurement on the customer PC.

## v1.0.3-rc.33

- Add a verified Windows Graphics Capture path for each LDPlayer window. A window frame is used only after it independently passes the same mission-screen validation as the ADB frame; any window-capture error safely falls back to that account's ADB capture.
- Keep one persistent, serial-scoped ADB shell per account for `input tap` commands, while discovery and screenshots keep the existing subprocess path.
- Enable a customer Start by default after its per-account mapping and Test-capture preflight succeed. Set `LDMANAGER_LIVE_MODE=0` only for diagnostic no-input mode.
- Revoke that account's Start readiness immediately when its latest Test capture fails, preventing a stale successful preflight from authorizing a later run.
- Require the exact `0/200` target template while accepting a new mission; use the active-target template only after acceptance as its progress changes.

## v1.0.3-rc.32

- Reduce long-running kill-progress polling: rotate one locked slot per account instead of touring all five rows on every pass.
- Reuse one ADB screenshot to check both `200/200` and the Complete button.
- Poll the next locked slot every second (maximum five-second revisit for one row), reducing waiting-path ADB process creation while keeping completion response responsive.

## v1.0.3-rc.31

- After a completed mission's reward/result close, reconfigure the replacement mission in that same row first; refresh non-target replacements before moving to lower rows.

## v1.0.3-rc.30

- Use a responsive timing profile: 0.2s normal UI settle, 0.3s initial result-close settle, and 0.4s only between bounded retries.

## v1.0.3-rc.29

- Preserve each account's next slot cursor after a verified result close, resuming at the row below the completed slot and wrapping only after row five.

## v1.0.3-rc.28

- Lower the shipped bounty UI transition pace from 1.5 seconds to 0.5 seconds while preserving bounded retries and structural verification.

## v1.0.3-rc.27

- Fix dungeon/plain-detail refresh: if the popup-only refresh point does not produce the confirmed dialog, tap only a confidently detected visible currency-action button and then re-verify the dialog.

## v1.0.3-rc.26

- Fix the result-close timing race: wait for the popup to become interactive, then retry the measured close touch only while the result popup remains visible.
- Require a fresh mission-list return check after every close attempt; include the close-attempt count in a failure diagnostic.

## v1.0.3-rc.25

- Fix the pre-confirm acknowledgement/odds overlay shown after a refresh-open tap.
- Verify that the overlay has cleared and that the refresh-confirm dialog is structurally present before sending confirm.
- Fail closed per account with `ack_popup_dismiss_failed` if that bounded transition never completes.

## v1.0.1

- Customer capture preflight gates Start per account and keeps calibration developer-only.

## v1.0.0

- LD1~LD9 independent ADB worker management and GUI mapping controls.
- OpenCV template matching with ADB-screen capture and image-center taps.
- Customer-provided target, mission, reward, and variable refresh-button templates.
- Per-account runtime slot state, error isolation, diagnostic capture helpers, and calibration tools.
- Windows PyInstaller distribution including OpenCV runtime and default configuration/templates.

## Customer PC validation still required

- Actual ADB serial mapping, screen calibration, live game transitions, completion timing, and long-running nine-account stability.
