# HANDOFF — Code worktree

각 단계는 아래에 절을 추가하는 방식으로 기록합니다(과거 절은 수정하지 않음).

## TP-001 stage 1: 프로젝트 기본 구조

**상태: 부분 구현 (stage 1 범위 한정). 최종 PASS/병합 선언 아님 — QA 확인 필요.**

### 구현 AC

| AC | 구현 여부 | 비고 |
|---|---|---|
| Python 패키지 구조 (이후 단계가 확장 가능한 형태) | 구현 | `src/ldmanager/` (`__init__.py`, `models.py`, `config.py`, `cli.py`), `pyproject.toml` (src-layout, setuptools) |
| 설정 파일 경로/로딩 골격 | 구현 | `ldmanager.config`: `resolve_config_path()` (명시 인자 > `LDMANAGER_CONFIG` 환경변수 > `./configs/config.yaml` 기본값), `load_config()` (YAML 로드 + 검증, 실패 시 조용히 넘어가지 않고 `ConfigError`) |
| ADB 매핑 자리표시자 (포트 추측/고정 금지) | 구현 | `configs/config.example.yaml`: LD1~LD9 전부 `null`. `validate_adb_mapping()`은 알 수 없는 키를 거부하고, 누락된 키는 추측값이 아닌 `None`으로 채움 |
| 계정 LD1~LD9 도메인 모델 / 상태 enum 최소 골격 | 구현 | `AccountId`(LD1..LD9), `AccountState`(UNKNOWN/OFFLINE/STARTING/ONLINE/BUSY/ERROR/STOPPING, 기본값 UNKNOWN), `Account` dataclass, `create_default_accounts()` |
| 테스트 실행 구조 | 구현 | `pytest` 기반, `tests/test_models.py`, `tests/test_config.py` (총 11개) |
| README 실행 안내 | 구현 | 설치/설정/테스트/골격 CLI 실행법 기술 |
| 안전 기본값 | 구현 | 모든 계정 기본 상태 `UNKNOWN`, `adb_serial=None`; 설정 파일 없으면 자동 생성/추측 없이 에러로 안내 |
| 실제 LD/게임 조작, 자격증명 처리, 웹 DOM, 전역 마우스 제어 | **미구현 (의도적, 범위 제외)** | 이번 단계 지시에 따라 구현하지 않음. `cli.py`는 설정을 읽고 계정 상태를 출력만 하는 정보성 골격 |
| 신규 에이전트/하위 에이전트/worktree/역할 생성 | **미수행 (의도적)** | 지시에 따라 생성하지 않음 |
| Manager 문서 수정 | **미수행 (의도적)** | Code worktree의 프로그램/테스트/설정 골격만 변경 |

### 변경 파일

```
 .gitignore                       (신규)
 README.md                        (수정)
 pyproject.toml                   (신규)
 configs/config.example.yaml      (신규)
 src/ldmanager/__init__.py        (신규)
 src/ldmanager/cli.py             (신규)
 src/ldmanager/config.py          (신규)
 src/ldmanager/models.py          (신규)
 tests/__init__.py                (신규)
 tests/test_config.py             (신규)
 tests/test_models.py             (신규)
 docs/HANDOFF_CODE.md             (신규, 본 문서)
```

### 실행 환경 참고

- 본 worktree(`C:\Users\User\orca\workspaces\LDplayer\Code`)에는 시작 시점에
  실제 Python 인터프리터가 없었음(Windows Store 스텁만 존재). 사용자 승인 하에
  `winget install --id Python.Python.3.12`로 Python 3.12.10을 설치한 뒤
  `.venv`를 만들어 테스트를 실행함. QA 환경에도 Python 3.10+ 인터프리터가
  준비되어 있는지 별도 확인 필요.

### 테스트 명령 / 결과

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m pytest -v
```

결과:

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
collected 11 items

tests/test_config.py::test_resolve_config_path_explicit_wins PASSED      [  9%]
tests/test_config.py::test_resolve_config_path_env_var PASSED            [ 18%]
tests/test_config.py::test_resolve_config_path_default PASSED            [ 27%]
tests/test_config.py::test_missing_config_file_raises_clear_error PASSED [ 36%]
tests/test_config.py::test_example_config_loads_with_all_placeholders_none PASSED [ 45%]
tests/test_config.py::test_validate_adb_mapping_rejects_unknown_key PASSED [ 54%]
tests/test_config.py::test_validate_adb_mapping_rejects_bad_value_type PASSED [ 63%]
tests/test_config.py::test_validate_adb_mapping_fills_missing_keys_as_none PASSED [ 72%]
tests/test_models.py::test_account_ids_cover_ld1_to_ld9 PASSED           [ 81%]
tests/test_models.py::test_account_default_state_is_unknown PASSED       [ 90%]
tests/test_models.py::test_create_default_accounts_has_nine_entries_all_unknown PASSED [100%]

============================= 11 passed in 0.20s ==============================
```

추가로 `python -m ldmanager.cli`를 설정 파일 없이 수동 실행하여, 자동 생성/추측
없이 명확한 에러 안내와 함께 LD1~LD9 기본 레지스트리(전부 `UNKNOWN`,
`adb_serial=None`)가 출력됨을 육안으로 확인함.

### 커밋 해시

- `4fada03` — "TP-001 stage 1: ldmanager project skeleton" (브랜치 `kpj0526/Code`)
- 본 문서 자체는 후속 커밋으로 추가됨 (아래 커밋 로그 참조).

### 제한사항 (Limitations)

1. **자동화 없음**: LDPlayer 제어, 게임 조작, ADB 실연결, 웹 DOM 조작, 전역 마우스
   제어 등은 전혀 구현되어 있지 않음 — 이번 단계 지시상 의도된 제외.
2. **ADB 매핑 미채움**: `configs/config.example.yaml`의 모든 값은 `null`.
   실제 사용 전 사용자가 `configs/config.yaml`을 만들어 직접 채워야 함(추측 없음).
3. **CLI는 정보 출력용**: `ldmanager.cli`는 인수 파싱조차 없는 최소 골격이며,
   이후 단계에서 실제 서브커맨드로 교체/확장될 것을 전제로 함.
4. **상태 전이 로직 없음**: `AccountState` enum만 정의되어 있고, 상태를
   실제로 바꾸는 로직(ADB 폴링 등)은 없음.
5. **의존성 최소화**: 외부 의존성은 `PyYAML`, 개발 의존성은 `pytest`만 포함.
6. **Windows 개행 경고**: 커밋 시 "LF will be replaced by CRLF" 경고 발생
   (core.autocrlf 설정에 따른 정상 동작으로 판단되며 기능에 영향 없음).
7. **실행 환경에 Python이 기본 설치돼 있지 않았음**: 위 "실행 환경 참고" 참조.

### QA 확인사항 (요청)

- [ ] QA 환경에서 `pip install -e ".[dev]"` 후 `pytest`가 동일하게 11개 통과하는지 확인
- [ ] `configs/config.yaml`이 없을 때 `ldmanager.cli` 실행 시 자동 생성/추측 없이
      에러 메시지만 출력되는지 확인 (부작용 없음 확인)
- [ ] `configs/config.example.yaml`을 복사해 임의 `LDx` 값 1~2개만 채운 뒤
      `LDMANAGER_CONFIG` 환경변수로 경로 지정 시 정상 로드되는지 확인
- [ ] 알 수 없는 키(예: `LD10`)를 `adb_mapping`에 넣었을 때 `ConfigError`로
      거부되는지 확인
- [ ] `docs/`, `configs/config.yaml` 등 민감할 수 있는 로컬 설정이
      `.gitignore`로 실제 제외되는지 확인 (`git status` 상 미추적)
- [ ] 이번 단계에서 금지된 항목(신규 에이전트/worktree/역할, Manager 문서 수정,
      실제 LD/게임 조작, 자격증명 처리, 웹 DOM, 전역 마우스 제어)이 코드베이스
      어디에도 없는지 diff 재확인

---

## TP-001 stage 2: 설정 확장 + 계정별 로그 시스템 + 진단 스크린샷 기반

**상태: 부분 구현 (stage 2 범위 한정). 최종 PASS/병합 선언 아님 — QA 확인 필요.
stage 1 항목 포함 전체 AC는 여전히 QA 미검증(NOT_TESTED) 상태이며, 아래는
"자체 실행 결과"이지 QA 승인이 아님.**

### 구현 AC

| AC | 구현 여부 | 비고 |
|---|---|---|
| 사용자 설정 안전 저장/로드/검증 | 구현 | `config.py`: `logging`/`diagnostics` 섹션 추가, 알 수 없는 top-level/섹션 키 거부, 값 타입·범위 검증(`retention_days`, `max_bytes`, `backup_count`, 경로 문자열) |
| 민감정보 필드 거부(저장하지 않음) | 구현(거부 방식) | `_find_sensitive_keys()`가 `password/secret/token/api_key/credential/auth/cookie` 등 패턴을 설정 트리 전체(중첩 포함)에서 재귀 탐색, 하나라도 있으면 `ConfigError`로 **로드 자체를 거부**. 부분 수용/자동 마스킹은 하지 않음(더 안전한 실패 방식 선택) |
| 로그 디렉터리/회전/보존 정책 | 구현 | `logs.py`: `LoggingSettings`(root_dir, retention_days, max_bytes, backup_count), `RotatingFileHandler` 기반 크기 회전, `purge_expired_logs()`로 `retention_days` 경과 회전 파일 삭제(파일명 패턴 한정, best-effort) |
| LD1~LD9 계정별 작업/오류 로그 분리 | 구현 | `get_account_logger()`가 계정마다 `logs/<LDx>/task.log`(INFO/WARNING, `_MaxLevelFilter`로 ERROR 제외)와 `logs/<LDx>/error.log`(ERROR 이상)를 별도 핸들러로 기록 |
| 진단 스크린샷 경로/메타데이터 생성 기반 (실제 캡처는 다음 단계) | 구현 | `diagnostics.py`: `build_screenshot_request()`(경로만 계산, 파일 미생성), `write_metadata_sidecar()`(JSON 메타데이터만 기록, PNG 바이트는 전혀 작성하지 않음). ADB 호출 없음 |
| 안전한 파일명/경로 검증 | 구현 | `paths.py`: `sanitize_filename()`(경로 구성요소 제거, 허용 문자만, `..`/빈 값은 fallback), `ensure_safe_subdir()`(세그먼트 화이트리스트 검증 + resolve 기반 root 이탈 차단) — logs/diagnostics 양쪽에서 재사용 |
| 기본 설정이 실제 ADB serial/port를 추측하지 않음 | 구현 (유지) | stage 1과 동일하게 `adb_mapping`은 전부 `null`; stage 2에서 추가된 섹션들도 값 추측 없음(생략 시 고정된 안전 기본값만 사용) |
| `config.yaml` gitignore 유지 | 구현 (유지, 변경 없음) | `.gitignore`의 `configs/config.yaml` 규칙 그대로 |
| pytest 자동 테스트 추가/재실행 | 구현 | 신규 `test_logs.py`(5), `test_diagnostics.py`(5), `test_paths.py`(9), `test_config.py`에 12개 추가 → 총 43개, 전부 통과 |
| 실제 LD/게임 조작, 웹 DOM, 전역 마우스, 자격증명 저장·로그 기록 | **미구현 (의도적, 범위 제외)** | 로거는 호출자가 넘긴 메시지를 그대로 기록할 뿐 자격증명 여부를 판별하지 않음 — "로그에 자격증명을 절대 넘기지 말 것"은 코드 주석으로만 명시된 **호출자 책임**이며, 런타임 강제 마스킹은 구현하지 않음(한계 항목 참고) |
| 실제 ADB 스크린샷 캡처 | **미구현 (의도적, 범위 제외)** | 다음 단계 예정. 이번 단계는 경로/메타데이터 골격까지만 |
| 신규 에이전트/하위 에이전트/worktree/역할 생성 | **미수행 (의도적)** | 지시에 따라 생성하지 않음 |
| Manager 문서 수정 | **미수행 (의도적)** | Code worktree의 프로그램/테스트/설정만 변경 |

### 변경 파일

```
 README.md                        (수정 — stage 2 안내 추가)
 configs/config.example.yaml      (수정 — logging/diagnostics 섹션 추가)
 src/ldmanager/config.py          (수정 — 섹션 검증 + 민감정보 거부)
 src/ldmanager/logs.py            (신규 — 계정별 로그/회전/보존)
 src/ldmanager/diagnostics.py     (신규 — 스크린샷 경로/메타데이터)
 src/ldmanager/paths.py           (신규 — 안전 파일명/경로 검증)
 tests/test_config.py             (수정 — 신규 케이스 12개 추가)
 tests/test_logs.py               (신규)
 tests/test_diagnostics.py        (신규)
 tests/test_paths.py              (신규)
 docs/HANDOFF_CODE.md             (수정 — 본 stage 2 절 추가)
```

### 테스트 명령 / 결과

```
.venv\Scripts\python.exe -m pytest -v
```

결과: **43 passed** (stage 1의 11개 포함, stage 2 신규/확장 32개).
전체 목록은 실행 로그 기준이며 실패/스킵 없음. 별도로
`python -m ldmanager.cli`를 설정 파일 없이 수동 실행해 기존 동작(에러
안내 + LD1~LD9 기본 레지스트리 출력)에 회귀가 없음을 확인함. 커밋 후
`git status --short`로 `logs/`, `diagnostics/` 등 의도치 않은 파일이
작업 트리에 남지 않았음을 확인함(모든 로그/스크린샷 테스트는
`tmp_path`에서만 파일을 생성).

### 커밋 해시

- stage 1: `4fada03`, `28dd160` (이전 절 참고)
- stage 2: 이 커밋 직후 `git log -1`로 확정 — 아래 "커밋 로그" 참고.
  (본 문서 커밋 자체가 stage 2 최종 커밋이므로, 해시는 PR/브랜치의
  `git log --oneline -3` 결과를 그대로 인용할 것.)

### 한계 (Limitations)

1. **로그 자격증명 마스킹 없음**: 로거는 전달된 메시지 문자열을 검사·필터링하지
   않는다. "자격증명을 로그 인자로 넘기지 말 것"은 코드 주석상의 호출자 계약일
   뿐, 실수로 비밀번호를 `logger.info(...)`에 넘기면 그대로 기록된다. 이후
   단계에서 실제 자격증명을 다루게 되면 마스킹/redaction 레이어가 별도로
   필요하다.
2. **회전 로그 보존 정책은 수동 트리거**: `purge_expired_logs()`는 존재하지만
   자동으로 스케줄링되지 않는다. 운영 시 별도 스케줄러(cron/Task Scheduler
   등)나 애플리케이션 시작 훅에서 호출해야 한다.
3. **로거 핸들러는 프로세스 전역 상태**: `logging.getLogger()` 기반이라 동일
   프로세스에서 같은 계정 로거를 다른 `LoggingSettings`로 다시 구성하려면
   `force=True`가 필요하다(테스트에서만 사용). 일반 런타임 흐름에서는 계정당
   설정이 한 번만 적용된다고 가정한다.
4. **진단 스크린샷은 메타데이터만**: `build_screenshot_request()`가 만든
   `image_path`에는 실제 PNG가 존재하지 않는다. 이 경로를 실제 파일 존재로
   착각하지 않도록 다음 단계 구현자가 주의해야 한다.
5. **퍼지 함수는 파일명 패턴에만 반응**: `purge_expired_logs()`는
   `task.log*`/`error.log*` 패턴에 맞는 파일만 삭제 대상으로 스캔한다.
   로그 디렉터리에 다른 용도의 파일을 섞어 두면 그 파일은 보존/삭제 대상에서
   아예 제외된다(의도된 보수적 동작).
6. **민감정보 탐지는 키 이름 기반 휴리스틱**: 값 내용이 아니라 키 이름
   패턴(`password`, `token` 등)만 검사한다. 키 이름을 우회하면(예: `x1: ...`)
   탐지되지 않으므로 완전한 방어선이 아니라 "실수 방지용 가드레일"이다.
7. **Windows 개행 경고**: 여전히 "LF will be replaced by CRLF" 경고가
   커밋 시 발생하나 기능에 영향 없음(stage 1과 동일).
8. **stage 1 한계 항목 유지**: CLI는 여전히 정보 출력용, 상태 전이 로직 없음,
   실제 LD/게임 조작 없음 등은 stage 1 절과 동일하게 유효.

### QA 중점사항 (요청)

- [ ] `password`/`token`/`api_key` 등 키를 `config.yaml`에 넣었을 때
      (top-level, `logging`/`diagnostics` 중첩 포함) 예외 없이 로드가
      거부되는지 재확인
- [ ] `logging.retention_days`/`max_bytes`/`backup_count`에 0/음수/문자열 등
      잘못된 값을 넣었을 때 각각 `ConfigError`로 거부되는지 확인
- [ ] 같은 프로세스에서 LD1~LD9 각각에 대해 `task.log`/`error.log`가 실제로
      분리되어 기록되는지(오류 로그에 INFO가 섞이지 않는지, 그 반대도) 수동
      확인
- [ ] `purge_expired_logs()`를 오래된 회전 로그와 최신 로그가 섞인 디렉터리에
      대해 실행했을 때 최신 파일은 보존되고 오래된 파일만 삭제되는지 확인
- [ ] `build_screenshot_request()` / `write_metadata_sidecar()` 실행 후
      디스크에 `.png`가 절대 생성되지 않고 `.json` 메타데이터만 생성되는지
      확인 (실제 캡처 미구현 원칙 준수 여부)
- [ ] `ensure_safe_subdir()`/`sanitize_filename()`에 `..`, `/`, 특수문자,
      빈 문자열 등 악의적 입력을 넣었을 때 경로 탈출이 발생하지 않는지 재확인
- [ ] `configs/config.yaml`이 여전히 `.gitignore`에 의해 추적 제외되는지,
      이번 커밋에 실수로 포함된 로컬 로그/스크린샷 파일이 없는지 `git show
      --stat` 재확인
- [ ] 이번 단계 금지 항목(신규 에이전트/worktree/역할, Manager 문서 수정,
      실제 LD/게임 조작, 웹 DOM, 전역 마우스, 자격증명 저장·로그 기록)이
      코드베이스 어디에도 없는지 diff 재확인
