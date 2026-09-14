# CURRENT TASK

## `v1.0.1` candidate publication decision (2026-09-14)

- Task ID: `REL-UPDATE-003-RELEASE`
- Title: Decide whether to publish the QA-smoke-passed `v1.0.1` candidate
- Purpose: keep QA approval and external customer deployment distinct.
- Owner: Manager publication only after explicit user direction.
- Status: `READY_FOR_APPROVAL`.
- QA result: `MVP_SMOKE_PASS`, QA report commit `2a13f52`; exact Code target `2c47736`.
- Evidence: QA independently reports 302 full-suite passes, 58 focused passes, safe-mode input block, local UI/isolation probes, and fresh artifact bootstrap/launch.
- Not complete: no GitHub `v1.0.1` release, tag push, executable asset, or checksum is published. No actual LD/game environment was used.
- Completion: Manager produces a new explicit MVP prerelease with artifact/hash/release notes only if user requests publication; real-environment validation remains later work.
- Next action: await explicit publication direction.

## `v1.0.1` independent QA release-candidate verification (2026-09-14)

- Task ID: `REL-UPDATE-003-QA`
- Title: Independently verify Code's `v1.0.1` import/candidate build
- Purpose: establish whether Code target `2c47736` is eligible for a future customer release without claiming real-game proof.
- Owner: existing QA.
- Status: `VERIFYING`.
- Target: Code `2c47736` (implementation/remediation `a241c5f`, source import merge `e67fcad`).
- Code-reported result: `302 passed`; Windows build and clean extracted EXE launch passed. This is not yet independent approval.
- Completion: QA runs independent regression/safety/package checks, documents evidence in `reports/QA_REPORT.md`, commits PASS/FAIL, and names the exact verified target.
- Blocker: actual LD/game validation is not available; it must remain `NEEDS_REAL_TEST` even if MVP smoke passes.
- Next action: QA verification; no customer action pending.

## `v1.0.1` governed import and candidate build (2026-09-14)

- Task ID: `REL-UPDATE-003`
- Title: Import reviewed remote source tag into the Code branch
- Purpose: produce a testable, packageable candidate with safe per-account capture preflight before any customer release.
- Owner: existing Code now; existing QA after Code commit.
- Status: `IMPLEMENTING`.
- Planned changes: Code-selected application/GUI/test/build/handoff files required to integrate exact source tag `299e7a9` safely.
- Actual changes: none submitted yet.
- Completion: exact Code commit, full test and Windows-build evidence, artifact details, Code handoff; then QA independently validates exact target.
- Current result: Manager reviewed the tag and confirmed existing Code/QA terminals are connected.
- Blocker: none for Code integration; live LD/game validation remains separate `NEEDS_REAL_TEST`.
- Next action: Code imports/builds without publishing; Manager passes submitted hash to QA.

## `v1.0.1` import preflight (2026-09-14)

- Task ID: `REL-UPDATE-002`
- Title: Verify whether remote `v1.0.1` can replace the published macro
- Purpose: review the candidate update before any checkout, build, customer distribution, or release mutation.
- Owner: Manager performed read-only review; existing Code must import/build; existing QA must independently verify.
- Status: `BLOCKED`.
- Actual result: adds per-account capture/template readiness gating and developer-only calibration UI. It has no GitHub release, artifact, published checksum, signed annotated tag, Code handoff, or QA report.
- Completion: exact `v1.0.1` source is imported by Code, tests/build pass, QA validates its exact commit/artifact, and Manager publishes a truthfully labelled release.
- Blocker: existing Code/QA agents are unavailable in the current session; Manager cannot perform their implementation or verification roles.
- Next action: reactivate existing Code and QA only; no substitute agent/worktree and no customer-facing update before that gate.

## GitHub macro update inspection (2026-09-14)

- Task ID: `REL-UPDATE-001`
- Title: Identify the latest retrievable macro version
- Purpose: distinguish the published customer artifact from an unpublished newer source tag without changing existing project worktrees.
- Owner: Manager inspection only; existing Code and QA own any later integration/verification.
- Started: 2026-09-14 Asia/Seoul.
- Status: `BLOCKED` pending release/integration direction.
- Planned changes: no production or test-code changes.
- Actual changes: management records only; remote refs fetched read-only.
- Current result: release `v1.0.0` is published; `v1.0.1` is a newer source tag only and contains unverified preflight-related changes.
- Completion: user selects the published artifact or authorizes the governed Code/QA integration path for the newer source tag.
- Blocker: no verified release exists for `v1.0.1`; existing Code/QA agents are not active in the current coordinator session.
- Next action: user chooses which artifact they mean by “GitHub macro.”

## Live ADB connection checkpoint (2026-09-13)

- Task ID: `LIVE-ADB-001`
- Title: Safe real-environment connection preflight
- Purpose: enumerate live ADB devices and explicitly map LD1--LD9 before any automation input.
- Owner: Manager coordinates; user supplies/activates the local LDPlayer ADB bridge. Independent QA is required before any live-function PASS claim.
- Started: 2026-09-13 Asia/Seoul.
- Status: `BLOCKED`.
- Planned changes: no production-code or test-code changes.
- Actual changes: management records only.
- Completion: `adb devices` can be invoked by the released application; user explicitly maps serials in the GUI; each mapped account is displayed online. No Worker/touch is permitted during discovery.
- Current result: released `ldmanager.exe` is running, but Windows reports `adb` unavailable. No standard LD install path or registry install location was found by read-only probes.
- Blocker: coordinator PC has no LDPlayer/ADB by user confirmation; this is a real-customer-environment dependency, not an attempted local repair target.
- Next action: customer enables the per-instance ADB bridge, refreshes devices in the GUI, and captures the resulting mapping state before continuing.

## REL-0.1.0 corrected asset replacement (2026-09-12)

- Task ID: `REL-0.1.0-PKG-01`
- Status: `PUBLISHED_CORRECTED_MVP_PRERELEASE`.
- QA: `MVP_SMOKE_PASS`, report commit `2ff8ebf`; independent `286 passed` and fresh extracted EXE/config bootstrap verification passed.
- Release: `https://github.com/kpj0526/LDplayer/releases/tag/v0.1.0`.
- Asset: `ldmanager-v0.1.0-windows-fixed-20260912.zip`, 11,231,354 bytes, SHA-256 `126F4F085B53C24CDB76A6AC90FF9A7C7567F6509BC7EBD969120AE4B2FC3432`.
- Result: first uploaded ZIP was removed. Corrected archive bootstraps missing safe local configs on first launch and never overwrites an existing config.
- Next: real-user LD device mapping and real-game validation.

## REL-0.1.0-PKG-01 — first-run release packaging repair (2026-09-12)

- Task ID: `REL-0.1.0-PKG-01`
- Status: `REWORK`.
- Purpose: ensure an extracted Windows release contains safe default configs and opens its GUI without terminal/YAML setup.
- Owner: existing `code` repairs; existing `qa` independently validates corrected archive and built-EXE launch.
- Defect evidence: Manager inspected the first uploaded ZIP: it listed `ldmanager.exe` but no `configs/` or initial config files.
- Containment: GitHub release notes flag the first asset as unusable; it must not be downloaded until replacement.
- Completion: corrected build contains null-mapped/no-credential config and bounty config, preserves existing user configs, full tests pass, built EXE launch passes, QA commits `MVP_SMOKE_PASS`, then Manager replaces asset.
- Next action: Code repair/build/handoff.

## `v0.1.0` MVP prerelease publication (2026-09-12)

- Task ID: `REL-0.1.0`
- Status: `PUBLISHED_MVP_PRERELEASE`.
- Owner: Manager publication after existing QA release-gate verdict.
- Source: remote `mvp/v0.1.0` / tag `v0.1.0` at `120a55b933e5688ff688ee49213a300133d77e52`; Code implementation is included through `817183b` / `5b0862b`.
- QA gate: `MVP_SMOKE_PASS`, QA report `120a55b`; independent `266 passed` and focused `53 passed`.
- Asset: `ldmanager-v0.1.0-windows-20260912.zip`, 11,210,660 bytes, SHA-256 `A525FA85A50DAB51AE2AAF9E0DCEF805A54C3A631C341E85507F042070059726`.
- Release page: `https://github.com/kpj0526/LDplayer/releases/tag/v0.1.0`.
- Completion boundary: publication is complete; final project completion is not. Real LD/game validation remains required.
- Next action: customer maps real LD instances through the GUI and provides real-environment test evidence.

## UI-ADB-001 QA release gate (2026-09-12)

- Task ID: `UI-ADB-001`
- Status: `VERIFYING`.
- Code target: `817183be5a2241bb426a55942230de21dff8df98` (implementation `5b0862b`).
- Code evidence: full suite `266 passed`; Windows artifact `dist\\ldmanager\\ldmanager.exe` exists at 2,071,926 bytes.
- Owner: existing `qa` independently verifies; Manager holds GitHub publication.
- Completion: QA validates AC-61..AC-65, regression safety, and release-launch evidence, then records `MVP_SMOKE_PASS`, `MVP_SMOKE_FAIL`, or `BLOCKED_REAL_ENVIRONMENT`.
- Release boundary: do not push/tag/publish before the QA verdict; no real-game result may be claimed from mocked discovery/tests.
- Next action: QA submits a committed report; Manager publishes only a truthfully labelled MVP prerelease if passed.

## UI-ADB-001 — GUI-based LD registration (2026-09-12)

- Task ID: `UI-ADB-001`
- Title: Customer-friendly ADB mapping without terminal/YAML editing
- Purpose: let a customer refresh devices, explicitly assign each ADB serial to LD1..LD9, save it, and see mapping errors in the application.
- Owner: existing `code`; existing `qa` verifies after Code commits.
- Status: `IMPLEMENTING` (queued behind the active release build command).
- Planned files: Code-selected GUI/controller/config/discovery modules, tests, run guide, and Code handoff.
- Completion: AC-61..AC-65 implemented; Code self-tests and commits; QA independently verifies the exact commit. No auto-assignment, Worker start, or touch during registration.
- Current result: prior GUI can open but configuration requires local YAML; this request closes that customer-usability gap.
- Blocker: none for mock implementation; real device discovery and mapping still require later customer environment verification.
- Next action: Code reports build result then implements this packet; release remains on hold.

## Supplemental live GUI launch smoke (2026-09-12)

- Task ID: `MVP-001-CV-GUI-SMOKE`
- Title: Safe documented GUI launch without device actions
- Purpose: confirm the MVP opens and exits normally while preserving the no-device safety boundary.
- Owner: existing `qa` (independent execution); Manager reviewed the evidence.
- Status: `PASS` as supplemental launch evidence.
- Actual changed files: ignored QA-local `configs/config.yaml` and `configs/bounty.yaml` copied from examples; no production-code change.
- Completion result: `ldmanager (MVP)` opened at 738x600 via `scripts\\run.ps1`; all mappings were null; no worker/ADB input started; normal `WM_CLOSE` exited the GUI.
- Evidence: QA report commit `144a0f7d08d8034cdfa507c084da9abfa2c86cf1`.
- Blocker: actual LD/game automation remains untested because device mapping and calibrated game assets are unavailable.
- Next action: `NEEDS_REAL_TEST`; do not represent this as live game-cycle validation.

## MVP smoke result (2026-09-12)

- Task ID: `MVP-001-CV`
- Status: `MVP_SMOKE_PASS`.
- QA target/report: Code `c42289c` / implementation `6f32610`; QA `d8ed7bd` (integration `fa856f2`).
- Actual result: QA full suite `241 passed in 3.98s`; app/GUI construction subset `8 passed in 0.61s`; mandatory injected/mock safety and customer-video cycle smoke passed.
- Completion boundary: executable MVP draft smoke is complete. Actual customer LDPlayer/game validation is not complete.
- Blocker: customer assets, calibrated recognizers, real serial mapping, and live cycle/repeat/concurrency evidence.
- Next action: `NEEDS_REAL_TEST`; do not declare final project completion until real validation is performed.

## MVP-001-CV QA smoke handoff (2026-09-12)

- Task ID: `MVP-001-CV`
- Status: `MVP_VERIFYING`.
- Code target: `c42289c` (implementation `6f32610`; includes MVP base `ff6648d` / `f6af8ee`).
- Code self-test: `241 passed`; build script previously reported successful. This is not approval.
- Owner: existing `qa`.
- Completion: QA records only `MVP_SMOKE_PASS`, `MVP_SMOKE_FAIL`, or `BLOCKED_REAL_ENVIRONMENT`; no real-environment AC may be marked PASS without user evidence.
- Next action: QA independently performs required smoke/safety checks of the exact target.

## Activation update (2026-09-12)

- Task ID: `MVP-001-CV`
- Status: `MVP_IMPLEMENTING`.
- MVP-001 dependency is satisfied by Code `ff6648d` / `f6af8ee`; existing Code now implements the customer-video extension from that retained base.
- QA action: combined MVP smoke only after Code supplies the extension handoff hash.

## Current authoritative task (2026-09-12)

- Task ID: `MVP-001`
- Title: Connected executable MVP draft for nine-account mission automation
- Purpose: deliver a runnable, configurable end-to-end draft that can be calibrated and smoke-tested on the user's real environment later.
- Owner: existing `code`; existing `qa` conducts post-commit MVP smoke verification only.
- Started: 2026-09-12 Asia/Seoul.
- Status: `MVP_IMPLEMENTING`.
- Planned files: Code-selected application/GUI/worker/state-machine/configuration/template/ROI/coordinate/logging/test/script/documentation files plus Code handoff.
- Actual changed files: uncommitted in the Code worktree at audit: `src/ldmanager/coordinates.py`, `src/ldmanager/app.py`, `src/ldmanager/controller.py`, `src/ldmanager/gui.py`, `src/ldmanager/mission.py`, `src/ldmanager/mission_config.py`, `src/ldmanager/recognition.py`, `tests/fakes.py`, `tests/test_controller.py`, and `tests/test_mission.py`. No Code MVP commit/test handoff exists yet.
- Completion: committed runnable Python MVP, start/build scripts, GUI, config/template folders, bounded account-isolated mission-cycle state machine, tests for mandatory safety checks, run/capture-gap/untested documentation, and Code handoff. QA then supplies MVP smoke verdict only.
- Current result: Stage 4 foundation passed scope QA `d69bc0b`; actual LD/game testing remains absent.
- Blocker: real game images and user environment needed for calibration and real-result validation, not for a configurable MVP draft.
- Next action: Code implements MVP-001 without creating agents/worktrees; Manager sends exact committed hash to existing QA for smoke testing.

## Queued extension (2026-09-12)

- Task ID: `MVP-001-CV`
- Title: Customer-video free regional-bounty mission cycle
- Status: `QUEUED_AFTER_SAFE_UNIT`.
- Owner: existing `code`; QA verifies after committed Code submission.
- Dependency: Code must complete and commit its current MVP-001 safe unit first; no work is discarded.
- Scope: implement the reference-video five-slot refresh/accept/200-complete/reward/close/return/repeat state flow with configuration-based recognition placeholders and mandatory safety limits.
- Next action: Manager has queued the packet to Code; Code begins it after current commit and reports a new exact handoff hash.

## Current authoritative task (2026-09-12)

- Task ID: `TP-003`
- Title: Per-instance ADB screenshot and guarded relative-touch foundation
- Purpose: make later image recognition and mission automation capable of safely capturing and acting on exactly one explicitly mapped LDPlayer device.
- Owner: existing `qa` independently verifies the submitted Code target.
- Started: 2026-09-12 Asia/Seoul.
- Status: `IMPLEMENTING`.
- Planned files: Code-selected ADB/capture/control interfaces, configuration/model/test files, and Code's `docs/HANDOFF_CODE.md`.
- Actual changed files: Code committed `src/ldmanager/adb.py`, `src/ldmanager/coordinates.py`, `src/ldmanager/screenshot.py`, `src/ldmanager/guarded_touch.py`, related fake/test files, and `docs/HANDOFF_CODE.md` as `8b1687b` / `efd3a2f`.
- Completion: capture and guarded touch are parameterized to one nonblank explicit serial, use only LD-internal relative coordinates, require before/after screen verification hooks, bound failures/timeouts, preserve account-local errors, have fake-runner tests and a committed Code handoff; QA then performs complete TP-003 verification.
- Current result: TP-002-RW-01 Stage 3 scope PASS at QA `a3eb77f`; no actual device/game operation has been performed.
- Blocker: real screen templates, ROI calibration, actual ADB mapping, and game fixtures are later user-environment evidence needs; they do not block this injectable interface/test stage.
- Next action: existing QA independently validates exact target `efd3a2f`; a FAIL returns work to Code and a PASS automatically opens the next planned stage.

## Current authoritative task (2026-09-12)

- Task ID: `TP-002-RW-01`
- Title: Reject blank ADB serials at the complete-mapping boundary
- Purpose: repair the Major Stage 3 validation defect independently reproduced by QA.
- Owner: existing `qa` performs full re-verification of the submitted Code hash.
- Started: 2026-09-12 Asia/Seoul.
- Status: `REWORK`.
- Planned files: Code-selected mapping validator and regression tests; `docs/HANDOFF_CODE.md` in Code worktree.
- Actual changed files: Code committed `src/ldmanager/discovery.py`, `tests/test_discovery.py`, and `docs/HANDOFF_CODE.md` as `5ea24e3` / `a4dce6d`; Code worktree was clean at Manager handoff.
- Completion: blank and whitespace-only values are rejected by `validate_complete_adb_mapping()` and `ensure_complete_adb_mapping()`; direct QA reproduction passes; full Code suite passes; Code commits/handoffs; QA completes the full TP-002 scope with PASS.
- Current result: QA `356e730` found `BLANK_SERIAL_DIRECT_MAPPING_ERRORS=[]` for Code `c5b8961` and declared a Major Stage 3 scope FAIL.
- Blocker: no technical blocker for the narrowly scoped repair. Actual LDPlayer hardware/game validation remains later work.
- Next action: existing QA independently verifies exact Code HEAD `a4dce6d`; a FAIL returns work to Code and a PASS permits Stage 4 planning only.

## QA handoff (2026-09-12)

- Task ID: `TP-002`
- Status: `VERIFYING`
- Code target: `c5b8961` (implementation `ffaa3ec`)
- Code self-test: 98 passed, 0 failed; pending independent QA.
- Owner: existing `qa`.
- Completion: Stage 3 scope PASS only; actual LD integration and AC-30 remain unverified.

## Current authoritative task (2026-09-12)

- Task ID: `TP-002`
- Title: Stage 3 LD1-LD9 discovery and explicit ADB mapping
- Owner: existing `code`; QA owner after Code submission: existing `qa`.
- Status: `IMPLEMENTING`.
- Planned files: Code-selected ADB discovery/mapping/config/models/tests and `docs/HANDOFF_CODE.md`.
- Completion: Code commit and self-test; QA independently verifies the exact hash. Stage 3 scope PASS is required before Stage 4.
- Actual PC/LD validation: deliberately pending; AC-30 remains `NOT_TESTED`.

## QA session resumed (2026-09-12)

- Task ID: `TP-001-RW-03`
- Status: `VERIFYING`
- Existing QA session was reinitialized in the same existing QA worktree after its prior terminal exited.
- Target and acceptance conditions are unchanged: Code `9f54d24`; full independent Stage 2 re-verification; no sensitive marker in any logged message/argument/traceback path.

## QA verification handoff (2026-09-12)

- Task ID: `TP-001-RW-03`
- Status: `VERIFYING`
- Code target: `9f54d24` (repair `d8a6fcd`)
- Code evidence: 66 passing tests, verification pending.
- Owner: existing `qa` for full independent Stage 2 re-verification.
- Completion: QA scope PASS only; global project ACs remain `NOT_TESTED` unless separately established.

## Authoritative current task (2026-09-12)

- Task ID: `TP-001-RW-03`
- Title: traceback and exception-output secret redaction
- Owner: existing `code`; QA re-verification owner: existing `qa`.
- Status: `REWORK`.
- Evidence: QA `179a679252cda5adb4002b0ed341ea9089ed4881` against Code `1305ba5a8b629e77664566702fb3ffe04eb8ac5e`.
- Completion: controlled marker absent from `logger.exception()` error log, full Code tests pass, Code commit/handoff, QA full Stage 2 PASS.
- Next: deliver `TP-001-RW-03` to Code.

## Rework update (2026-09-12)

- Task ID: `TP-001-RW-02`
- Status: `REWORK`
- Current result: QA independent test of Code target `1305ba5` has reproduced a Critical secret leak through `logger.exception()` traceback output despite 64 passing tests.
- Next action: await QA report commit, then send Code a narrowly scoped corrective packet for traceback/exc_info redaction and regression coverage. QA must again re-run complete Stage 2 verification.

## QA verification handoff (2026-09-12)

- Task ID: `TP-001-RW-02`
- Current status: `VERIFYING`
- Implementer result: Code commits `1acf510` and `1305ba5`; Code reports 64 passing tests.
- Verification owner: existing `qa`.
- Exact target: `1305ba5` on `kpj0526/Code` (contains corrective implementation `1acf510`).
- Required result: independent PASS/FAIL report with commands, evidence, actual results, reproduction steps for any failure, and QA report commit.
- Next action: wait for QA; a FAIL returns work to Code, a PASS permits only Stage 3 planning/implementation.

## Current authoritative record (2026-09-12)

- Task ID: `TP-001-RW-02`
- Title: Stage 2 sensitive-log and generated-artifact corrective work
- Purpose: prevent credentials/secrets in account logs and prevent generated diagnostics/logs from accidental Git staging.
- Owner: existing `code`; Manager coordinates; existing `qa` re-verifies.
- Start: 2026-09-12 Asia/Seoul (following QA failure).
- Status: `REWORK`.
- Planned files: Code-selected logging implementation, `.gitignore`, regression tests; Code must report exact actual files.
- Actual files: none for this corrective task yet.
- Completion: no controlled sensitive marker in task/error output; generated artifacts ignored; full Code tests pass; Code commits; QA independently returns Stage 2 PASS.
- Current result: QA FAIL `5cba31e2d09b254166e4dbb79a5786be674e848e` for target `ba0e3da1228b70cd34a40e74a0f262212ed8310a`.
- Blocker: Critical secret persistence and non-ignored generated artifacts.
- Next: Manager delivers corrective Task Packet to `code`.

- 작업 ID: `TP-001`
- 작업 제목: 단계 2 — 설정 및 계정별 로그 시스템
- 작업 목적: 사용자 설정을 안전하게 관리하고 계정별 작업·오류 로그 및 진단 경로의 기반을 만든다.
- 담당 에이전트: qa (Manager 조정)
- 작업 시작 시각: 2026-09-12 (Asia/Seoul; 정확한 시각 미기록)
- 현재 상태: `VERIFYING`
- 변경 예정 파일: code worktree의 Python 프로젝트·테스트·설정 골격 (정확한 파일은 code 설계 후 제출)
- 실제 변경 파일: `AGENTS.md`, `docs/PROJECT_SPEC.md`, `docs/TASK_PACKET.md`, `docs/STATUS.md`, `docs/DECISIONS.md`, `docs/HANDOFF_CODE.md`, `docs/TEST_PLAN.md`, `docs/PROGRESS.md`, `docs/CURRENT_TASK.md`, `docs/WORK_LOG.md`, `docs/ACCEPTANCE_STATUS.md`, `reports/QA_REPORT.md`
- 완료 조건: 사용자가 `Task Packet 승인, 구현 시작`을 명시하고 필요한 화면 자료·기술 결정 사항을 확인한다.
- 현재 결과: 필수 관리 문서와 AC별 테스트 계획 작성 완료; 중단 후 상태 재확인 완료. 구현·QA 테스트는 미시작.
- 차단 요소: 화면 자료·ADB 매핑·기술 선택 미확정, 사용자 구현 승인 대기. Manager 문서는 미커밋 상태.
- 다음 행동: 사용자에게 중단 후 확인 결과를 보고하고 승인 대기.
