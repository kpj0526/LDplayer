# Changelog

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
