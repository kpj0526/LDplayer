# ldmanager v1.0.2-rc.1 — ADB path configuration candidate

This is a prerelease for Windows local/customer verification. It is **not** a final project release and is not evidence that the game mission loop has passed real-environment testing.

## Included

- A visible **ADB executable** field in the GUI.
- **Browse**, **Save**, and **Clear** controls for selecting `adb.exe` without manually editing YAML.
- Save validates that the selected path is an existing file, persists it to local configuration, and runs read-only ADB device discovery immediately.
- Invalid paths fail closed and do not overwrite the prior configuration.
- No serial is auto-mapped. No worker, capture, touch, or game input is started by Browse/Save/Clear/Refresh.

## Quick verification

1. In LDPlayer, select **Settings → Other → ADB debugging → Local debugging**, save, and restart the intended LD instance.
2. Start `ldmanager.exe`.
3. In **ADB executable**, choose the installed `adb.exe` (example: `D:\LDPlayer\LDPlayer14\adb.exe`) and click **Save**.
4. Confirm the path status says found and the discovered device list is refreshed.
5. Do not start an account until every intended LD serial is explicitly mapped and each account passes its capture/preflight check.

## Verification status and limits

- Independent automated regression: **319 passed**; fresh packaged GUI launch passed.
- User-operated check: the actual path `D:\LDPlayer\LDPlayer14\adb.exe` was selected and saved successfully.
- The independent QA host did not have that literal LDPlayer install path, so its actual-path result remains `BLOCKED_REAL_ENVIRONMENT`.
- No real ADB device, game capture, mission state, worker execution, or live touch was independently validated for this candidate.
