# STATUS

## GAME-CAL-001 (2026-09-14)

- Status: `PUBLISHED_MVP_PRERELEASE`.
- Customer evidence: valid 1280x720 mapped mission screens fail template preflight; completed LD1/LD3 and both in-progress/currency and completed LD4 captures were supplied.
- QA: `MVP_SMOKE_PASS` at QA `1277b016` over Code `0a0f777`: 345 automated tests, independent injected 1280x720 safety probe, and clean-artifact startup smoke.
- Publication: GitHub prerelease `v1.0.3-rc.1`, Windows ZIP SHA-256 `4764FE903D4C2F7D5F7D4F1904D4E53D6EE0B964BC2D622D050A4C46960DA959`.
- Limit: this does not establish real template calibration, LDPlayer/game flow, or live multi-account proof; those remain `NEEDS_REAL_TEST` / `BLOCKED_REAL_ENVIRONMENT`.

## Corrected v0.1.0 asset (2026-09-12)

- Current phase: `NEEDS_REAL_TEST`
- Published: corrected Windows ZIP replaces the initial unusable asset at the existing `v0.1.0` prerelease.
- QA: `MVP_SMOKE_PASS`, QA `2ff8ebf`; `286 passed`; fresh extracted EXE and bootstrap passed.
- Customer start: extract all files, execute `ldmanager.exe`, assign devices in GUI.
- Not complete: actual LD/game behavior remains unverified.

## GitHub v0.1.0 publication (2026-09-12)

- Current phase: `NEEDS_REAL_TEST`
- Published: `v0.1.0` MVP prerelease on `mvp/v0.1.0`; release page `https://github.com/kpj0526/LDplayer/releases/tag/v0.1.0`.
- QA gate: `MVP_SMOKE_PASS`, report `120a55b`; 266 independent tests plus 53 focused registration tests passed.
- Asset: Windows ZIP 11,210,660 bytes, SHA-256 `A525FA85A50DAB51AE2AAF9E0DCEF805A54C3A631C341E85507F042070059726`.
- Not complete: no actual LDPlayer/game automation result is represented by this prerelease.

## Supplemental GUI launch result (2026-09-12)

- Current phase: `NEEDS_REAL_TEST`
- Verdict: GUI launch PASS only
- Evidence: QA `144a0f7d`; documented `scripts\\run.ps1` opened `ldmanager (MVP)` at 738x600 and exited through standard `WM_CLOSE`.
- Safety result: LD1-LD9 mappings were null; no Worker, ADB command, or game input was started.
- Not complete: this is not a real-game result and does not change any real-environment AC status.

## MVP-001-CV smoke result (2026-09-12)

- Current phase: `NEEDS_REAL_TEST`
- QA verdict: `MVP_SMOKE_PASS`
- Evidence: QA `d8ed7bd`; target Code `c42289c` / implementation `6f32610`; independent `241 passed`, GUI/app subset `8 passed`.
- Not complete: actual customer game templates/ROIs, LD1-LD9 serials, live full cycle/repeat, and 9-instance cross-click proof remain blocked/not tested.

## MVP-001-CV QA smoke handoff (2026-09-12)

- Current phase: `MVP_VERIFYING`
- Owner: `qa`
- Target: Code `c42289c` / implementation `6f32610`
- Code self-test: `241 passed` (not approval)
- Next: QA runs mandatory startup/GUI/config/serial-isolation/lifecycle/video-cycle/error-stop smoke only and returns an MVP verdict, not final project PASS.

## MVP-001-CV customer-video extension (2026-09-12)

- Current phase: `MVP_IMPLEMENTING`
- Owner: `code` after current MVP-001 safe-unit commit
- Scope: five free-bounty slots; cost-independent refresh popup confirmation; target phrase plus 200 quantity; accepted-slot preservation; only-when-complete reward cycle; verified return and repeat.
- Safety: all clicks require screen-state verification and one account's serial only; progress 0-199 may not trigger complete/reward; unknown/low-confidence/stalled screens become account-local error.
- QA: abbreviated MVP smoke expands to mock video flow and mandatory safety; actual customer video/LD validation is `BLOCKED_REAL_ENVIRONMENT` pending supplied assets.

## MVP-001 (2026-09-12)

- Current phase: `MVP_IMPLEMENTING`
- Owner: `code`
- Previous gate: Stage 4 scope PASS, QA `d69bc0b`; Code target `efd3a2f` / implementation `8b1687b`.
- Scope: connected runnable MVP draft with worker lifecycle, mission-state flow, recognition/configuration placeholders, GUI/status/logs, scripts, and mandatory safety tests.
- QA approach after Code commit: MVP smoke only; no final-project PASS claim. Actual LD/game evidence remains `NEEDS_REAL_TEST`.

## TP-003 QA handoff (2026-09-12)

- Current phase: `VERIFYING`
- Owner: `qa`
- Target: Code `efd3a2f` / implementation `8b1687b`
- Code self-test: `159 passed, 0 failed` (not approval)
- Next: QA independently reruns full TP-003 scope. A scope PASS permits automatic transition to the template/ROI configuration stage.

## TP-003 Stage 4 (2026-09-12)

- Current phase: `IMPLEMENTING`
- Owner: `code`
- Previous gate: TP-002-RW-01 Stage 3 scope PASS, QA `a3eb77f`; target `a4dce6d` / repair `5ea24e3`.
- Current scope: per-instance ADB screenshot and guarded relative-touch foundation using only explicit serials and injected automated-test runners.
- Next: Code implementation/self-test/commit/handoff, then full independent QA verification. Actual LD/game use remains excluded from this stage.

## TP-002-RW-01 QA handoff (2026-09-12)

## REL-003 (2026-09-14)

- Current phase: `PACKAGING`
- Owner: `code`
- Target: Code `c814ae8` / implementation `4688104`; prior `v1.0.3-rc.1` is withdrawn.
- Next: Code builds and publishes a new customer-test prerelease; QA independently checks the exact release asset. No final PASS claim.

## REL-003 published and independently smoke-checked (2026-09-14)

- Current phase: `CUSTOMER_TEST_RELEASED`
- Release: `v1.0.3-rc.2` — https://github.com/kpj0526/LDplayer/releases/tag/v1.0.3-rc.2
- Asset SHA-256: `174C34B625AD2087C5A070E604FBB8880E4F9D2935EC8E85829AB10844A4F6DA`
- Code release record: `e7e6898`; QA report: `3f08fee` (`MVP_SMOKE_PASS`).
- Scope limit: customer-test prerelease only; live LDPlayer/ADB/game validation and AC-58--AC-60 remain `BLOCKED_REAL_ENVIRONMENT / NOT_TESTED`.

## LIVE-SERIAL-001 customer failure (2026-09-14)

- Current phase: `REWORK`
- Owner: `code`
- Failure: started LD1 worker supplied `''` to `validate_serial()` despite GUI mapping `emulator-5554`; customer traceback identifies the cycle/capture path.
- Safety: validation rejected the empty serial before capture/touch. No default or cross-account command is permitted.
- Next: Code serial-propagation repair and committed tests; QA independent re-verification.

## ACK-POPUP-POSTCONDITION-001 (2026-09-20)

- Current phase: `IMPLEMENTING`
- Owner: `code`
- Failed customer release: `v1.0.3-rc.24`; popup Close center matches the configured point, so the defect is missing UI postcondition verification rather than a coordinate mismatch.
- Safety requirement: no later mission action when the popup remains; bounded account-local failure only.
- Next: Code repair and tests, QA independent exact-hash plus published-artifact verification, then new customer-test RC.

- Current phase: `VERIFYING`
- Owner: `qa`
- Target: Code `a4dce6d` / repair `5ea24e3`
- Code self-test: `105 passed, 0 failed` (not approval)
- Next: QA completes the full Stage 3 re-verification, including blank/whitespace direct validation boundaries and all Stage 3/Stage 2 regressions.

## TP-002-RW-01 (2026-09-12)

- Current phase: `REWORK`
- Owner: `code`
- Failed target: Code `c5b8961` / implementation `ffaa3ec`; QA report `356e730`.
- Major failure: the complete-mapping validator accepts a blank serial (`LD1: ""`) as valid, even though command construction later rejects it.
- Next: Code rejects blank/whitespace-only serial values at the validator boundary, adds regression coverage, self-tests and commits; QA repeats all Stage 3 checks against the submitted hash.

## TP-002 QA handoff (2026-09-12)

- Current phase: `VERIFYING`
- Owner: `qa`
- Target: Code `c5b8961` / `ffaa3ec`
- Code self-test: 98 passed (not approval)
- Next: QA independent Stage 3 scope PASS/FAIL.

## Stage transition (2026-09-12)

- Stage 2 scope: PASS, QA report `2529a1a`.
- Current phase: `IMPLEMENTING`
- Current task/owner: `TP-002` / `code`
- Next: Code implements safe ADB discovery and explicit LD1-LD9 mapping, then QA independently verifies.

## QA handoff: TP-001-RW-03 (2026-09-12)

- Current phase: `VERIFYING`
- Owner: `qa`
- Target: Code `9f54d24` / repair `d8a6fcd`
- Code self-test: 66 passed (unapproved)
- Next: QA complete Stage 2 re-verification including traceback and `exc_info` paths.

## TP-001-RW-03 (2026-09-12)

- Current phase: `REWORK`
- Owner: `code`
- Failure evidence: QA `179a679`; Critical password-like marker in `logger.exception()` traceback reaches `error.log`.
- Next: Code traceback redaction repair and commit; QA full re-verification.

## QA failure update (2026-09-12)

- Current phase: `REWORK`
- Failed target: Code `1305ba5` / repair `1acf510`
- Critical condition: controlled password marker survives `logger.exception()` traceback and is emitted to `error.log`.
- Evidence: QA direct controlled exception reproduction; QA report update in progress.
- Next: Code corrective task after QA report commit; then full QA re-verification.

## QA handoff update (2026-09-12)

- Current phase: `VERIFYING`
- Current owner: `qa`
- Task: `TP-001-RW-02` complete Stage 2 re-verification
- Target Code HEAD: `1305ba5` (repair `1acf510`)
- Code self-test: `64 passed, 0 failed` (not an approval)
- Next: QA independent PASS/FAIL. Stage 3 is not authorized until Stage 2 scope PASS.

## Latest authoritative status (2026-09-12)

- Current phase: `REWORK`
- Current owner: `code` (Manager coordination)
- Current task: `TP-001-RW-02` Stage 2 security correction
- Failed Code target: `ba0e3da1228b70cd34a40e74a0f262212ed8310a`
- QA failure report commit: `5cba31e2d09b254166e4dbb79a5786be674e848e`
- Blocking: controlled password marker persisted in account log (Critical); generated `logs/` and `diagnostics/` artifacts are not ignored.
- Next: Code repair/self-test/commit; QA full re-verification of exact repair hash.

- 현재 단계: `VERIFYING`
- 현재 담당자: qa (Manager 조정)
- 현재 작업: TP-001 단계 2 — 설정 및 계정별 로그 시스템 독립 검증
- Manager 브랜치/커밋: `kpj0526/Manager` / `ddca498abb5073d00ffd1fb80c0761df7ebae4ac`
- Code_edit 브랜치/커밋: `kpj0526/Code` / `ddca498abb5073d00ffd1fb80c0761df7ebae4ac`
- QA 브랜치/커밋: `kpj0526/Qa` / `ddca498abb5073d00ffd1fb80c0761df7ebae4ac`
- 차단 요소: 실제 ADB 매핑·게임 화면 fixture는 후속 단계에서 필요. 단계 1 구현은 시작 가능.
- 다음 작업: qa PASS/FAIL 수신 후 단계 3 또는 단계 2 재작업.
