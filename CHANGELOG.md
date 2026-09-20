# Changelog

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
