# MVP delivery mode override (2026-09-12)

- Current priority is an executable, configurable MVP draft—not final full-AC delivery.
- Only existing `Manager`, `code`, and `qa` worktrees/roles may be used. No agent, subagent, role, or worktree may be created.
- `code` implements the connected MVP flow in one packet and commits it; `qa` performs the required MVP smoke/safety suite after submission. This does not authorize a final project PASS claim.
- Mandatory safety: explicit ADB serial scope/no cross-account command; individual-stop isolation; no automatic input after global stop; bounded retries/timeouts/no infinite clicks; worker exception containment; program and GUI startup.
- Untested real LDPlayer/game work remains `NEEDS_REAL_TEST`, `NOT_TESTED`, or `BLOCKED_REAL_ENVIRONMENT`.

# LDplayer Manager 운영 규약

## 고정 역할과 작업공간

이 프로젝트는 이미 존재하는 다음 역할과 worktree만 사용한다. 신규 에이전트, 하위 에이전트, 역할, Git worktree 생성은 금지한다.

| 역할 | worktree | 브랜치 | 권한 |
| --- | --- | --- | --- |
| Manager | `C:/Users/User/orca/workspaces/LDplayer/Manager` | `kpj0526/Manager` | 요구사항·문서·조정·통합 |
| Code_edit (Code) | `C:/Users/User/orca/workspaces/LDplayer/Code` | `kpj0526/Code` | 프로그램·테스트 코드 구현 및 커밋 |
| QA (Qa) | `C:/Users/User/orca/workspaces/LDplayer/Qa` | `kpj0526/Qa` | 독립 검증 및 QA 보고서 |

Manager는 `src` 등 production code를 직접 변경하지 않는다. Code_edit와 QA는 하위 에이전트를 생성하지 않는다. Code_edit는 Manager의 승인된 Task Packet 없이 구현을 시작하지 않으며, QA는 Code_edit의 정확한 커밋을 독립 검증한다.

## 완료·통합 규칙

- 흐름: `USER → Manager 구조화 → Code_edit 구현 → QA 독립 검증 → Manager 판단`.
- QA FAIL 시 Manager가 실패를 정리하고 Code_edit 재작업 후 QA가 전체 재검증한다.
- QA 최종 PASS 전에는 완료·납품 가능 선언이나 기본 브랜치 통합을 하지 않는다.
- 통합 전제: Code_edit 완료, QA 전체 PASS, Critical/Major 미해결 0건, 문서와 구현 일치.
- 기존 사용자 파일·변경사항을 삭제하거나 파괴적 Git 명령을 실행하지 않는다.

## 문서 책임

Manager는 `docs/PROJECT_SPEC.md`, `docs/TASK_PACKET.md`, `docs/STATUS.md`, `docs/DECISIONS.md`, `docs/PROGRESS.md`, `docs/CURRENT_TASK.md`, `docs/WORK_LOG.md`, `docs/ACCEPTANCE_STATUS.md`를 사실에 따라 지속 갱신한다. Code_edit는 완료 시 `docs/HANDOFF_CODE.md`, QA는 검증 시 `reports/QA_REPORT.md`를 작성한다.
