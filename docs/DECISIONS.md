# DECISIONS

## 2026-09-12 — Customer-video flow is MVP-required

- Decision: merge the supplied reference-video behavior into the existing MVP rather than defer refresh, acceptance, completion, reward, close, and re-refresh cycle.
- Reason: customer identifies that sequence as the required real operational behavior.
- Impact: old AC-01..AC-30 remain stable; 30 new continuous AC IDs AC-31..AC-60 track video-specific behavior. Concrete image values stay config/placeholder backed until customer assets exist.

## 2026-09-12 — MVP-first delivery mode

- Decision: replace remaining fine-grained stages with one connected, configurable MVP implementation packet.
- Reason: deadline pressure; immediate value is a runnable draft for later real LDPlayer/game calibration.
- Impact: QA does mandatory smoke/safety only. Full AC, long-running, performance, and real-environment validation remain deferred and cannot be final PASS.

## 2026-09-12 — TP-003 guarded device-control boundary

- Decision: Stage 4 must expose capture/touch only through an explicit per-account ADB serial and a guarded before/after screen-verification contract; unrestricted global mouse or device-default control is out of scope.
- Reason: the user requires no cross-account input, no global fixed-coordinate control, and safe stop/error behavior when expected screens cannot be verified.
- Impact: TP-003 automated tests must use injected runners and screen-verification fakes. Actual template/ROI calibration and live LDPlayer proof remain later user-environment tasks.

| 날짜 | 결정 | 이유 | 영향 범위 |
| --- | --- | --- | --- |
| 2026-09-12 | 관리·계획 문서만 작성하고 구현은 보류 | 사용자가 Task Packet 명시 승인을 구현 시작 조건으로 지정 | 전체 프로젝트 |
| 2026-09-12 | 웹 DOM 제어를 제외하고 이미지 인식/OCR/LD별 ADB를 후보로 유지 | 게임 화면 기반 자동화 요구사항 | 화면 인식·입력 계층 |
| 2026-09-12 | 계정별 독립 실행과 오류 격리를 필수 구조로 채택 | 한 계정 오류가 나머지를 중단하면 안 됨 | 동시성·상태 관리 |
| 2026-09-12 | Python·OpenCV·ADB 캡처/터치를 우선 기술 구조로 확정 | 사용자 1·2부 지시 | 전체 구현 |
| 2026-09-12 | AC 체계를 AC-01~AC-30으로 갱신 | 사용자 2부 지시 | 요구사항 추적·QA |

## 구현 전 미결정 사항

1. 목표 UI 프레임워크와 언어/런타임.
2. LD1~LD9 ADB serial/port의 실제 매핑 및 연결 검사 방식.
3. 지원 해상도, DPI/배율, 창 모드, 캡처 방식.
4. 토벌임무·변경·완료·보상·초기화·오류 화면의 기준 이미지, 허용 오차, OCR 사용 구간.
5. 클릭/재시도 제한, 타임아웃, 오류 상태 전이 및 로그 보존 정책.
6. 실제 200마리 완료 표시와 보상 수령 성공 표시의 판별 기준.
