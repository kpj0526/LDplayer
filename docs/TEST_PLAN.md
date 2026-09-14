# MVP smoke plan override (2026-09-12)

## Customer remote-environment validation checklist: `v1.0.1` (2026-09-14)

Record a screenshot and relevant account log after every failed checkpoint. Do not treat prior mock results as real-environment PASS.

| Order | Safe test | Pass evidence | Stop / capture evidence instead |
| --- | --- | --- | --- |
| 1 | Set identical LD display/DPI/orientation; enable ADB debugging; start LD1 only. | LD1 is logged in and manually placed at intended mission screen. | Different setting, login/connection screen, frozen LD, or unavailable ADB debug. |
| 2 | Launch extracted `ldmanager.exe`; click **Refresh ADB devices**. | Device list appears with no global error. | Capture GUI error, especially missing `adb.exe`/no devices. Never guess a port. |
| 3 | Explicitly save LD1 serial and refresh again. | LD1 shows mapping `OK`; LD2--LD9 unchanged. | Duplicate/offline/error mapping: capture panel; do not Start. |
| 4 | Click LD1 **Test capture** at a supported mission anchor. | LD1 preflight recognizes screen; only LD1 becomes eligible. | Retain diagnostic capture path/file and LD1 log; do not Start or guess calibration. |
| 5 | Repeat mapping/Test capture one account at a time. | Each account becomes ready independently. | Any cross-account change/wrong serial/unexpected screen: Stop All and retain evidence. |
| 6 | Confirm normal/default launch is safe before live authorization. | Refresh/save/Test capture do not send game input. | Any input: Stop All immediately; preserve logs/captures. |
| 7 | Only after prior evidence review, observe one controlled LD1 live mission cycle. | LD1-only clicks, expected post-screen change, safe low-confidence/unknown stop. | Wrong target/stall/repeat click/disconnect: stop LD1, retain evidence. |
| 8 | Validate in order: phrase + `/200`; five-slot gate; 0--199 no completion; 200/200 complete → reward → close → return → refresh. | Recording/captures/log per reached state. | Wrong acceptance/click before 200/missing postcondition/retry error: stop LD1. |
| 9 | Then test LD1 Stop/restart, LD1+LD2, and all mapped accounts. | LD1 stop/error leaves others alive; Stop All leaves no later input. | Cross-click/residual input: Stop All and collect account logs. |

Required return evidence: mapping/error screenshots; `diagnostics/captures/LDx/` failed/unknown images; relevant `logs/`; first controlled LD1 recording; LDPlayer version plus display/DPI/ADB settings.

Safety: `v1.0.1` is QA smoke-tested, not real-game verified. Default safe mode blocks inner ADB tap dispatch until a deployment operator deliberately enables live mode. Do not enable live input or run a mission loop before the mapping/capture evidence is retained.

## UI-ADB-001 test extension: AC-61..AC-65

| AC | Automated/GUI verification | Required safety evidence |
| --- | --- | --- |
| AC-61 | Construct GUI and verify all LD1..LD9 panels expose mapping state plus editable/selectable serial control. | No terminal/YAML edit needed in the tested user path. |
| AC-62 | Fake ADB discovery populates available serial choices only. | No automatic assignment and no ADB touch command. |
| AC-63 | Save valid nine-unique mapping to isolated temporary config, reload it, and verify panel values. | Existing config remains valid/compatible. |
| AC-64 | Blank, duplicate, missing/offline, and malformed serial cases present an account-local visible error and reject start. | No mapping overwrite or Worker start. |
| AC-65 | Probe refresh/save with fake runner and assert zero touch/Worker actions; change LD1 then verify LD2 mapping remains unchanged. | Every discovery/control call carries an explicit target serial when applicable. |

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
