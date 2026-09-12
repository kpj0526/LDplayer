# MVP smoke plan override (2026-09-12)

After MVP-001, QA prioritizes application and GUI startup; LD1-LD9 config loading; mock ADB serial/account separation; individual and global stop; no touch after global stop; one mock mission cycle; recognizer interface invocation; recognition/capture failure safety; bounded retry/timeout; and one worker exception not terminating the controller.

Long-duration/performance, exhaustive boundary, visual calibration, actual LDPlayer/game, clean-host packaging, and full AC tests are deferred as `NEEDS_REAL_TEST` or `BLOCKED_REAL_ENVIRONMENT`, never PASS.

## Customer-video test extension: AC-31..AC-60 (2026-09-12)

| AC range | Mock/automated verification | Real-environment requirement |
| --- | --- | --- |
| AC-31..AC-33 | Fixture-driven slot 1-5/selected-slot recognition contract and ordered state-machine traversal. | Confirm the five actual customer UI slots and ROI alignment. |
| AC-34..AC-37 | Refresh popup/detail recognition contract; confirm tap only after positive popup state; variable cost text ignored. | Screenshots/videos for popup at different costs and detail screen. |
| AC-38..AC-44 | Phrase + 200 joint recognizer result; non-target bounded reroll; target preservation; next slot only after accept; all-five gate. | Real Korean text/template/OCR calibration and five accepted missions. |
| AC-45..AC-48 | Progress classifier for 0-199 versus 200/completion; assert no complete/reward touch while incomplete; completion gate. | Actual progress and completion screen examples. |
| AC-49..AC-55 | Mocked guarded flow: complete → reward screen → claim → result → close → list return → refresh/reaccept/repeat. | One full customer-game cycle and repeat validation. |
| AC-56..AC-57 | Button/state disambiguation and one Worker exception isolation. | Confirm no look-alike controls cause action in the actual UI. |
| AC-58..AC-60 | Mock serial isolation and multi-worker smoke only. | Customer LD1-LD9 full flow, repeat, and no cross-click evidence. |

Required MVP smoke additions: variable refresh-cost fixture must not alter popup decision; phrase without 200 and 200 without phrase must reject; 0-199 cannot issue completion/reward; every action in one mock loop needs its preceding and following screen-state result. These tests do not replace actual customer footage/environment validation.

# TEST PLAN — TP-001

## 자동 테스트 우선

| 범주 | 검증 내용 | 관련 AC |
| --- | --- | --- |
| 인식 | 이미지 fixture 목표 문구 있음/없음, 낮은 신뢰도·잘못된 화면 거부 | AC-10~16, AC-23, AC-28 |
| 상태 | 상태 머신 전환, 최대 재시도, 타임아웃, 예외 격리 | AC-08, AC-14~16, AC-21, AC-23~24 |
| ADB | 모의 장치, 대상 serial 분리, 캡처·터치 대상 검증 | AC-01~02, AC-09 |
| Worker | 9개 동시 실행, 개별/전체 시작·정지, 안전 종료 | AC-03~08, AC-22, AC-27 |
| 운영 | 계정별 로그·진단 캡처, GUI 상태·오류, 설정 분리 | AC-25~26, AC-28 |

## 실제 사용자 PC 통합 테스트

LD1~LD9 탐색·ADB 매핑·독립 클릭·동시 실행·문구 인식·임무 변경/유지·5개 처리·200마리 완료·보상·초기화·반복·개별 정지/재시작·접속 종료 격리를 검증한다. 증거는 캡처·ADB/프로그램 로그·QA 보고서에 기록한다. AC-30은 실제 환경 전체 시나리오 통과 전 `NOT_TESTED` 또는 `BLOCKED`다.
