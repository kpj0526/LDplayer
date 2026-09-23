# MVP delivery-mode addendum (2026-09-12)

Current delivery is an executable, configurable Windows MVP draft: LD1-LD9 mapping, workers/lifecycle, capture/recognition hooks, bounded mission-cycle state machine, status/log GUI, start/build scripts, configuration/template folders, and operator documentation. Placeholder templates and mocked ADB do not prove real-game success.

Real LDPlayer/game validation, pixel accuracy, long-duration/performance testing, clean-host packaging testing, and final AC-30 integration remain `NEEDS_REAL_TEST` or `BLOCKED_REAL_ENVIRONMENT`.

## Customer-friendly LD registration amendment (2026-09-12)

Customers must not need to edit YAML or use a terminal to register LD instances. The GUI shall show an explicit ADB-device registration area below every LD1..LD9 account panel: current mapping status, a user-selectable discovered-device serial, and a per-account save/clear action. A global **Refresh ADB devices** action shall display devices discovered by the configured ADB runner so the customer can choose a serial for each LD panel. Mapping remains an explicit user choice: the app must never guess which discovered device belongs to LD1..LD9, must reject duplicates/blank mappings, and must persist only the mapping/settings data locally. Worker start remains blocked for an unmapped or invalid account, with an understandable GUI error.

## Customer-video mission-cycle amendment (2026-09-12)

This is an addition to the existing MVP, not a replacement. For each independently mapped LD1-LD9 account, the MVP must cover the actual free regional-bounty flow shown in the customer reference: open mission list; select and inspect each of five slots; classify pending/completed/requires-refresh; refresh only when needed; identify the `지역 퀘스트를 갱신하시겠습니까?` confirmation popup by its structural screen state rather than refresh cost; click its confirm button only after a positive popup match; inspect new mission detail; accept and preserve only missions that jointly verify `모든 몬스터 처치` and quantity 200; otherwise boundedly refresh again; advance only after a slot is accepted; proceed to kill/reward flow only after all five are accepted.

For an accepted mission, 0-199/200 must remain in progress and must not trigger completion/reward input. Only 200/200 or an explicit completion indicator may select the mission and click completion. The flow then requires verified reward screen, reward claim, verified result screen, close result, verified return to mission list, refresh of the completed slot, acceptance of a new `모든 몬스터 처치 0/200` mission, and repetition.

Recognition objects are separate configurable targets: five slots/selected slot; refresh control; refresh confirmation/cancel; new detail; target phrase; `/200`; accept; progress count; completion indicator/control; reward screen/claim; reward result/close; and mission-list return. Prefer OpenCV template/ROI checks and use OCR only as corroboration. Never decide a click from one OCR result alone. Refresh-cost values (for example 4,400, 6,600, 9,900, 14,900) are not a screen-state criterion. All templates, ROIs, relative coordinates, thresholds, retries and timeouts are configuration data. Missing real assets remain placeholders and `NEEDS_REAL_TEST`, never fabricated success.

The per-account state machine includes `SELECTING_MISSION_SLOT`, `CHECKING_MISSION_STATUS`, `OPENING_REFRESH_CONFIRM`, `CONFIRMING_REFRESH`, `CHECKING_NEW_MISSION`, `ACCEPTING_TARGET_MISSION`, `REJECTING_NON_TARGET_MISSION`, `WAITING_KILL_PROGRESS`, `MISSION_COMPLETED`, `CLICKING_COMPLETE`, `OPENING_REWARD`, `CLAIMING_REWARD`, `CLOSING_REWARD_RESULT`, `RETURNING_TO_MISSION_LIST`, and `ERROR`. Every action follows capture → screen/condition verification → serial-scoped click → observed change. Unknown/low-confidence/stalled/disconnected/ended screens, exhausted retries, or timeout safely stop only that account.

# PROJECT SPEC — LDplayer 십이지천2M 토벌임무 자동화

## 목표 및 범위

Windows에서 LD플레이어 LD1~LD9를 각각 독립적인 Android ADB 장치로 제어하는 Python 기반 십이지천2M 토벌임무 자동화 프로그램을 제작한다. 동일한 화면·해상도·게임 설정의 9개 계정이 동시 동작하되, 시작·정지·오류·재시작과 입력 대상은 계정별로 격리된다.

각 계정은 임무 화면에서 슬롯 1~5를 순서대로 확인한다. `모든 몬스터 처치` 문구가 없는 슬롯만 확인창을 거쳐 제한된 재시도로 변경하고, 목표 임무는 유지한다. 보상 후 새로 나온 미션도 문구가 검증되면 초기 수치가 정확히 `0/200`이 아니어도 갱신하지 않는다. 완료된 목표 미션은 신규 수락/갱신 대신 보상 처리 경로로 보낸다. 실제 게임에서의 수치별 완료 판정은 고객 테스트가 필요하다.

GUI는 LD1~LD9 목록, 개별/전체 시작·정지, 연결 상태, 현재 단계·슬롯·목표 수·최근 결과·오류·로그 및 설정 저장/불러오기를 제공한다. 최종 산출물은 Windows 실행파일과 실행·화면 보정 설명서다.

## 기술 구조

- Python, OpenCV, 필요 시 OCR, ADB 캡처·터치, Windows 패키징.
- ADB 포트를 추측해 고정하지 않고 탐색 또는 사용자 지정 매핑을 사용한다.
- 계정별 Worker와 상태 머신, GUI/Worker 분리, 설정 파일, 계정별 로그.
- 입력 흐름: 대상 LD 캡처 → 화면/신뢰도 판별 → 대상 ADB에만 내부 상대좌표 터치 → 화면 변화 확인 → 다음 상태.
- 템플릿·ROI·좌표·임계값은 코드 밖 설정 파일에서 관리한다.

최소 상태: `STOPPED`, `CONNECTING`, `READY`, `OPENING_MISSION`, `CHECKING_SLOT`, `REROLLING`, `WAITING_RESULT`, `TARGET_CONFIRMED`, `MOVING_NEXT_SLOT`, `ALL_TARGETS_READY`, `WAITING_200_KILLS`, `CLAIMING_REWARD`, `RESETTING_MISSION`, `PAUSED`, `ERROR`.

## 안전 제약 및 제외 범위

- 웹 DOM 자동화, 전역 마우스 고정좌표 기본 제어, 게임 메모리 변조·패킷 조작·보안 우회는 금지한다.
- 낮은 인식 신뢰도·미등록 화면에서는 클릭하지 않으며, 모든 반복은 최대 재시도와 타임아웃을 적용한다.
- 오류 시 해당 계정의 로그와 진단 캡처를 남기고 다른 계정에는 영향이 없어야 한다.
- 자동 로그인·자동 재접속·재접속 후 자동 사냥터 이동은 제외한다. 사용자가 복구·사냥터 이동 후 해당 계정만 재시작한다.
- 계정정보·비밀번호·인증정보를 저장하거나 Git에 올리지 않는다.
- 실제 환경에서 확인하지 않은 기능은 성공으로 보고하지 않는다.

## 검증 원칙

실제 게임 전 fixture·모의 ADB 기반 자동 테스트를 먼저 수행한다. AC-30은 실제 사용자 PC의 LD1~LD9 통합 테스트 전 PASS가 될 수 없다. AC-01~AC-30의 상태는 `docs/ACCEPTANCE_STATUS.md`에서 관리한다.
