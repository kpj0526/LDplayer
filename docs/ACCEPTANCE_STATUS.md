# ACCEPTANCE STATUS

## UI-ADB-001 extension (2026-09-12)

Total ACs: `65`. The addition is planned only; implementation and QA counts remain unchanged until an exact Code commit and independent QA evidence exist.

| AC ID | Verification item | Implementation status | QA status | Evidence | Note |
| ----- | ----- | ----- | ----- | -- | -- |
| AC-61 | Per-LD GUI mapping state and explicit selection/entry | NOT_STARTED | NOT_TESTED | None | Customer-friendly registration |
| AC-62 | Discover devices without automatic assignment | NOT_STARTED | NOT_TESTED | None | Explicit customer choice only |
| AC-63 | Persist and reload a valid unique local mapping | NOT_STARTED | NOT_TESTED | None | Ignored local config only |
| AC-64 | Reject invalid mapping with visible account-local error | NOT_STARTED | NOT_TESTED | None | Must block account start |
| AC-65 | Registration has no Worker/touch side effects or cross-account change | NOT_STARTED | NOT_TESTED | None | Mandatory safety regression |

UI-ADB-001 submission override: AC-61..AC-65 are `IMPLEMENTED` at Code `5b0862b` / `817183b`, pending independent QA. Global final QA remains `0/65`.

## MVP-001-CV smoke-result override (2026-09-12)

| AC range | MVP status | Smoke status | Global QA status | Real environment status | Evidence |
| --- | --- | --- | --- | --- | --- |
| AC-01..AC-57 (implemented mock scope) | MVP_IMPLEMENTED | MVP_SMOKE_PASS | NOT_TESTED | NEEDS_REAL_TEST | Code `c42289c`; QA `d8ed7bd` |
| AC-58..AC-60 | NEEDS_REAL_TEST | BLOCKED_REAL_ENVIRONMENT | BLOCKED | BLOCKED_REAL_ENVIRONMENT | QA `d8ed7bd`; customer assets/environment absent |

Total ACs: `60`. Global final QA verification/PASS is still `0/60`; global BLOCKED is `3/60`. `MVP_SMOKE_PASS` verifies the injected/mock draft only and is not converted to global PASS.

## MVP-001-CV Code-submission override (2026-09-12)

| AC range | Implementation status | QA status | Evidence | Note |
| --- | --- | --- | --- | --- |
| AC-31..AC-57 | IMPLEMENTED | NOT_TESTED | Code `6f32610` / `c42289c`; Code self-test `241 passed` | Fixture/configurable implementation submitted; pending independent MVP smoke. |
| AC-58..AC-60 | BLOCKED | BLOCKED | No real customer LD/game assets or environment | Actual full flow/repeat/nine-instance evidence required. |

Total ACs: `60`. Conservative recorded implementation count: `31/60`; global final QA verification: `0/60`; global PASS: `0/60`; global FAIL: `0/60`; global BLOCKED: `3/60`. The new `IMPLEMENTED` label means committed draft code exists, not a final or real-environment success.

## Customer-video Acceptance Criteria extension (2026-09-12)

| AC ID | Verification item | Implementation status | QA status | Evidence | Note |
| ----- | ----- | ----- | ----- | -- | -- |
| AC-31 | Distinguish five free-bounty mission slots | NOT_STARTED | NOT_TESTED | None | NEEDS_REAL_TEST |
| AC-32 | Identify selected mission slot | NOT_STARTED | NOT_TESTED | None | NEEDS_REAL_TEST |
| AC-33 | Process slots 1 through 5 in order | NOT_STARTED | NOT_TESTED | None | |
| AC-34 | Identify refresh confirmation popup | NOT_STARTED | NOT_TESTED | None | NEEDS_REAL_TEST |
| AC-35 | Confirm only verified refresh popup | NOT_STARTED | NOT_TESTED | None | |
| AC-36 | Recognize popup independent of refresh cost | NOT_STARTED | NOT_TESTED | None | |
| AC-37 | Identify new-mission detail | NOT_STARTED | NOT_TESTED | None | NEEDS_REAL_TEST |
| AC-38 | Identify target phrase | NOT_STARTED | NOT_TESTED | None | NEEDS_REAL_TEST |
| AC-39 | Verify target quantity is 200 | NOT_STARTED | NOT_TESTED | None | NEEDS_REAL_TEST |
| AC-40 | Do not accept non-target mission | NOT_STARTED | NOT_TESTED | None | |
| AC-41 | Bounded reroll until target | NOT_STARTED | NOT_TESTED | None | |
| AC-42 | Preserve target slot without reroll | NOT_STARTED | NOT_TESTED | None | |
| AC-43 | Advance only after current acceptance | NOT_STARTED | NOT_TESTED | None | |
| AC-44 | End refresh only after all five targets | NOT_STARTED | NOT_TESTED | None | |
| AC-45 | Classify 0-199/200 as in progress | NOT_STARTED | NOT_TESTED | None | NEEDS_REAL_TEST |
| AC-46 | Never complete/reward while in progress | NOT_STARTED | NOT_TESTED | None | |
| AC-47 | Identify 200/200 or completion state | NOT_STARTED | NOT_TESTED | None | NEEDS_REAL_TEST |
| AC-48 | Click completion only when complete | NOT_STARTED | NOT_TESTED | None | |
| AC-49 | Verify reward screen after completion | NOT_STARTED | NOT_TESTED | None | NEEDS_REAL_TEST |
| AC-50 | Claim reward on reward screen | NOT_STARTED | NOT_TESTED | None | |
| AC-51 | Verify reward result screen | NOT_STARTED | NOT_TESTED | None | NEEDS_REAL_TEST |
| AC-52 | Close only verified reward result | NOT_STARTED | NOT_TESTED | None | |
| AC-53 | Verify return to mission list | NOT_STARTED | NOT_TESTED | None | NEEDS_REAL_TEST |
| AC-54 | Refresh completed mission again | NOT_STARTED | NOT_TESTED | None | |
| AC-55 | Accept new target and repeat | NOT_STARTED | NOT_TESTED | None | |
| AC-56 | Distinguish confirm/complete/claim/close by screen | NOT_STARTED | NOT_TESTED | None | |
| AC-57 | One account error does not halt another | NOT_STARTED | NOT_TESTED | None | Existing foundation needs MVP flow proof. |
| AC-58 | Complete one whole flow on customer screen | NOT_STARTED | NOT_TESTED | None | BLOCKED_REAL_ENVIRONMENT |
| AC-59 | Verify completed/reward/reroll repeat on customer screen | NOT_STARTED | NOT_TESTED | None | BLOCKED_REAL_ENVIRONMENT |
| AC-60 | No cross-account click during LD1-LD9 concurrency | NOT_STARTED | NOT_TESTED | None | BLOCKED_REAL_ENVIRONMENT |

Total ACs: `60`. Strict committed implementation: `4/60`; global final QA verification: `0/60`; global PASS: `0/60`; global FAIL: `0/60`; global BLOCKED: `0/60`. Customer-video AC-31..AC-60 are not started at this record.

## MVP mode tracking (2026-09-12)

| Deliverable area | MVP status | Smoke status | Real environment status | Evidence | Note |
| --- | --- | --- | --- | --- | --- |
| Explicit LD1-LD9 mapping | MVP_IMPLEMENTED | NOT_TESTED | NEEDS_REAL_TEST | Code `a4dce6d`; QA scope `a3eb77f` | Faked/injected evidence only. |
| Serial-scoped capture/guarded touch | MVP_IMPLEMENTED | NOT_TESTED | NEEDS_REAL_TEST | Code `efd3a2f`; QA scope `d69bc0b` | Foundation only; no live LD device. |
| Connected worker/GUI/mission MVP | IN_PROGRESS | NOT_TESTED | NEEDS_REAL_TEST | `MVP-001` assigned | No completion assertion before Code commit and smoke test. |

## Stage 3 scope PASS / Stage 4 start override (2026-09-12)

| AC ID | Verification item | Implementation status | QA status | Evidence | Note |
| ----- | ----- | ----- | ----- | -- | -- |
| AC-01 | LD1-LD9 identification | IMPLEMENTED | NOT_TESTED | Code `a4dce6d`; QA scope PASS `a3eb77f` | Automated mapping foundation only; real LD identification remains unverified. |
| AC-02 | Exact ADB-device mapping | IMPLEMENTED | NOT_TESTED | Code `a4dce6d`; QA scope PASS `a3eb77f` | Explicit nonblank mapping validation and target scope passed in fakes only. |
| AC-09 | Per-account command isolation | IN_PROGRESS | NOT_TESTED | QA `a3eb77f` explicit one-serial command probe | Capture/touch path remains TP-003 work. |

Implementation complete: `3/30`; QA verification complete: `0/30`; PASS: `0`; FAIL: `0`; BLOCKED: `0`. Global QA totals do not convert scope-level fake-runner validation into actual project-AC PASS.

## TP-002-RW-01 override (2026-09-12)

| AC ID | Verification item | Implementation status | QA status | Evidence | Note |
| ----- | ----- | ----- | ----- | -- | -- |
| AC-01 | LD1-LD9 identification | IN_PROGRESS | NOT_TESTED | Code `c5b8961`; QA `356e730` | Stage 3 scope failed before actual-device project verification. |
| AC-02 | Exact ADB-device mapping | BLOCKED | NOT_TESTED | QA `356e730`: blank serial validation defect | Repair must reject blank/whitespace serials at validation boundary. |
| AC-09 | Per-account command isolation | IN_PROGRESS | NOT_TESTED | QA `356e730` serial argv probe passed | Full touch/click isolation is still a later stage. |

Implementation complete: `1/30`; QA verification complete: `0/30`; PASS: `0`; FAIL: `0`; BLOCKED: `0`. These are global project-AC totals; the Major result is a Stage 3 scope failure, not a global QA AC verdict.

## Status audit override (2026-09-12)

| AC ID | Verification item | Implementation status | QA status | Evidence | Note |
| ----- | ----- | ----- | ----- | -- | -- |
| AC-26 | Account work/error logging | IMPLEMENTED | NOT_TESTED | Code `9f54d24`; QA Stage 2 scope PASS `2529a1a` | Scope tested; global project-AC status remains NOT_TESTED until full project traceability is complete. |

Implementation complete: `1/30`; QA verification complete: `0/30`; PASS: `0`; FAIL: `0`; BLOCKED: `0`.

## Stage 3 update (2026-09-12)

| AC ID | Verification item | Implementation status | QA status | Evidence | Note |
| ----- | ----- | ----- | ----- | -- | -- |
| AC-01 | LD1-LD9 identification | IN_PROGRESS | NOT_TESTED | TP-002 assigned to Code | Actual LD environment remains untested. |
| AC-02 | Exact ADB-device mapping | IN_PROGRESS | NOT_TESTED | TP-002 assigned to Code | No port guessing permitted. |
| AC-09 | Per-account command isolation | IN_PROGRESS | NOT_TESTED | TP-002 automated target-isolation scope | Full click isolation waits for later capture/touch stages. |

## Latest status override (2026-09-12)

| AC ID | Verification item | Implementation status | QA status | Evidence | Note |
| ----- | ----- | ----- | ----- | -- | -- |
| AC-26 | Account work/error logging | BLOCKED | FAIL | QA `5cba31e`: controlled password marker persisted; generated artifacts unignored | `TP-001-RW-02` required; global project-AC completion still not counted. |

Implementation complete: `0/30`; QA verification complete: `0/30`; PASS: `0`; FAIL: `0`; BLOCKED: `0`. The table above records a Stage 2 scope failure, not a completed project-AC result.

진행률: 구현 완료 0/30 · QA 검증 완료 0/30 · PASS 0 · FAIL 0 · BLOCKED 0

| AC ID | 검증 항목 | 구현 상태 | QA 상태 | 증거 | 비고 |
| ----- | ----- | ----- | ----- | -- | -- |
| AC-01 | LD1~LD9 식별 | IN_PROGRESS | NOT_TESTED | Code commit 28dd160: LD1~LD9 도메인 모델 | 실제 식별 미구현 |
| AC-02 | 정확한 ADB 장치 매핑 | IN_PROGRESS | NOT_TESTED | Code commit 28dd160: 사용자 매핑 설정 골격 | 실제 ADB 연결 미구현 |
| AC-03 | 9개 계정 동시 실행 | NOT_STARTED | NOT_TESTED | 없음 | |
| AC-04 | 계정별 개별 시작 | NOT_STARTED | NOT_TESTED | 없음 | |
| AC-05 | 계정별 개별 정지 | NOT_STARTED | NOT_TESTED | 없음 | |
| AC-06 | 전체 시작·정지 | NOT_STARTED | NOT_TESTED | 없음 | |
| AC-07 | 정지의 계정 간 독립성 | NOT_STARTED | NOT_TESTED | 없음 | |
| AC-08 | 오류의 계정 간 격리 | NOT_STARTED | NOT_TESTED | 없음 | |
| AC-09 | 클릭 대상 격리 | NOT_STARTED | NOT_TESTED | 없음 | |
| AC-10 | 계정별 임무 5개 확인 | NOT_STARTED | NOT_TESTED | 없음 | |
| AC-11 | 목표 문구 인식 | NOT_STARTED | NOT_TESTED | 없음 | |
| AC-12 | 비목표 임무만 변경 | NOT_STARTED | NOT_TESTED | 없음 | |
| AC-13 | 목표 임무 유지 | NOT_STARTED | NOT_TESTED | 없음 | |
| AC-14 | 제한 재시도 변경 | NOT_STARTED | NOT_TESTED | 없음 | |
| AC-15 | 확정 후 다음 임무 이동 | NOT_STARTED | NOT_TESTED | 없음 | |
| AC-16 | 5개 확정 후 다음 단계 | NOT_STARTED | NOT_TESTED | 없음 | |
| AC-17 | 200마리 완료 인식 | NOT_STARTED | NOT_TESTED | 없음 | |
| AC-18 | 보상 수령 | NOT_STARTED | NOT_TESTED | 없음 | |
| AC-19 | 보상 후 임무 초기화 | NOT_STARTED | NOT_TESTED | 없음 | |
| AC-20 | 초기화 후 반복 | NOT_STARTED | NOT_TESTED | 없음 | |
| AC-21 | 접속 종료 계정 오류 처리 | NOT_STARTED | NOT_TESTED | 없음 | |
| AC-22 | 복구 계정 개별 재시작 | NOT_STARTED | NOT_TESTED | 없음 | |
| AC-23 | 예상 화면 무한 클릭 방지 | NOT_STARTED | NOT_TESTED | 없음 | |
| AC-24 | 최대 재시도·타임아웃 | NOT_STARTED | NOT_TESTED | 없음 | |
| AC-25 | GUI 상태·오류 표시 | NOT_STARTED | NOT_TESTED | 없음 | |
| AC-26 | 계정별 실행·오류 로그 | NOT_STARTED | NOT_TESTED | 없음 | |
| AC-27 | 전체 정지 후 입력 없음 | NOT_STARTED | NOT_TESTED | 없음 | |
| AC-28 | 이미지 템플릿·설정 코드 분리 | IN_PROGRESS | NOT_TESTED | Code commit 28dd160: 설정 로딩·ADB 매핑 분리 | 이미지/ROI는 후속 단계 |
| AC-29 | Windows 실행파일 패키징 | NOT_STARTED | NOT_TESTED | 없음 | |
| AC-30 | 실제 LD1~LD9 통합 테스트 | NOT_STARTED | NOT_TESTED | 없음 | 실제 사용자 PC 필요 |
