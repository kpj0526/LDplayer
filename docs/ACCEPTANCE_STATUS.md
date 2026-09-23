# Acceptance Status

## 기준

기존 AC-01~60은 번호를 유지한다. 고객 영상 요구사항 30개는 연속 번호 **AC-61~90**으로 추가했으며, 총 AC 수는 **90개**다. 코드 구조나 fake 테스트 통과는 실제 게임 검증 PASS가 아니다.

| 범위 | 수량 | 상태 |
| --- | ---: | --- |
| 기존 AC-01~30 | 30 | 기존 추적 문서의 상태 유지; 이 문서에서 재판정하지 않음 |
| 기존 AC-31~57 | 27 | fake 기반 상태 머신/격리 테스트 근거 있음, 실게임 PASS 아님 |
| 기존 AC-58~60 | 3 | `BLOCKED_REAL_ENVIRONMENT` |
| 신규 AC-61~90 | 30 | 미구현 또는 실제 화면 자료·실환경 검증 대기 |

현재 고객 영상 확장 범위의 최종 PASS는 **0/30**, 전체 최종 PASS는 **선언 불가**다. 완료율을 숫자 PASS로 표시하지 않으며, 실제 화면을 이용한 검증 전에는 0%로 취급한다.

## 신규 AC 추적

| AC | 기준 | 상태 |
| --- | --- | --- |
| 61~63 | 슬롯 5개/선택 상태/순차 처리 | 코드 골격 있음, 실제 인식 미구현 |
| 64~66 | 갱신 팝업·확인 게이트·가변 비용 | 구조/fake 검증만, 실제 인식 미구현 |
| 67~74 | 새 임무·문구+200·비목표 거부·제한 재갱신·슬롯 유지·5개 완료 | 구조/fake 검증만, 실제 인식 미구현 |
| 75~78 | 진행 상태·입력 금지·완료 상태·완료 탭 | 구조/fake 검증만, 실제 인식 미구현 |
| 79~86 | 보상 확인/수령/결과/닫기/목록 복귀/재갱신/반복/버튼 구분 | 구조/fake 검증만, 실제 인식 미구현 |
| 87 | 계정 오류 격리 | 자동 테스트 근거 있음, 실환경 미검증 |
| 88~90 | 실제 전체 흐름·반복·LD1~LD9 입력 격리 | `BLOCKED_REAL_ENVIRONMENT` |

AC-61~90의 정확한 고객 문구는 전달된 Packet의 AC-01~30과 각각 순서대로 대응한다.

## Customer revised requirement trace (2026-09-14)

| Requirement | QA status | Evidence / remaining condition |
| --- | --- | --- |
| Five independent slots; target-only acceptance | SIMULATED_PASS | Per-slot cycle and exact combined target template path are implemented; target reference frame `013.png` matches at 0.969 in the OpenCV smoke check. |
| Keep confirmed slots; progress only after all five | PARTIAL | Within one configuration pass accepted slots advance correctly. Persistence across a worker's later `KILL_PROGRESS_NOT_COMPLETE` cycle is not yet implemented. |
| Non-target refresh without arbitrary production limit | IMPLEMENTED | Production template-map mode retries until Stop or an error; legacy empty-map fixtures retain bounded retry only for test compatibility. |
| Recognition/ADB/stall/change errors stop only that account | PARTIAL | Recognition and ADB failures are account-local. Explicit screenshot-delta/stall detection is not implemented. |
| Completion → claim → close → rebuild loop | SIMULATED_PASS | State machine has the sequence and Worker repeats cycles. Real UI timing remains `NEEDS_REAL_TEST`. |
| Variable refresh cost, image-center tap | IMPLEMENTED | Four whole-button variants are OR-searched; amount is not read. Common button/icon calibration for unseen prices remains `NEEDS_REAL_TEST`. |
| LD1~LD9 isolation and Start/Stop | SIMULATED_PASS | Independent workers, serial-scoped ADB argv, and controller tests. Real nine-instance run is `NEEDS_REAL_TEST`. |
| GUI phase/slot count/action/score/error screenshot | FAIL | GUI currently exposes worker status/error/log and capture test, but not all requested structured diagnostics. |
| No reconnect; user restarts one account | SIMULATED_PASS | No reconnect code exists; worker error is contained and account Start is individual. |
| Duplicate Start / Stop prevents later click | SIMULATED_PASS | Worker start is idempotent and stop checks occur before touch. |

No row labelled `NEEDS_REAL_TEST` or `PARTIAL` is a customer completion claim.

## Core-runtime QA update

| Requirement | Implementation | Test | QA |
| --- | --- | --- | --- |
| Per-account slot states and explicit reset | `runtime.AccountMissionRuntime`, `SlotState` | `test_runtime_slots_are_independent_and_reset_only_when_explicit` | PASS |
| Target lock survives cycle and skips locked slots | `bounty_mission.run_one_cycle(runtime=...)` | existing bounty-cycle regression + runtime state test | PASS (simulated) |
| No target refresh count in production template mode | `_accept_or_refresh_slot` production loop | existing bounded legacy-fixture regression | PASS (simulated) |
| Click expected-state / stale / stop verification | `runtime.click_and_verify` | `test_click_and_verify_*` | PASS |
| Error screenshot artifact | `runtime.click_and_verify` | `test_click_and_verify_saves_stale_screen` | PASS |
| Account-local fatal Worker stop | `controller.AccountWorker._loop` | controller isolation regression | PASS (simulated) |
| GUI phase / locked count / slot states / error | `controller.AccountWorkerStatus`, `gui.AccountPanel.refresh` | GUI snapshot regression | PASS (simulated) |

Remaining `NEEDS_REAL_TEST`: actual LDPlayer serials, customer resolution thresholds, real game transitions, `/200` completion timing, and long-running LD1~LD9 stability.
