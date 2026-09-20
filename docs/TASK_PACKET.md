# TASK PACKET — TP-001 (통합본)

## ADB-PATH-001 — customer-visible ADB executable selection (2026-09-14)

1. **WHO**: customer/operator configures local LDPlayer; Manager coordinates; existing Code implements; existing QA independently verifies.
2. **WHAT**: resolve live customer error `Device discovery failed: ADB device listing failed: FileNotFoundError` by adding a GUI-visible ADB executable path state/control (auto-detect result plus Browse/select and save/clear) rather than requiring customer terminal/PATH setup.
3. **WHERE**: existing Code GUI/config/ADB-discovery/tests and Code handoff only.
4. **WHEN**: immediately after approved packet; QA receives exact Code commit after implementation.
5. **WHY**: real customer screenshot proves `v1.0.1` could not locate `adb.exe`; device serial discovery cannot begin even with local ADB debugging enabled.
6. **HOW**: preserve existing candidate resolution order; expose resolved/configured path and error in GUI; permit an explicit existing `adb.exe` selection; persist only the local path in existing ignored config; reinitialize/refresh discovery safely; no guessed serial/port, Worker, touch, or game input.
7. **CONSTRAINTS**: no credentials; no filesystem deletion; no automatic device mapping; invalid/missing executable must remain fail-closed with actionable UI error; no agents/subagents/worktrees; do not claim real LD/game success.
8. **ACCEPTANCE CRITERIA**: `ADBPATH-01` GUI shows configured/resolved ADB executable state. `ADBPATH-02` user can choose a real local `adb.exe` without terminal/YAML editing; invalid path is rejected visibly. `ADBPATH-03` configured path persists locally and enables read-only discovery after restart. `ADBPATH-04` discovery/path selection produces zero touch/Worker side effects and never assigns serials automatically. `ADBPATH-05` regression suite/build pass; QA independently verifies exact Code hash.
9. **OWNER**: Code implements/tests/builds/handoffs; QA verifies; Manager records/release decision.
10. **NEXT ACTION**: Code receives packet; customer can meanwhile apply explicit `adb_path` workaround only after locating real emulator `adb.exe`.

## GAME-CAL-001: live mission-screen template/state calibration (2026-09-14)

1. **WHO**: Manager coordinates; existing Code implements/commits; existing QA independently verifies. No new agents, roles, or worktrees.
2. **WHAT**: Correct account-local mission-screen recognition that rejects customer-valid screens.
3. **WHERE**: Code worktree only: external recognition assets/ROI/threshold configuration, state logic, tests, build, and Code handoff. Manager changes no production code.
4. **WHEN**: Code starts from this packet; QA receives only an exact Code commit.
5. **WHY**: Customer's mapped 1280x720 LD1/LD3/LD4 screens fail preflight. Test capture is diagnostic-only, not template editing.
6. **HOW**: Configure stable anchors for `Mission`, `Region`, and mission-list/detail layout using supplied captures. Distinguish verified completed state from in-progress `130/180`/currency state. Permit a completion touch only on verified completed state, with one explicit account serial and verified pre/postconditions. Dynamic reward amounts/progress cannot be a sole anchor.
7. **CONSTRAINTS**: No touch on mismatch, unknown, progress, or currency state; specifically never press the `6600` action. No template auto-overwrite, guessed serial/port, global coordinates, login, unbounded loop, or real success claim. Retain global/individual-stop, serial isolation, bounded timeout/retries, worker containment, and GUI startup safety.
8. **ACCEPTANCE CRITERIA**: completed and in-progress fixtures classify differently; completion is impossible for `130/180`/currency/unknown/mismatch; completion is serial-scoped with pre/postcondition; mismatch stays diagnostic/account-local; tests/build/startup pass. Live-game proof remains `NEEDS_REAL_TEST`.
9. **OWNER**: Code implements/tests/commits/handoff; QA independently verifies exact hash; Manager records/gates.
10. **NEXT ACTION**: Code supplies one committed correction; Manager routes its exact hash to QA.

## REL-UPDATE-003 — import and verify remote `v1.0.1` (2026-09-14)

1. **WHO**: customer receives the macro; Manager coordinates; existing Code imports/builds; existing QA independently verifies.
2. **WHAT**: safely incorporate remote source tag `v1.0.1` (`299e7a91840505cc90dcbb6b6f9e2ad75ed3b1cf`) into the existing Code branch and prepare a candidate Windows artifact.
3. **WHERE**: Code worktree/branch only. No new agent, worktree, or role.
4. **WHEN**: immediately after this packet; QA starts only after Code submits an exact committed target.
5. **WHY**: the candidate adds an account-local screen-capture/template preflight that prevents Start until an explicitly mapped account's game screen is recognized.
6. **HOW**: Code inspects ancestry/diff, uses a non-destructive integration method preserving existing committed work, resolves any conflict without discarding user changes, runs the full suite and Windows build, records precise artifact/test evidence in `docs/HANDOFF_CODE.md`, and commits. QA checks the exact Code hash independently.
7. **CONSTRAINTS**: no reset/checkout that discards work; no auto-mapping, touch, Worker, game input, release publish, credentials, or real-game success claim. No agents/subagents/worktrees. The tag itself is not an executable release or QA evidence.
8. **ACCEPTANCE CRITERIA**: `REL-003-AC-01` Code imports only reviewed `v1.0.1` change set and preserves approved work. `REL-003-AC-02` Start stays disabled until this account's mapping is OK and Test capture passes; LD1 readiness must not enable LD2. `REL-003-AC-03` saving/clearing a mapping resets only that account's capture readiness. `REL-003-AC-04` capture mismatch saves diagnostic capture/prevents Start and calibration UI is hidden by default. `REL-003-AC-05` full tests and Windows build succeed; no publication pending QA.
9. **OWNER**: Code implementation/build/handoff; QA independent regression/package verification; Manager records/release decision.
10. **NEXT ACTION**: Code receives this packet, submits exact commit, Manager routes that target to QA.

## UI-ADB-001: Customer-friendly LD registration

1. **WHO**: Windows customer who does not use terminals or edit configuration files; existing `code` implements; existing `qa` independently verifies; Manager coordinates. No other agents or worktrees.
2. **WHAT**: Add an ADB registration area under each LD1..LD9 GUI panel, with current mapping/state, discovered serial selection or manual entry, save/clear controls, and a global device-refresh action.
3. **WHERE**: Existing native Python GUI and local ignored configuration in the existing Code worktree; mappings remain `LDx -> ADB serial`.
4. **WHEN**: Before starting an account. Refresh discovers available ADB devices; customer explicitly assigns one to an LD panel and saves. Invalid/unmapped accounts cannot start.
5. **WHY**: Customers must be able to register their LD instances without terminals or YAML editing while retaining strict cross-account safety.
6. **HOW**: Use the existing explicit-serial ADB discovery/validation layer. Display discovered serials without auto-assignment; validate exact LD1..LD9 keys, nonblank serials and uniqueness; write a local ignored config atomically; reload/update panel state; surface understandable errors. Keep all ADB control serial-scoped.
7. **CONSTRAINTS**: No guessed port/automatic LD assignment; no credentials; no Worker or tap from refresh/save; do not mutate production mapping until validation succeeds; no new agents/worktrees; existing configuration remains compatible.
8. **ACCEPTANCE CRITERIA**: `AC-61` GUI displays per-LD mapping state and allows explicit serial selection/entry. `AC-62` Refresh shows discovered ADB devices but never auto-assigns them. `AC-63` Save persists a valid unique mapping locally and reloads it. `AC-64` blank, duplicate, unavailable, or invalid mapping is rejected with a panel-visible error and cannot start that account. `AC-65` registration/refresh emits no touch and starts no Worker; mapping to one LD cannot affect another.
9. **OWNER**: `code` implements/tests/commits/handoffs; `qa` verifies the exact commit; Manager tracks and only publishes a release after the release scope is verified.
10. **NEXT ACTION**: Code completes its currently running release build safely, then implements UI-ADB-001 on its existing branch, runs tests and reports a commit. QA independently verifies AC-61..AC-65. Release is held for that verified MVP increment.

## 1. WHO

사용자는 Windows의 십이지천2M 다계정 사용자다. Manager는 조정·문서·최종 판단, code는 코드·테스트 구현, qa는 독립 검증을 담당한다. LD1~LD9의 9개 계정과 계정별 5개 토벌임무가 대상이다.

## 2. WHAT

LD1~LD9 독립 제어, 계정/전체 시작·정지, GUI 상태·오류·로그·설정 관리를 제공한다. 계정마다 5개 임무의 목표 문구를 확정하고 200마리 완료·보상·초기화·반복을 수행한다.

## 3. WHERE

Windows 데스크톱의 LD플레이어 인스턴스와 각 인스턴스의 개별 ADB 장치다. 화면 위치가 아닌 인스턴스 이름·ID·ADB 장치/포트 또는 사용자 매핑으로 식별한다.

## 4. WHEN

개별/전체 명령은 해당 범위의 자동 입력만 제어한다. 재시작 전 현재 화면을 판별하고 불명확하면 오류 처리한다. 2부 수신으로 구현이 허가됐으며, 단계별 `Manager 전달 → code 구현·자체 테스트·커밋 → Manager 확인 → qa 검증`을 적용한다.

## 5. WHY

단순 반복 클릭이 아닌, 게임의 현재 상태를 검증하고 정확한 조건에서만 임무 변경·완료·보상·초기화를 반복하기 위함이다.

## 6. HOW

Python·OpenCV·필요 시 OCR·ADB 캡처/터치·개별 Worker/상태 머신·GUI/Worker 분리·설정/로그·Windows 패키징을 사용한다. 클릭 전후 화면 상태와 신뢰도를 확인하고 대상 ADB의 내부 상대좌표만 사용한다. 이미지·ROI·좌표·임계값은 설정 파일로 분리한다.

## 7. CONSTRAINTS

웹 DOM·전역 고정좌표·메모리/패킷/보안 우회·자동 로그인/재접속/사냥터 이동을 금지한다. 낮은 신뢰도나 예상 밖 화면에서 클릭하지 않고, 모든 반복은 타임아웃·최대 재시도를 갖는다. 계정 오류·입력은 서로 격리한다. 신규 에이전트·하위 에이전트·worktree·역할 생성 금지, 민감정보 저장 금지, QA PASS 전 완료 선언 금지다.

## 8. ACCEPTANCE CRITERIA

AC-01~AC-30을 적용한다. 명세·진행 상태는 `docs/ACCEPTANCE_STATUS.md`, 검증 방법은 `docs/TEST_PLAN.md`에 기록한다.

## 9. OWNER

현재 Manager는 단계 1 작업 전달과 진행 문서, code는 단계 1 구현, qa는 code 커밋 후 독립 검증을 담당한다.

## 10. NEXT ACTION

## TRANSITION-POSTCONDITION-AUDIT-001: audit every game-state-changing tap

1. **WHO**: Existing `code` implements/commits; existing `qa` independently verifies. No new agents, roles, or worktrees.
2. **WHAT**: Repair and audit every state-changing mission tap for the observed class of defect: a tap command returning success is treated as a screen transition, while an intervening acknowledgement popup remains or the expected screen never appears.
3. **NEW CUSTOMER EVIDENCE**: `v1.0.3-rc.24`, LD1 `127.0.0.1:5555`, original live screen shows the “자유 토벌작전 / 확률 / 닫기” overlay immediately following mission initialization. GUI: `refresh_popup_not_verified`, `Slot 1: refresh popup never verified structurally within 5 attempt(s); confirm not sent.` This proves the currently missing site is **after `refresh_button_point` and before `_verify_refresh_popup`**; existing rc.24 dismissal logic runs only after `refresh_confirm_point` or `accept_mission_point`, so it cannot run before confirmation was sent.
4. **AUDIT SCOPE**: Inspect every `runner.run(... build_tap_args(...))` in `bounty_mission.py` and direct guarded touch path: slot select, refresh open, refresh confirm, mission accept (both paths), complete select/tap, reward open/claim, result close, and any configurable fixed-point fallback. For each, define: precondition recognition, explicit serial, bounded postcondition recognition, retry delay/budget, individual/global stop boundaries, and account-local failure outcome. Fix any path that proceeds based only on ADB return code or that has no safe postcondition. Do not add unbounded loops or default/guessed targets.
5. **REQUIRED FIX**: Before refresh-popup structural verification, detect the acknowledgement overlay using the real `reward_odds_label`; if present, close once per bounded attempt using the measured point, freshly capture until the overlay is absent, then verify the actual refresh popup. If absent, do not tap Close. On no transition, return a distinct outcome; do not send refresh-confirm or any later action.
6. **TESTS**: Build a table-driven transition audit with fake runner/recognizer coverage for every listed tap. Include the supplied pre-confirm overlay path, permanent overlay/no downstream confirm, delayed transition, stop between retries, serial isolation, and regression of all prior result/claim/accept flows. Run full suite; update Code handoff.
7. **RELEASE**: New customer-test prerelease only after Code commit and QA independent verification. Mark rc.24 superseded for the pre-confirm acknowledgement overlay failure. Real live test remains `NEEDS_REAL_TEST`.

## ACK-POPUP-POSTCONDITION-001: verify the close popup actually disappeared

1. **WHO**: Existing `code` implements and commits; existing `qa` independently verifies and release-smokes. No new agent, subagent, role, or worktree.
2. **WHAT**: Correct the live `v1.0.3-rc.24` failure where the “자유 토벌작전 / 확률 / 닫기” acknowledgement popup remains visible after the close tap, but the worker treats a successful ADB return code as dismissal success and later reports `mission_list_verify_failed`.
3. **EVIDENCE**: Customer supplied original 1280x720 capture (2026-09-20). Its Close center is approximately `(641, 511)`, matching the current `close_result_point` `(0.5012, 0.7104)` exactly. GUI showed `mission_list_verify_failed`, five bounded verification attempts, and phase `VERIFYING_MISSION_LIST` while the popup remained. Thus this is not a guessed-coordinate calibration issue.
4. **HOW**: After every acknowledgement-popup close tap, capture fresh frames and require the popup anchor (`reward_odds_label`) to become absent AND the expected next state to be positively recognized before proceeding. Use bounded retries, the configured delay, explicit selected serial only, and no repeated input after individual/global stop. If postcondition never becomes true, return a distinct account-local `ACK_POPUP_DISMISS_FAILED` outcome with evidence/capture detail; make no later slot select, refresh, completion, reward, claim, or cross-account command. Never regard ADB `returncode == 0` alone as proof of a game-screen transition.
5. **TESTS**: Add real-capture and fake-runner regressions for the supplied exact popup: (a) first close does not transition then second permitted close does; (b) never-transition stays bounded, produces the distinct outcome, and sends no downstream action; (c) popup absent is a no-op; (d) stop before/between retries gives no further input; (e) serial isolation includes every capture/tap. Preserve existing full suite.
6. **RELEASE**: Code builds a new customer-test RC only after the committed repair and Code self-tests. QA independently tests exact commit and published ZIP. Release notes must state that rc.24 is superseded for this popup case and that live re-test remains `NEEDS_REAL_TEST`.
7. **NEXT**: Code begins now; QA validates the exact submitted hash and new published asset. No Start on the current rc.24 during repair.

## LIVE-SERIAL-001: configured-serial loss in worker-cycle corrective packet

1. **WHO**: Existing `code` repairs and commits; existing `qa` independently re-verifies. No new agents, roles, or worktrees.
2. **WHAT**: Correct the customer-environment failure where LD1 displays a valid mapping (`emulator-5554`) but the worker passes an empty ADB serial into screenshot capture after Start.
3. **EVIDENCE**: Customer screenshot, 2026-09-14: `worker crashed` → `controller.py:127 _loop` → `app.py:80 _cycle` → `bounty_mission.py:373 run_one_cycle` → `_accept_or_refresh_slot` → `_tap_template` → `_recognize` → `screenshot.py:71 capture_screenshot` → `adb.py:149 validate_serial` → `ValueError: Invalid ADB serial: ''`. GUI simultaneously displays LD1 mapping `emulator-5554`.
4. **HOW**: Trace controller/worker construction and every mission-cycle helper. Preserve the one explicit nonblank selected-account serial through all capture/recognize/tap calls; reject/make account-local error before any capture/touch if absent. Never substitute a default device or another account. Add regression coverage specifically proving a configured LD1 serial reaches every cycle capture/tap helper and that an absent serial produces zero ADB/capture/touch calls and a contained account error. Retain individual/global stop and bounded-action behavior.
5. **ACCEPTANCE**: Full regression passes; direct injected reproduction passes; Code commits exact hash and `HANDOFF_CODE.md`. QA repeats exact serial-argv/capture/touch isolation and exception-containment checks. Real customer re-test remains `NEEDS_REAL_TEST`; no global/final PASS.
6. **NEXT**: Code begins now; QA receives only Code's committed exact hash.

## REL-003: customer-test replacement prerelease

1. **WHO**: Existing `code` packages and publishes; existing `qa` independently smoke-checks the exact packaged result; Manager coordinates. No new agent, subagent, role, or worktree.
2. **WHAT**: Replace the withdrawn `v1.0.3-rc.1` customer artifact with a new Windows prerelease built from Code commit `c814ae850f3cd89e9c5e0feefc451e9c90d7aeff` (implementation `4688104067bbb90cdc5e5cb1d74579be770a5c1a`).
3. **HOW**: Use a new version/tag (do not alter or re-enable `v1.0.3-rc.1`); build the Windows ZIP from the exact target; verify ZIP/executable hash, packaged real-calibration templates, clean Git state, and release asset; push only the Code branch/tag and create a GitHub prerelease with the explicit customer-test limitations. Record exact commit/tag/asset SHA-256/URL in `docs/HANDOFF_CODE.md` and commit the release-record update.
4. **SAFETY / RELEASE NOTES**: State that this is a customer-test prerelease, not final delivery. The customer must configure an explicit nonblank ADB serial per account, begin with one account, use Test capture/mapping verification before Start, and stop immediately on mismatch/unknown/error. No automatic input after global stop; no live-game/LDPlayer validation has been performed by QA. `AC-58`--`AC-60` remain `BLOCKED_REAL_ENVIRONMENT / NOT_TESTED`.
5. **ACCEPTANCE**: The published asset must derive from the named target, must not be the withdrawn hash `4764FE903D4C2F7D5F7D4F1904D4E53D6EE0B964BC2D622D050A4C46960DA959`, and must be independently smoke-checked by QA before Manager reports the customer download link. QA does not claim final project PASS.
6. **NEXT**: Code submits the exact release commit/tag/hash/URL; QA independently checks the published artifact and records `MVP_SMOKE_PASS`, `MVP_SMOKE_FAIL`, or `BLOCKED_REAL_ENVIRONMENT`.

## MVP-001-CV: customer-video free-bounty mission-cycle extension

1. **WHO**: Customer operates nine LDPlayer accounts and supplies real game assets/environment; existing `code` implements; existing `qa` independently smoke-tests; Manager coordinates. No new agents, subagents, roles, or worktrees.
2. **WHAT**: Merge the customer-video behavior into the MVP: five mission slots; status inspection; popup-verified refresh; phrase-plus-200 target acceptance; bounded rerolls; selected target preservation; completion/reward/result/close/list-return/re-refresh/reaccept/repeat cycle.
3. **WHERE**: Existing Code worktree after its current MVP-001 safe-unit commit. Use per-account ADB capture/guarded relative touch only. Recognition assets, ROI, coordinates, thresholds/retries/timeouts must be external configuration/placeholders; no guessed live values.
4. **WHEN**: Code begins this extension only after safely committing current MVP-001 work. QA performs abbreviated mock/safety smoke after Code's new committed handoff. Actual customer device/video validation follows only when the user supplies the needed assets/environment.
5. **WHY**: Customer video defines the operational mission loop; a draft that stops at generic mission states is insufficient.
6. **HOW**: Add/merge states `SELECTING_MISSION_SLOT`, `CHECKING_MISSION_STATUS`, `OPENING_REFRESH_CONFIRM`, `CONFIRMING_REFRESH`, `CHECKING_NEW_MISSION`, `ACCEPTING_TARGET_MISSION`, `REJECTING_NON_TARGET_MISSION`, `WAITING_KILL_PROGRESS`, `MISSION_COMPLETED`, `CLICKING_COMPLETE`, `OPENING_REWARD`, `CLAIMING_REWARD`, `CLOSING_REWARD_RESULT`, `RETURNING_TO_MISSION_LIST`, `ERROR`. Before every action: capture and recognize expected state; then conditionally make one serial-scoped touch; require state change before advancing. Refresh uses verified popup structure/title/buttons rather than any fixed cost. Target needs both phrase and 200. Incomplete 0-199 never clicks complete/reward. Use fakes/fixtures for state sequence and configurable placeholder recognition adapter.
7. **CONSTRAINTS**: Current MVP work is retained. No DOM/global mouse/fixed desktop coordinate/guessed serial or port/credentials/login/reconnect/automatic hunting movement/security bypass. All loops bounded. Unknown/low-confidence/stalled/disconnected/ended screen yields account-local error and no arbitrary click. Do not treat a placeholder or a single OCR reading as real-game verification. No feature is PASS without evidence.
8. **ACCEPTANCE CRITERIA**: New continuous AC-31..AC-60. Mandatory smoke priority: serial isolation; verified-popup-only confirmation independent of cost; joint phrase+200 condition; target/non-target behavior; 0-199 no completion/reward; bounded repeat; account fault containment; GUI/controller startup. AC-58..AC-60 remain `BLOCKED_REAL_ENVIRONMENT` pending customer LD/video proof.
9. **OWNER**: `code` implements/tests/commits and updates `HANDOFF_CODE.md`; `qa` checks the exact submitted hash, reports MVP smoke outcome, and preserves real-environment gaps; Manager tracks new ACs and routes failures back to Code.
10. **NEXT ACTION**: Manager queues this packet to existing Code after current MVP-001 safe unit. Code submits its exact extension hash; QA then smoke-tests mock video cycle and logs needed real customer captures.

## MVP-001: connected executable MVP draft Task Packet

1. **WHO**: Windows user runs LDPlayer LD1-LD9; existing `code` implements the MVP; existing `qa` runs a post-commit smoke/safety suite; Manager coordinates. Existing roles/worktrees only—no agent, subagent, role, or worktree creation.
2. **WHAT**: Deliver one runnable, configurable Python MVP linking: LD1-LD9 explicit mapping; per-account independent Workers; individual start/stop and global start/stop; capture; target phrase recognition interface; five mission slots with reroll-or-keep logic; kill-complete/reward/reset/repeat state transitions; account status/error/log display; basic GUI; start and Windows build scripts.
3. **WHERE**: Existing Code worktree. Program/test/config/script/docs changes are allowed there. Manager does not edit production code; QA does not edit production code. Actual user credentials, real game accounts, or secret mappings must never be committed.
4. **WHEN**: Start immediately after Stage 4 scope PASS `d69bc0b`. Code makes one connected MVP submission; QA then uses abbreviated MVP smoke testing rather than full AC certification.
5. **WHY**: Produce a usable draft that can be launched now and calibrated with actual screen templates/ROIs on the customer's LDPlayer environment instead of waiting for full final validation.
6. **HOW**: Reuse the explicit-serial ADB, capture, guarded touch, config, diagnostics and logging foundations. Implement a controller with one cancellable Worker per account; an explicit bounded state machine for five slots and the mission cycle; a recognizer abstraction that calls configured template/OCR adapters and returns confidence/unknown safely; configurable image-template paths, ROIs, relative coordinates, thresholds, retry/timeouts; a simple native Python GUI that displays per-account status, slot, targets, error and recent log and offers individual/global start/stop; CLI/start script; PyInstaller build script or equivalent. Use placeholder config/template assets where real game inputs are missing and document them. Build tests with mocks/fakes.
7. **CONSTRAINTS**: Never use DOM/global mouse/external fixed coordinates/guessed device ports. Every command has exactly one explicit serial. Do not automate login/reconnect/hunting-ground movement or circumvent game security. Keep every repeat bounded; recognition/capture/unknown-screen failures must safely stop/error the affected account with logs/diagnostics. One Worker fault must not end others. Global stop must cancel all automatic input. Avoid fake hard-coded image recognition success. Do not claim real-environment success.
8. **ACCEPTANCE CRITERIA**: MVP code traceability targets core requested areas, especially AC-03..AC-08, AC-10..AC-27, AC-28 and AC-29. Mandatory MVP smoke: (a) LD1 command cannot reach another account and each argv has the selected serial; (b) individual stop is local; (c) global stop leaves no automatic touch; (d) retry/timeouts work; (e) recognition failure cannot loop click; (f) one Worker exception is contained; (g) application/GUI starts; (h) mock cycle enters each core mission state once. Results use only `MVP_IMPLEMENTED`, `MVP_SMOKE_PASS`, or `NEEDS_REAL_TEST`; actual LD/game checks remain `NOT_TESTED`/`BLOCKED_REAL_ENVIRONMENT`.
9. **OWNER**: `code` implements, tests, commits and updates `docs/HANDOFF_CODE.md`. `qa` independently runs required smoke/safety tests and commits `reports/QA_REPORT.md` with `MVP_SMOKE_PASS`, `MVP_SMOKE_FAIL`, or `BLOCKED_REAL_ENVIRONMENT`. Manager documents/gates and does not alter program code.
10. **NEXT ACTION**: Send this packet to existing Code now. On committed submission, send exact hash to existing QA for abbreviated smoke testing; then report runnable MVP scope and real-environment gaps.

## TP-003: per-instance screenshot and guarded relative-touch Task Packet

1. **WHO**: Windows user ultimately operates LD1-LD9; existing `code` implements; existing `qa` independently verifies; Manager coordinates. No agents, subagents, new roles, or worktrees may be created.
2. **WHAT**: Implement a safe foundation to capture the screen of one explicitly mapped ADB device and send a guarded relative-coordinate touch only to that same device.
3. **WHERE**: Existing Code worktree. Scope covers injectable ADB/capture/control interfaces, models/configuration as needed, automated fakes/tests, and Code handoff. It excludes live game navigation, mission actions, global mouse, GUI, OCR/template matching, login/reconnect, and real device testing.
4. **WHEN**: Start after Stage 3 scope PASS (`a3eb77f`). QA receives the exact Code hash only after Code self-tests and commits.
5. **WHY**: Later mission automation must capture, verify, and act within exactly one LD instance without cross-account clicks or uncontrolled clicking.
6. **HOW**: Use only parameterized `adb -s <explicit-serial>` commands through an injectable binary-capable runner. Provide safe screenshot capture with failure/invalid-image handling and diagnostic metadata. Provide relative device-coordinate validation and a guarded-touch operation requiring a caller-supplied precondition on a fresh capture and a postcondition after touch; if either condition is low-confidence/false, fails, or times out, send no further action and return an account-local controlled failure. Bound retries/timeouts; do not infer ports, serials, device defaults, or external screen coordinates. Use fakes to prove exact argv targeting, capture byte validation, precondition rejection/no touch, postcondition timeout, and cross-account isolation.
7. **CONSTRAINTS**: No web DOM, global mouse, fixed desktop coordinates, automatic login/reconnect/movement, credentials, game-memory/packet manipulation, unbounded loops, or real-device activity in tests. Each action must be restricted to a nonblank explicitly supplied serial. Keep templates/ROI/threshold values out of code where configuration is needed. Preserve prior Stage 1-3 behavior and security regressions.
8. **ACCEPTANCE CRITERIA**: Primary implementation traceability AC-09; foundations for AC-23, AC-24, AC-28, and later AC-10..AC-20. Automated evidence must show one target serial only, capture failure safety, invalid image safety, no touch when precondition fails, no repeated input after postcondition failure/timeout, account-local error containment, and preserved regression suite. No global AC PASS or AC-30 PASS is allowed without actual user-PC verification.
9. **OWNER**: `code` implements/tests/commits and updates `docs/HANDOFF_CODE.md`; `qa` validates the exact Code hash, performs independent probes and regression runs, and commits `reports/QA_REPORT.md`; Manager records/gates results and does not modify production code.
10. **NEXT ACTION**: Send TP-003 to existing Code. After committed handoff, send exact hash to existing QA for full TP-003 verification.

## TP-002-RW-01: blank ADB serial validation corrective Task Packet

1. **WHO**: Manager coordinates; existing `code` repairs; existing `qa` independently re-verifies. No agent, subagent, role, or worktree may be created.
2. **WHAT**: Repair the Major Stage 3 defect where a nine-account mapping with `LD1: ""` passes complete ADB-mapping validation.
3. **WHERE**: Existing Code worktree only. Scope is the complete-mapping validation API, its tests, and the Code handoff document. No real ADB, LDPlayer, screenshot, touch, or game action is authorized in this repair.
4. **WHEN**: Begin now. QA runs full TP-002 re-verification only after Code submits a committed exact hash.
5. **WHY**: QA report `356e730` reproduced `validate_complete_adb_mapping(mapping) == []` after setting `mapping["LD1"] = ""`. This violates the explicit nonblank serial mapping contract and is a Major safety defect.
6. **HOW**: Make `validate_complete_adb_mapping()` report an error for empty and whitespace-only serial values; ensure `ensure_complete_adb_mapping()` consequently raises. Preserve valid nine-distinct mappings and the already safe command builder. Add focused regression tests for empty and whitespace-only values, then run the complete suite.
7. **CONSTRAINTS**: Do not infer ports, default devices, or mappings; do not weaken/remove tests; do not bypass validation; do not introduce touch/global mouse/DOM/login/reconnect behavior; do not expose credentials; do not create agents/worktrees; do not modify unrelated production behavior.
8. **ACCEPTANCE CRITERIA**: Stage scope traceability AC-02 and foundational AC-09: (a) direct empty and whitespace-only mapping probes yield validation errors and `ensure_complete_adb_mapping()` raises; (b) nine distinct nonblank mappings remain accepted; (c) full regression passes; (d) QA repeats parser, mapping, no-auto-assignment, account-local-status, serial-argv, and prior regression checks. Global ACs remain `NOT_TESTED` until actual project-level evidence exists.
9. **OWNER**: `code` implements/tests/commits and updates `HANDOFF_CODE.md`; `qa` independently verifies the exact Code hash and updates `reports/QA_REPORT.md`; Manager records results and makes no program-code change.
10. **NEXT ACTION**: Send this packet to existing Code. After a committed submission, send its exact hash to existing QA for full Stage 3 re-verification.

## TP-001-RW-02: Stage 2 corrective Task Packet

## TP-001-RW-03: traceback secret-leak corrective Task Packet

## TP-002: Stage 3 LD1-LD9 discovery and ADB mapping

1. **WHO**: Windows user operates LDPlayer instances LD1-LD9; existing `code` implements; existing `qa` independently verifies; Manager coordinates.
2. **WHAT**: Build the safe discovery and explicit mapping foundation for exactly nine LDPlayer accounts and their distinct ADB devices.
3. **WHERE**: Code worktree: configuration/model/service/tests/docs only. No actual game automation, screenshots, touch commands, or GUI interaction is in this stage.
4. **WHEN**: Start after Stage 2 scope PASS (QA report `2529a1a`). Actual user-PC integration remains a later QA gate.
5. **WHY**: Every later capture/touch command must target one verified device only; no ADB port may be guessed or shared across accounts.
6. **HOW**: Query available ADB devices through an injectable runner; parse safe `adb devices` results; require an explicit LD1-LD9-to-serial mapping in validated configuration; reject missing, duplicate, offline, unauthorized, unknown, or non-nine mappings; expose mapping connection status and structured diagnostic errors without logging secrets. Use fakes/mocks for automated tests. Do not connect or issue control commands to real devices during tests.
7. **CONSTRAINTS**: No fixed/guessed ports, global mouse, web DOM, game control, login/reconnect, credentials, or destructive operations. ADB command execution must remain parameterized and scoped to a selected serial. One account mapping failure must be representable without affecting valid mappings. No new agents/worktrees.
8. **ACCEPTANCE CRITERIA**: Implement-stage traceability: AC-01 (LD1-LD9 identification), AC-02 (exact ADB mapping), and foundational isolation evidence for AC-09. Automated evidence must cover nine valid mappings, duplicate/missing mappings, offline/unauthorized/unknown serials, malformed discovery output, and command target separation. Actual LD1-LD9 user-PC validation remains AC-30 `NOT_TESTED`.
9. **OWNER**: `code` implements, self-tests, commits, and updates `HANDOFF_CODE.md`; `qa` validates exact commit independently and reports scope PASS/FAIL. Manager does not change program code.
10. **NEXT ACTION**: Deliver TP-002 to Code. After Code commit, QA completes the Stage 3 verification before Stage 4 begins.

1. **WHO**: Manager coordinates; existing `code` repairs; existing `qa` independently re-verifies. No agents, subagents, roles, or worktrees may be created.
2. **WHAT**: Correct the Critical Stage 2 failure in which `logger.exception()` emits a controlled password-like marker in formatted traceback text to `error.log`.
3. **WHERE**: Existing Code worktree only. Scope: logging/redaction boundary, regression tests, and Code handoff document.
4. **WHEN**: Start immediately. QA re-verifies the full Stage 2 scope only after a committed Code submission.
5. **WHY**: QA report commit `179a679252cda5adb4002b0ed341ea9089ed4881` reproduced `traceback_sensitive_marker_absent=False` for Code target `1305ba5a8b629e77664566702fb3ffe04eb8ac5e`.
6. **HOW**: Ensure sensitive values are redacted or exception output is safely prevented before any file handler writes formatted `exc_info`/traceback text. Do not retain originals. Add direct regression coverage using `logger.exception()` with a controlled marker and verify the marker is absent from `error.log`. Preserve previously passing ordinary, percent-argument, ignore, isolation, rotation, retention, config-validation, path-safety, and diagnostics behavior.
7. **CONSTRAINTS**: Mandatory no credential/password/authentication logging applies to message, arguments, exception text, and traceback output. Do not weaken tests, delete user data, bypass error logging without a documented safe behavior, or create agents/worktrees. Run complete tests, commit, and update Code handoff.
8. **ACCEPTANCE CRITERIA**: Mandatory security gate associated with AC-26 logging. Exact QA reproduction must return `traceback_sensitive_marker_absent=True`; complete tests pass; all prior Stage 2 checks are rerun independently by QA. No global project AC is marked PASS based solely on this stage.
9. **OWNER**: `code` implements/self-tests/commits; `qa` independently validates exact Code hash and writes `reports/QA_REPORT.md`; Manager records and gates Stage 3.
10. **NEXT ACTION**: Manager sends this packet to `code`; Code provides a committed handoff; QA performs full Stage 2 re-verification.

1. **WHO**: Manager coordinates; existing `code` repairs; existing `qa` independently re-verifies. No new agent or worktree is permitted.
2. **WHAT**: Correct Stage 2 security failures found for Code commit `ba0e3da1228b70cd34a40e74a0f262212ed8310a`.
3. **WHERE**: Code worktree only: logging implementation, tests, and `.gitignore`.
4. **WHEN**: Begin immediately; QA fully re-verifies Stage 2 after Code submits a new commit.
5. **WHY**: A controlled `password=...` marker persisted unredacted in an account log; generated log and diagnostic artifacts were not ignored.
6. **HOW**: Redact or reject sensitive content before any handler emits a record. Cover password, token, API key, authorization, and cookie-style values. Ignore generated `logs/` and `diagnostics/`. Add regression tests proving task/error logs contain no literal marker and those outputs are ignored.
7. **CONSTRAINTS**: Do not log credentials. Do not delete user data, weaken tests, bypass failure, create agents/worktrees, or claim an AC PASS. Run complete tests and commit; QA independently runs all Stage 2 checks.
8. **ACCEPTANCE CRITERIA**: Primary traceability AC-26; security constraints are mandatory gates. Expected: no literal marker in task/error logs; the generated test paths are ignored; full regression passes. All project ACs remain globally `NOT_TESTED` until relevant implementation and evidence exist.
9. **OWNER**: `code` implements/self-tests; `qa` validates exact submitted commit; Manager records and decides progression.
10. **NEXT ACTION**: Send this packet to `code`; send its exact repair hash to `qa` for full Stage 2 re-verification.

code가 1단계 프로젝트 기본 구조를 구현·테스트·커밋·인수인계한 뒤, Manager가 증거를 확인하고 qa에 해당 커밋의 독립 검증을 전달한다.
