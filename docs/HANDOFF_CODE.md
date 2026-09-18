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
- stage 2: `6130f0d` — "TP-001 stage 2: config extension + per-account log system"
  (브랜치 `kpj0526/Code`). 본 문서 갱신은 그 뒤의 후속 커밋.

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

---

## TP-001-RW-02 (Stage 2 교정): 로그 자격증명 미저장 + gitignore 커버리지

**Manager corrective packet**: TP-001-RW-02. QA FAILED 대상 커밋
`ba0e3da1228b70cd34a40e74a0f262212ed8310a`. QA report 커밋
`5cba31e2d09b254166e4dbb79a5786be674e848e`.

**상태: 지시된 4개 교정 항목만 부분 구현. 프로젝트 전체 AC PASS를 선언하지
않음. QA 재검증 필요.**

> AC 트레이서빌리티 참고: 이 worktree에는 Manager 쪽 공식 AC 카탈로그
> 원문이 없어 "AC-26"의 정확한 문구를 직접 확인할 수 없었습니다. 아래
> 표는 교정 지시 패킷(TP-001-RW-02) 본문에 적힌 4개 항목 + 그 항목이
> 가리키는 것으로 보이는 보안 제약("로그에 자격증명 평문 미저장")을
> 기준으로 작성했습니다. QA가 공식 AC-26 문구와 1:1로 대조해 주시기
> 바랍니다.

### 구현 AC / 트레이서빌리티

| # | 지시 항목 (교정 패킷 원문 요약) | AC 매핑(추정) | 구현 여부 | 비고 |
|---|---|---|---|---|
| 1 | `password=...` 등 통제 마커가 계정 task/error 로그에 절대 남지 않아야 함(비식별화 또는 거부, password/token/API key/authorization/cookie 커버, 원문 값 보존 금지) | **AC-26** (로그 자격증명 미기록/미보존) + 보안 필수 제약 | **구현** | `src/ldmanager/redaction.py`(`redact_sensitive_text`) + `src/ldmanager/logs.py`의 `SensitiveDataRedactionFilter`. 로거(핸들러 아님)에 부착되어 `record.getMessage()`로 렌더링 후 치환, `record.args=()`로 재노출 차단 — 핸들러가 레코드를 받기 *전에* 1회 적용 |
| 2 | 생성되는 `logs/`, `diagnostics/` 아티팩트에 대한 Git ignore 커버리지 추가, 기존 config 보호 유지 | (인프라/위생 요구사항) | **구현** | `.gitignore`에 `/logs/`, `/diagnostics/` 추가. 기존 `configs/config.yaml` 규칙은 그대로 유지(삭제/수정 없음) |
| 3 | 통제된 민감 마커가 task/error 출력에 없음 + 명시된 생성 경로들이 ignore됨을 증명하는 회귀 테스트, 격리/보존·회전/설정 검증/경로 안전성/JSON-only 진단은 보존 | (회귀 테스트 요구사항) | **구현** | `tests/test_redaction.py`(9), `tests/test_logs.py`에 레드액션 통합 테스트 5개 추가, `tests/test_gitignore.py`(7, `git check-ignore` 서브프로세스 기반). 기존 격리/보존·회전/설정검증/경로안전/JSON-only 테스트는 **삭제·수정 없이 그대로 유지**(회귀 없음을 재실행으로 확인) |
| 4 | 전체 테스트 실행, 커밋, HANDOFF 갱신(태스크ID/AC/파일/명령·결과/커밋/한계/QA 포인트) | (프로세스 요구사항) | **구현** | 아래 각 절 참고 |
| — | 프로젝트 AC PASS 선언 | — | **선언하지 않음** | Manager 지시대로 개별 교정 항목 완료만 보고, 전체 PASS 주장 없음 |

### 실제 변경 파일

```
 .gitignore                (수정 — /logs/, /diagnostics/ 추가; configs/config.yaml 규칙 유지)
 src/ldmanager/redaction.py (신규 — 자격증명형 값 텍스트 치환)
 src/ldmanager/logs.py       (수정 — SensitiveDataRedactionFilter를 로거에 부착)
 tests/test_redaction.py    (신규 — 9개)
 tests/test_logs.py         (수정 — 레드액션 통합 회귀 테스트 5개 추가, 기존 10개 유지)
 tests/test_gitignore.py    (신규 — 7개, git check-ignore 기반)
 docs/HANDOFF_CODE.md       (수정 — 본 절 추가)
```

건드리지 않은 것(회귀 보존 확인): `config.py`(민감 키 거부/섹션 검증),
`paths.py`(경로 안전성), `diagnostics.py`(JSON-only 메타데이터, 이미지
미생성) — 코드 변경 없음, 관련 기존 테스트 전부 그대로 통과.

### 테스트 명령 / 결과

```
.venv\Scripts\python.exe -m pytest -v
```

결과: **64 passed**, 0 failed, 0 skipped (stage 1의 11개 + stage 2의 32개 +
이번 교정의 21개[레드액션 9 + 로그 통합 5 + gitignore 7]). 전체 로그는
세션 기록 참고. 별도로 `git status --short`로 테스트 실행 후 저장소
루트에 `logs/`, `diagnostics/` 등 의도치 않은 파일이 생성되지 않았음을
확인함(모든 로그/스크린샷 테스트는 `tmp_path`에서만 파일 생성).

추가 수동 확인:
```
git check-ignore -q logs/LD1/task.log            # exit 0 (ignored)
git check-ignore -q diagnostics/screenshots/x.png  # exit 0 (ignored)
git check-ignore -q configs/config.yaml           # exit 0 (ignored, 유지됨)
git check-ignore -q configs/config.example.yaml   # exit 1 (추적 대상 유지)
```

### 커밋 해시

- 이전(QA FAIL 대상): `ba0e3da` (stage 2 문서 갱신 커밋, QA가 지목한 해시)
- 이번 교정 커밋: `1acf510` — "TP-001-RW-02: redact log secrets + gitignore
  generated artifacts" (브랜치 `kpj0526/Code`). 본 문서의 해시 기록 갱신은
  그 뒤의 후속 커밋.

### 한계 (Limitations)

1. **`exc_info`/트레이스백은 레드액션 대상이 아님**: `SensitiveDataRedactionFilter`는
   `record.getMessage()`(포맷된 메시지 문자열)만 치환한다. 예외 객체의
   `str(exception)`이나 트레이스백 텍스트 안에 자격증명이 들어있는 경우
   (예: `logger.exception(...)`으로 예외 메시지 자체에 비밀번호가 포함된 경우)는
   이번 교정 범위 밖이며 레드액션되지 않는다.
2. **키 이름 기반 값 매칭의 한계**: `password=`, `token:` 같은 "키=값"/
   "키: 값" 패턴과 `Authorization`/`Cookie` 헤더 형태만 인식한다. 완전히
   다른 표현(예: 키 이름 없이 값만 로깅, 혹은 커스텀 헤더명)은 탐지되지
   않는다 — 이는 완벽한 DLP가 아니라 "실수 방지 가드레일"이다.
3. **헤더형 치환은 해당 줄 전체를 지움**: `Authorization`/`Cookie` 패턴은
   구분자 뒤 "그 줄 전체"를 치환한다. 같은 줄에 자격증명과 무관한 후속
   텍스트가 있었다면 그것도 함께 사라진다(형식 손실은 있지만 안전 우선
   설계로 의도됨).
4. **필터는 로거 인스턴스에 부착 — 프로세스 전역 상태**: stage 2와 동일한
   한계로, 동일 계정 로거를 재구성하려면 `force=True`가 필요하다(테스트
   전용). 이 교정은 필터를 항상 (재)설치하도록 만들었으므로 `force=True`
   경로에서 필터가 누락되거나 중복되지 않음을 테스트로 확인했다.
5. **`.gitignore`의 `/logs/`, `/diagnostics/`는 저장소 루트 기준 절대
   경로 패턴**: `LoggingSettings.root_dir`/`DiagnosticsSettings.screenshot_dir`를
   저장소 루트 밖(예: 절대 경로, 다른 드라이브)으로 설정하면 이 ignore
   규칙이 적용되지 않는다(원래 git ignore가 저장소 밖 경로에 적용될 수
   없다는 것과 동일한 제약이며, 별도 버그 아님).
6. **AC-26 원문 미대조**: 위 "AC 트레이서빌리티 참고"에 적었듯, 공식 AC
   카탈로그를 이 worktree에서 직접 열람하지 못해 매핑은 교정 패킷 텍스트
   기반 추정이다.
7. stage 1/2에서 이미 기록된 한계(자동 보존정책 미스케줄링, CLI 정보출력
   전용 등)는 그대로 유효하며 본 교정과 무관하게 남아 있다.

### QA 중점사항 (요청)

- [ ] 지시된 통제 마커(`password=`, `token=`, `api_key=`, `Authorization:
      Bearer ...`, `Cookie: ...`)를 각각 task/error 로거로 직접 호출해
      실제 파일에서 원문 리터럴이 전혀 검색되지 않는지(`grep`/`findstr`
      등으로) 재확인
- [ ] `logger.info("password=%s", secret)`처럼 **인자로 전달된** 값도
      레드액션되는지(형식 문자열에 리터럴로 박혀있지 않은 경우) 별도 확인
- [ ] `git check-ignore -v logs/... diagnostics/...`로 어떤 `.gitignore`
      규칙이 매칭되는지 확인하고, `configs/config.yaml`이 여전히
      ignore되며 `configs/config.example.yaml`은 추적 대상으로 남는지 확인
- [ ] stage 2에서 검증된 항목(계정별 로그 격리, 회전/보존, config 섹션
      검증, 경로 안전성, 진단 스크린샷 JSON-only) 테스트가 이번 커밋에서도
      전부 통과하는지(회귀 없음) 재실행 확인
- [ ] `exc_info`/예외 트레이스백 경유 자격증명 유출 가능성(위 한계 1번)에
      대해 이후 단계에서 별도 AC로 다룰지 Manager와 확인
- [ ] 이번 교정에서도 금지 항목(신규 에이전트/worktree/역할 생성, Manager
      문서 수정, 실제 LD/게임 조작, 웹 DOM, 전역 마우스, 자격증명 저장)이
      코드베이스에 없는지 diff 재확인

---

## TP-001-RW-03 (Stage 2 재교정): `logger.exception()` 트레이스백 자격증명 미저장

**Manager corrective packet**: TP-001-RW-03. QA final report
`179a679252cda5adb4002b0ed341ea9089ed4881`이 대상 커밋
`1305ba5a8b629e77664566702fb3ffe04eb8ac5e`(TP-001-RW-02 결과물)를 **FAIL**
처리함 — 64개 테스트가 전부 통과했음에도, `logger.exception()`으로 통제된
`password=...` 형태 마커를 기록하면 그 마커가 `error.log`의 트레이스백
텍스트에 그대로 남는 문제(`traceback_sensitive_marker_absent=False`,
Critical). 이는 TP-001-RW-02 한계 1번("`exc_info`/트레이스백은 레드액션
대상이 아님")으로 이미 명시했던 갭이 실제로 재현된 것입니다.

**상태: 이번 교정 항목만 구현. 프로젝트 전체 AC PASS를 선언하지 않음.**
QA 재검증 조건(동일 재현 시 `traceback_sensitive_marker_absent=True` +
Stage 2 전체 재실행 PASS)은 아래 자체 실행 결과로는 충족되는 것으로
보이나, 최종 판정은 QA가 내립니다.

### 근본 원인

`SensitiveDataRedactionFilter`(TP-001-RW-02)는 `record.getMessage()`
(즉 `msg % args`)만 치환했다. `logger.exception()`이 설정하는
`record.exc_info`(예외 타입/값/트레이스백 튜플)는 `logging.Formatter.format()`
내부에서 **핸들러가 레코드를 포맷할 때** 비로소
`self.formatException(record.exc_info)`로 원문 그대로 렌더링되므로,
필터 단계에서 건드리지 않으면 예외 메시지에 박힌 비밀값이 그대로
`error.log`(때로는 `task.log`, `exc_info=True`를 낮은 레벨에 쓴 경우)에
쓰였다.

### 구현 AC / 트레이서빌리티

| # | 지시 항목 | 구현 여부 | 비고 |
|---|---|---|---|
| 1 | `exc_info`/포맷된 트레이스백 출력에서 민감값을 어떤 파일 핸들러가 쓰기 전에 레드액션 또는 안전 차단. 예외 메시지/트레이스백 + 기존 메시지/args 모두 커버. 정상 오류 진단 정보는 보존, 원본 비밀값은 미보존 | **구현** | `logs.py`의 `SensitiveDataRedactionFilter`를 확장: `record.exc_info`가 있으면 `traceback.format_exception(*record.exc_info)`로 직접 렌더링 → `redact_sensitive_text()`로 치환 → `record.exc_text`에 저장 → `record.exc_info = None`으로 원본 예외 튜플 제거(Formatter가 재포맷 못 하도록). `record.stack_info`도 동일 원칙으로 치환. 기존 msg/args 경로는 변경 없이 유지 |
| 2 | `logger.exception()`/`exc_info`를 쓰는 직접 회귀 테스트 추가, 마커가 error.log에 없음을 단언. task/error + 기존 일반/`%` 테스트 포함 | **구현** | `tests/test_logs.py`에 2개 추가: `test_logger_exception_traceback_marker_absent_from_error_log`(ERROR 레벨, `logger.exception()`, error.log 검증 + `ValueError`/메시지/`Traceback (most recent call last)` 등 정상 진단 정보 보존 확인), `test_exc_info_marker_absent_from_task_log_when_logged_below_error`(INFO 레벨 + `exc_info=True`, task.log 검증). 기존 일반 메시지/`%`-인자 레드액션 테스트(TP-001-RW-02, 5개)는 수정 없이 그대로 유지 |
| 3 | 전체 스위트 실행, Stage 2 기능 전부 보존 | **구현** | `pytest -v` → **66 passed**, 0 failed(기존 64 + 신규 2). Stage 1/2/RW-02의 기존 테스트는 무수정, 전부 재통과 |
| 4 | 커밋 + HANDOFF 갱신(TP-001-RW-03, 파일, 명령/결과, 정확한 해시, 한계, QA 포인트) | **구현** | 아래 각 절 참고 |
| — | 프로젝트 AC PASS 선언 | — | **선언하지 않음** |

### 실제 변경 파일

```
 src/ldmanager/logs.py   (수정 — SensitiveDataRedactionFilter가 exc_info/stack_info도 레드액션)
 tests/test_logs.py      (수정 — exc_info 회귀 테스트 2개 추가)
 docs/HANDOFF_CODE.md    (수정 — 본 절 추가)
```

건드리지 않은 것(회귀 보존 확인): `redaction.py`(패턴 자체는 변경 없음,
`traceback.format_exception()` 출력 문자열에 그대로 재사용),
`config.py`/`paths.py`/`diagnostics.py`/`.gitignore` — 무변경, 관련 기존
테스트 전부 그대로 통과.

### 테스트 명령 / 결과

```
.venv\Scripts\python.exe -m pytest -v
```

결과: **66 passed**, 0 failed, 0 skipped
(Stage 1 11 + Stage 2 32 + RW-02 21 + RW-03 신규 2). QA가 보고한 재현
시나리오와 동일한 형태로 자체 재현:

```python
try:
    raise ValueError(f"login failed password={marker}")
except ValueError:
    logger.exception("unexpected failure")
```

위 코드로 생성된 `error.log`를 확인한 결과, 마커 리터럴은 부재하고
`password=***REDACTED***`, `ValueError`, `unexpected failure`,
`Traceback (most recent call last)` 등 정상 진단 정보는 그대로 보존됨을
자체 확인함(`traceback_sensitive_marker_absent=True`에 해당).

### 커밋 해시

- 이전(QA FAIL 대상): `1305ba5` (TP-001-RW-02 HANDOFF 갱신 커밋, QA가 지목한 해시)
- 이번 교정 커밋: `d8a6fcd` — "TP-001-RW-03: redact exc_info/traceback text
  in account logs" (브랜치 `kpj0526/Code`). 본 문서의 해시 기록 갱신은
  그 뒤의 후속 커밋.

### 한계 (Limitations)

1. **`record.exc_info`를 의도적으로 `None`으로 비움**: 표준 `logging.Formatter`
   흐름에서는 `exc_text`가 이미 설정되어 있으면 `exc_info`를 재사용하지
   않으므로 안전하지만, 이 레코드를 이후 다른 목적(예: 향후 단계에서 추가될
   외부 에러 리포팅/크래시 수집 연동)으로 원본 예외 객체가 필요한 커스텀
   핸들러가 붙는다면 그 핸들러는 원본 `exc_info` 튜플을 받지 못한다 —
   레드액션된 텍스트(`exc_text`)만 사용 가능하다. 의도된 트레이드오프.
2. **트레이스백 레드액션도 키 이름 기반 휴리스틱**: `redact_sensitive_text()`
   패턴 자체는 RW-02와 동일 — `password=`/`token:`/`Authorization:`/
   `Cookie:` 형태만 인식한다. 예외 메시지가 이런 키=값 형태를 쓰지 않고
   비밀값만 단독으로 들어 있으면(예: `raise ValueError(secret)`) 탐지되지
   않는다. 여전히 완전한 DLP가 아니라 가드레일이다.
3. **`stack_info`도 동일 함수로 일괄 치환**: `stack_info=True`로 남긴 콜
   스택 텍스트도 문자열 전체를 `redact_sensitive_text()`에 통과시킨다 —
   해당 기능은 이번 QA 실패 재현에 직접 관련되지 않았으나, 동일 취약점
   경로이므로 선제적으로 함께 처리함(과잉 구현이 아니라 동일 원인의 다른
   증상을 막기 위함).
4. RW-02/Stage 2에서 이미 기록된 한계(키 이름 기반 매칭의 일반적 한계,
   헤더형 치환이 해당 줄 전체를 지우는 점, `.gitignore` 루트 기준 제약,
   AC 카탈로그 원문 미대조, 자동 보존정책 미스케줄링 등)는 그대로
   유효하며 본 교정과 무관하게 남아 있다.

### QA 중점사항 (요청)

- [ ] QA가 보고한 정확한 재현 절차(같은 마커 문자열/호출 방식)로
      `error.log`를 재검사하여 `traceback_sensitive_marker_absent=True`가
      QA 환경에서도 재현되는지 확인
- [ ] `logger.exception()` 외에 `logger.error(msg, exc_info=True)`,
      `logger.warning(msg, exc_info=sys.exc_info())` 등 다른 `exc_info`
      전달 경로도 동일하게 레드액션되는지 추가 확인(본 교정은 필터가
      `record.exc_info` 존재 여부만 보므로 호출 방식과 무관하게 동작해야
      함 — 회귀 테스트로 일부 확인했으나 QA 자체 케이스로도 재확인 권장)
- [ ] 트레이스백에서 파일 경로/줄 번호/예외 타입 등 **비민감** 진단 정보가
      과도하게 삭제되지 않았는지(레드액션이 과잉 적용되지 않는지) 확인
- [ ] Stage 2 + RW-02에서 검증된 항목(계정별 로그 격리, 회전/보존, config
      섹션 검증, 경로 안전성, 진단 스크린샷 JSON-only, gitignore 커버리지)
      전체 재실행 PASS 확인(회귀 없음)
- [ ] 한계 1번(exc_info 소거)이 향후 크래시 리포팅 등 계획에 영향이
      있는지 Manager와 사전 확인
- [ ] 이번 교정에서도 금지 항목(신규 에이전트/worktree/역할 생성, Manager
      문서 수정, 실제 LD/게임 조작, 웹 DOM, 전역 마우스, 자격증명 저장)이
      코드베이스에 없는지 diff 재확인

---

## TP-002 stage 3: LD1~LD9 discovery + 명시적 ADB 매핑

**Manager task packet**: TP-002 (Stage 3). Prior Stage 2 범위는 QA PASS
(QA report `2529a1a`)로 확인됨. **프로젝트 전체 AC는 여전히
NOT_TESTED이며, 이번 절은 stage 3 범위에 한정된 자체 실행 결과다.**

**상태: 지시된 stage 3 항목만 구현. 프로젝트 AC PASS를 선언하지 않음.
병합하지 않음.**

> AC 트레이서빌리티 참고: 이 worktree에는 Manager 쪽 공식 AC 카탈로그
> 원문이 없어 "AC-01/02/09"의 정확한 문구를 직접 확인할 수 없었다. 아래
> 매핑은 패킷 지시 항목의 순서/의미를 기준으로 한 최선 추정이며, QA가
> 공식 문구와 대조해야 한다.

### 구현 AC / 트레이서빌리티

| AC(추정) | 지시 항목 | 구현 여부 | 비고 |
|---|---|---|---|
| **AC-01** | 주입 가능한 ADB 러너 + `adb devices` 출력 안전 파싱 | 구현 | `src/ldmanager/adb.py`: `AdbRunner`(Protocol, `list_devices()`/`run(serial, args)` 2개뿐), `SubprocessAdbRunner`(유일하게 실제 프로세스 실행), `parse_adb_devices_output()`(배너/데몬 라인 무시, 토큰 부족 라인은 스킵, 인식 못 하는 상태는 `UNKNOWN`으로 분류 — 어떤 입력에도 예외 없음) |
| **AC-02** | LD1~LD9 정확히 9개, distinct 시리얼로만 구성된 명시적 매핑 검증. 포트 추측 금지. 사용자가 매핑을 제공할 수 있으나 discovery가 임의 배정하지 않음. 누락/중복/9개 아님/미확인·오프라인·미승인·알수없음·손상된 상태로의 매핑 거부 | 구현 | `src/ldmanager/discovery.py`: `validate_complete_adb_mapping()`/`ensure_complete_adb_mapping()`(모양 검증: 정확히 LD1~LD9, distinct, non-null — ADB 미호출), `build_account_connection_statuses()`(실제 discovery 결과와 교차검증: `device_not_found`/`device_offline`/`device_unauthorized`/`device_state_unknown`/`discovery_unavailable`). discovery는 매핑되지 않은 계정에 보이는 장치를 자동 배정하지 않음(테스트로 확인) |
| **AC-09** | 계정별 연결/매핑 상태 및 구조화된 진단 오류를 자격증명 없이 노출 | 구현 | `AccountConnectionStatus`(account_id/status/serial/detail) — `serial`은 자격증명이 아닌 ADB 대상 문자열이라 노출 가능하다고 판단. `InvalidAdbMappingError`/`MappingValidationError`도 이슈 종류 + 사람이 읽을 수 있는 detail만 담고, 원시 예외 스택이나 시스템 경로 등은 노출하지 않음 |
| (인프라) | 명령 구성/러너는 파라미터화되고 정확히 지정된 시리얼 하나로만 범위가 한정됨. 실제 touch/screenshot/게임 조작/전역 마우스/DOM/로그인·재연결 없음 | 구현 | `build_adb_command()`가 `["adb", "-s", <serial>, *args]` 형태만 생성(빈/공백 포함 시리얼 거부). 이 프로젝트 어디에도 touch/tap/screenshot/입력/로그인/재연결/게임 로직 없음 — `adb.py`/`discovery.py` 모두 "무엇이 보이는가"와 "임의의 한 시리얼에 임의의 명령을 스코프해서 실행"까지만 구현 |
| (테스트) | 페이크 러너 기반 자동 테스트: 유효한 9개, 중복/누락/9개 아님, 오프라인/미승인/알수없음, 손상된 출력, 대상 명령 분리, 계정별 오류 표현 | 구현 | `tests/fakes.py`(`FakeAdbRunner`/`BrokenAdbRunner`), `tests/test_adb.py`(15개: 파싱 안전성, 명령 구성/분리, 서브프로세스 러너 argv), `tests/test_discovery.py`(15개: 유효 9개/누락/중복/9개 아님/오프라인/미승인/알수없음/discovery 불가/비-문자열 출력/미배정 원칙/불완전 매핑에서도 크래시 없음) |
| (문서) | config 예시/문서 갱신, 자격증명 없음 | 구현 | `configs/config.example.yaml`에 매핑 원칙 설명 추가(실제 시리얼 값은 여전히 전부 `null`), README에 stage 3 섹션 추가 |
| — | 실제 LDPlayer 연동 | **구현하지 않음 / 주장하지 않음** | 페이크 러너로만 검증됨. 실제 `adb` 바이너리·실제 에뮬레이터로 검증된 바 없음 |
| — | 프로젝트 AC PASS 선언 / 병합 | — | **선언하지 않음 / 수행하지 않음** |

### 실제 변경 파일

```
 src/ldmanager/adb.py         (신규)
 src/ldmanager/discovery.py   (신규)
 tests/fakes.py               (신규 — FakeAdbRunner/BrokenAdbRunner)
 tests/test_adb.py            (신규, 15개)
 tests/test_discovery.py      (신규, 15개)
 configs/config.example.yaml  (수정 — adb_mapping 설명 보강, 값 변경 없음)
 README.md                    (수정 — stage 3 섹션/구조 갱신)
 docs/HANDOFF_CODE.md          (수정 — 본 절 추가)
```

건드리지 않은 것(회귀 보존 확인): `config.py`, `logs.py`, `redaction.py`,
`paths.py`, `diagnostics.py`, `.gitignore`, `cli.py` — 코드 변경 없음.
`cli.py`는 이번 단계에서 discovery/adb 기능을 노출하도록 확장하지
않았다(범위를 라이브러리 계층으로 한정 — 아래 한계 3번 참고).

### 테스트 명령 / 결과

```
.venv\Scripts\python.exe -m pytest -v
```

결과: **98 passed**, 0 failed, 0 skipped. 실행 후 `git status --short`로
저장소에 의도치 않은 파일이 남지 않았음을 확인함(모든 신규 테스트는
인메모리 페이크 러너만 사용, 실제 subprocess/네트워크/파일 I/O 없음 —
`SubprocessAdbRunner` 관련 테스트도 `subprocess.run` 자체를
monkeypatch로 대체해 실제 `adb` 바이너리를 호출하지 않음).

### 커밋 해시

- 이전(Stage 2 PASS 확인 대상): `d8a6fcd`/`9f54d24` (TP-001-RW-03, QA PASS
  보고 `2529a1a`가 참조한 것으로 보이는 최신 상태)
- 이번 stage 3 커밋: `ffaa3ec` — "TP-002 stage 3: LD1-LD9 discovery +
  explicit ADB mapping validation" (브랜치 `kpj0526/Code`). 본 문서의
  해시 기록 갱신은 그 뒤의 후속 커밋.

### 한계 (Limitations)

1. **실제 LDPlayer/실제 ADB 미검증**: 이 worktree에는 실제 `adb` 실행
   파일이나 실제 LDPlayer 인스턴스가 없다(설치/확인하지 않음). 모든
   discovery/매핑 로직은 `FakeAdbRunner`로만 검증되었다.
   `SubprocessAdbRunner`의 argv 구성도 `subprocess.run` 자체를
   monkeypatch로 대체해 검증했을 뿐, 실제 프로세스 실행 경로는 시험되지
   않았다.
2. **`adb devices -l`의 확장 필드 미파싱**: `adb devices -l`이 출력하는
   `product:`/`model:`/`device:`/`transport_id:` 같은 추가 컬럼은
   파싱하지 않는다(현재는 시리얼 + 상태 두 컬럼만 사용). 필요해지면
   `parse_adb_devices_output()` 확장이 필요하다.
3. **CLI 미노출**: `cli.py`는 이번 단계에서 discovery/연결 상태를
   출력하도록 확장하지 않았다 — 라이브러리 계층(`adb.py`/`discovery.py`)만
   구현했다. 사람이 직접 상태를 보려면 아직 별도 스크립트/REPL에서
   함수를 호출해야 한다.
4. **`ensure_complete_adb_mapping()`은 어디서도 자동 호출되지 않음**:
   `config.load_config()`는 여전히 부분/미할당 매핑을 허용한다(stage
   1/2와 동일한 관대한 로딩). "완전한 9개 매핑" 요구는 이 함수를 명시적
   으로 호출하는 호출자(향후 연결 플로우)의 책임이다.
5. **`adb devices` 파싱은 상태 컬럼이 있는 모든 2-토큰 이상 라인을
   받아들임**: 진짜 ADB 출력이 아닌 우연히 2단어 이상인 노이즈 라인도
   시리얼+상태로 오인될 수 있다(상태는 `UNKNOWN`으로 안전하게 분류되지만
   "라인"으로는 집계됨). 완전한 grammar 파서가 아니라 실용적 파서다.
6. **AC-01/02/09 원문 미대조**: 위 "AC 트레이서빌리티 참고" 그대로 —
   공식 카탈로그 문구와 직접 대조하지 못했다.
7. Stage 1/2/RW-02/RW-03에서 이미 기록된 한계(자동 보존정책 미스케줄링,
   `exc_info` 소거의 트레이드오프, 키 이름 기반 레드액션 휴리스틱 등)는
   그대로 유효하며 본 단계와 무관하게 남아 있다.

### QA 중점사항 (요청)

- [ ] `validate_complete_adb_mapping()`이 정확히 "LD1~LD9, 9개, distinct,
      non-null"만 허용하고 그 외 모든 변형(8개/10개/중복/None 혼합)을
      거부하는지 경계값 위주로 재확인
- [ ] `build_account_connection_statuses()`가 매핑되지 않은 계정에
      discovery로 보이는 장치를 **절대 자동 배정하지 않는지**
      (`test_discovery_never_auto_assigns_unmapped_account_even_if_a_device_is_present`
      외에 QA 자체 시나리오로) 재확인
- [ ] `offline`/`unauthorized`/인식 불가 상태 토큰 각각이 서로 다른
      `ConnectionStatus`로 구분되는지, 그리고 `discovery_unavailable`
      (러너 예외/비-문자열 반환)이 예외를 전파하지 않고 안전하게
      보고되는지 확인
- [ ] `build_adb_command()`/`SubprocessAdbRunner.run()`이 항상 정확히
      하나의 명시적 시리얼로만 스코프되고, 빈 문자열/공백 포함 시리얼을
      거부하는지, 그리고 이 코드 경로 어디에도 touch/tap/screenshot/
      게임 입력/로그인 로직이 없는지 diff 재확인
- [ ] 이번 단계가 Stage 2(계정별 로그 격리/회전/보존, 민감정보 레드액션
      — msg/args + exc_info, config 섹션 검증, 경로 안전성, 진단
      스크린샷 JSON-only, gitignore 커버리지) 전체를 회귀 없이 유지하는지
      전체 스위트 재실행으로 확인
- [ ] "실제 LDPlayer 연동은 검증되지 않았다"는 명시적 서술이 README/
      HANDOFF 양쪽에 정확히 반영되어 있는지, 과장된 표현이 없는지 확인
- [ ] 금지 항목(신규 에이전트/worktree/역할 생성, Manager 문서 수정,
      실제 게임 자동화, 병합)이 이번 단계에도 없는지 diff 재확인

---

## TP-002-RW-01 (Stage 3 교정): 빈/공백 시리얼 미거부 결함 수정

**Manager corrective packet**: TP-002-RW-01. QA report 커밋 `356e730`이
Code 대상 `c5b8961`/`ffaa3ec`(TP-002 stage 3 결과물)를 **Major 결함으로
FAIL** 처리함 — `validate_complete_adb_mapping()`이 나머지 8개는
정상이고 `LD1`만 빈 문자열(`""`)인 9키 매핑을 아무 이슈 없이 통과시켰고,
그 결과 `ensure_complete_adb_mapping()`도 예외를 던지지 않음. 기대
동작: 빈 문자열/공백만 있는 시리얼 값은 이후 연결/명령 경로가 그 값에
의존하기 전에 "완전한 매핑" 검증 단계에서 반드시 거부되어야 함.

**상태: 이번 교정 항목만 구현. 프로젝트 AC PASS 선언하지 않음. 병합하지
않음.**

### 근본 원인

`validate_complete_adb_mapping()`의 누락 검사가 `serial is None`만
확인했다. config 레이어(`config.py`)는 빈 문자열을 애초에 허용하지
않지만(`validate_adb_mapping()`이 `""`.strip()이 falsy면 거부), 이
함수는 `dict`를 직접 받는 독립 함수라서 config를 거치지 않고 호출되는
경로(테스트, 향후 다른 호출자)에서는 `""`나 `"   "`가 `None`이 아니라는
이유만으로 "설정된 시리얼"로 오인되어 그대로 통과했다.

### 구현 AC / 트레이서빌리티

| # | 지시 항목 | 구현 여부 | 비고 |
|---|---|---|---|
| 1 | `validate_complete_adb_mapping()`이 빈 문자열/공백만 있는 시리얼을 거부하도록 매퍼 검증기 수정 | **구현** | `discovery.py`: 누락 판정을 `serial is None or (isinstance(serial, str) and serial.strip() == "")`로 확장. 빈/공백 값은 `MappingIssue.MISSING_ACCOUNT`로 분류(어떤 값이었는지 detail에 `repr()`로 표시 — 값 자체가 공백/빈 문자열이므로 노출해도 안전) |
| 2 | 빈/공백 시리얼에 대한 집중 테스트 추가(`ensure_complete_adb_mapping`이 예외를 던지는 것 포함) | **구현** | `tests/test_discovery.py`에 7개 추가: 빈 문자열(`test_empty_string_serial_is_rejected`), 공백만(`test_whitespace_only_serial_is_rejected`), 탭/개행만(`test_tab_and_newline_only_serial_is_rejected`), `ensure_complete_adb_mapping`이 빈 문자열/공백에 대해 각각 예외를 던지는지(`test_ensure_complete_adb_mapping_raises_for_empty_string_serial`, `..._for_whitespace_only_serial`), 두 계정이 모두 빈 값이어도 `DUPLICATE_SERIAL`로 오분류되지 않고 각각 `MISSING_ACCOUNT`로 집계되는지(`test_blank_serial_does_not_count_as_a_valid_distinct_serial`), 정상적인 9개 distinct non-blank 매핑은 여전히 통과하는지(`test_nine_distinct_nonblank_serials_are_still_accepted`) |
| 3 | 기존 stage 3 동작 전부 보존, 테스트 약화/삭제 금지 | **구현** | `test_adb.py`/기존 `test_discovery.py` 테스트는 한 줄도 수정/삭제하지 않음. 전체 스위트 재실행으로 무회귀 확인 |
| 4 | 전체 테스트 실행, 커밋, HANDOFF 갱신 | **구현** | 아래 각 절 참고 |
| — | 포트/장치 추측, 실제 ADB/LDPlayer/touch/screenshot/게임 제어 추가, Manager 문서 수정 | **수행하지 않음** | 지시대로 순수 검증 로직 수정 + 테스트만 추가 |
| — | 프로젝트 AC PASS 선언 / 병합 | — | **선언하지 않음 / 수행하지 않음** |

### 실제 변경 파일

```
 src/ldmanager/discovery.py   (수정 — 빈/공백 시리얼을 MISSING_ACCOUNT로 판정)
 tests/test_discovery.py      (수정 — 회귀 테스트 7개 추가, 기존 테스트 무변경)
 docs/HANDOFF_CODE.md         (수정 — 본 절 추가)
```

건드리지 않은 것(회귀 보존 확인): `adb.py`, `config.py`, `logs.py`,
`redaction.py`, `paths.py`, `diagnostics.py`, `.gitignore`, `cli.py`,
`tests/fakes.py`, `tests/test_adb.py` — 코드 변경 없음.

### 테스트 명령 / 결과

```
.venv\Scripts\python.exe -m pytest -v
```

결과: **105 passed**, 0 failed, 0 skipped (이전 98 + 이번 교정 7개
신규). QA가 보고한 정확한 재현(나머지 8개는 정상 + `LD1`만 `""`)을
자체 재현한 결과, `validate_complete_adb_mapping()`이
`MappingIssue.MISSING_ACCOUNT`를 반환하고 `ensure_complete_adb_mapping()`
이 `InvalidAdbMappingError`를 던짐을 확인함.

### 커밋 해시

- 이전(QA FAIL 대상): `c5b8961` / `ffaa3ec` (TP-002 stage 3, QA report `356e730`이 지목)
- 이번 교정 커밋: `5ea24e3` — "TP-002-RW-01: reject empty/whitespace-only
  serials in mapping validator" (브랜치 `kpj0526/Code`). 본 문서의 해시
  기록 갱신은 그 뒤의 후속 커밋.

### 한계 (Limitations)

1. **`build_account_connection_statuses()`는 별도로 blank 체크하지
   않음**: 이번 수정은 지시된 범위인 "complete-mapping 검증 경계"
   (`validate_complete_adb_mapping`/`ensure_complete_adb_mapping`)에
   한정했다. `build_account_connection_statuses()`는 여전히 `serial is
   None`만으로 `UNMAPPED`를 판정하므로, `ensure_complete_adb_mapping()`을
   거치지 않고 빈 문자열이 섞인 매핑을 이 함수에 직접 전달하면 그
   계정은 `UNMAPPED`가 아니라 `DEVICE_NOT_FOUND`로 보고된다(빈 문자열
   시리얼이 discovery 결과에 없을 것이므로). "완전한 매핑" 요구를
   먼저 통과시키는 것이 여전히 호출자의 책임이며, 이 경계를 생략하면
   이런 형태로 노출된다.
2. **config 레이어와의 이중 방어**: `config.py`의
   `validate_adb_mapping()`은 이미 빈 문자열을 거부하므로(stage 1부터
   존재), `load_config()`를 통해 로드된 정상 경로에서는 애초에 이
   결함이 재현되지 않았다. 이번 결함은 `config.py`를 우회해 dict를
   직접 구성/전달하는 경로(테스트, 향후 다른 호출자)에서만 실제로
   발생했다 — 두 레이어 모두에서 방어하는 현재 구조를 유지한다.
3. Stage 1/2/RW-02/RW-03/Stage 3에서 이미 기록된 한계는 그대로 유효하며
   본 교정과 무관하게 남아 있다.

### QA 중점사항 (요청)

- [ ] QA가 보고한 정확한 재현 절차(나머지 8개 정상 + `LD1=""`)로
      `validate_complete_adb_mapping()`/`ensure_complete_adb_mapping()`
      재검증
- [ ] 공백 종류 변형(스페이스만, 탭만, 개행만, 혼합)도 모두 거부되는지
      QA 자체 케이스로 추가 확인
- [ ] 두 계정이 모두 빈 값일 때 `DUPLICATE_SERIAL`로 잘못 집계되지
      않고 각각 `MISSING_ACCOUNT`로 보고되는지 재확인
- [ ] 정상적인 9개 distinct non-blank 매핑에 대해 오탐(false positive)이
      생기지 않았는지(회귀) 확인
- [ ] 한계 1번에서 언급한 `build_account_connection_statuses()`의 별도
      blank 처리 여부를 이후 단계에서 다룰지 Manager와 협의 필요한지
      판단
- [ ] Stage 3 전체(파싱 안전성, 명령 스코핑, discovery 상태 구분,
      미배정 원칙) 및 Stage 1/2/RW-02/RW-03 전체가 이번 커밋에서도
      회귀 없이 통과하는지 전체 스위트 재실행 확인
- [ ] 금지 항목(신규 에이전트/worktree/역할 생성, Manager 문서 수정,
      포트/장치 추측, 실제 게임 자동화, 병합)이 이번 교정에도 없는지
      diff 재확인

---

## TP-003: 계정별 ADB 스크린샷 캡처 + 가드된 상대 좌표 터치 기반

**Manager task packet**: TP-003. Gate: TP-002-RW-01 stage 3 범위 QA PASS
(`a3eb77f`, 대상 `a4dce6d`). **프로젝트 전체 AC는 여전히 NOT_TESTED이며,
이번 절은 TP-003 범위 자체 실행 결과다.**

**상태: 지시된 "안전한 주입형 기반(foundation)" 항목만 구현. 게임
자동화가 아님. 프로젝트 AC PASS 선언하지 않음. 병합하지 않음.**

### 구현 개요

| 구성요소 | 파일 | 역할 |
|---|---|---|
| 바이너리 캡처 가능한 ADB 러너 | `adb.py` (확장) | `AdbRunner` Protocol에 `capture_binary(serial, args)` 추가(텍스트 디코딩 없이 raw bytes), `SubprocessAdbRunner.capture_binary()`가 유일한 실제 구현, `validate_serial()`을 `build_adb_command()`/`screenshot.py`/`guarded_touch.py`가 공유 |
| 스크린샷 캡처 + 안전한 바이트 검증 | `screenshot.py` (신규) | `capture_screenshot()`: PNG 매직 헤더 검사, 실패/빈 출력/손상 바이트/러너 예외를 전부 구조화된 `ScreenshotCaptureResult(ok=False, error=...)`로 반환(예외 전파 없음) |
| 기기-내부 상대 좌표 | `coordinates.py` (신규) | `RelativeCoordinate`(`[0.0,1.0]` 엄격 검증, 생성 시점 즉시 거부), `ScreenSize`(양의 정수만), `build_tap_args()`(상대 좌표 → 픽셀 → `shell input tap x y` 인자만 생성, 전역 데스크톱 좌표 개념 없음) |
| 가드된 터치 상태 머신 | `guarded_touch.py` (신규) | `perform_guarded_touch()`: 캡처→사전조건 훅→(수락 시에만) 시리얼 하나에 정확히 한 번 터치→캡처→사후조건 훅. 실패/거짓/예외/타임아웃(재시도 상한 소진) 시 추가 입력 없이 계정 로컬 `GuardedTouchResult` 반환 |
| 테스트 더블 확장 | `tests/fakes.py` (수정) | `FakeAdbRunner`에 `capture_binary`/`capture_results`/`capture_calls` 추가, `ExceptionRaisingCaptureRunner`(러너 자체가 예외를 던지는 경로 전용) 신규 |

### 요구사항 대비 확인

- **단일 명시적 비공백 시리얼로만 범위 고정**: `validate_serial()`이
  `capture_binary`/`run` 양쪽에서 공유되며, 빈/공백 시리얼은 어떤 캡처나
  터치도 시도되기 전에 `ValueError`로 즉시 거부됨(테스트로 확인:
  `test_blank_serial_is_rejected_before_any_capture_or_touch` 등). 포트나
  장치를 추론/기본값으로 채우는 코드는 없음.
- **기기-내부 상대 좌표, 엄격 검증, 전역 마우스/고정 외부 좌표 없음**:
  `RelativeCoordinate.__post_init__`이 범위 밖/NaN/Inf/비수치/bool 값을
  전부 생성 시점에 거부. `build_tap_args()`는 항상
  `["shell", "input", "tap", <px>, <py>]`만 생성하며, 이 argv는 여전히
  `AdbRunner.run(serial, args)`를 통해 하나의 시리얼로만 스코프됨.
- **가드 계약**: `perform_guarded_touch()`가 정확히 지시된 5단계
  (신선한 캡처 → 사전조건 → 수락 시 단일 터치 → 신선한 캡처 →
  사후조건)를 구현. 사전조건 거짓/예외, 캡처 실패/손상, 사후조건
  거짓/예외/캡처실패 어느 경우든 `runner.calls`(탭 호출 기록)는 정확히
  0개(터치 전) 또는 1개(터치 후 실패)만 존재함을 테스트로 직접 확인.
- **재시도/타임아웃 상한**: `max_capture_attempts`/
  `max_postcondition_attempts`로 캡처·검증 재시도만 상한이 걸림(터치
  자체는 성공 여부와 무관하게 최대 1회). `sleep_fn`을 주입 가능하게 해
  테스트는 실제로 대기하지 않음(`lambda s: None`).
- **안전한 스크린샷 바이트 검증**: PNG 매직 헤더(`\x89PNG\r\n\x1a\n`)
  미만 길이/불일치 바이트는 `INVALID_IMAGE_BYTES`로, 빈 출력은
  `EMPTY_OUTPUT`으로, 러너 비정상 종료는 `RUNNER_FAILED`로, 러너 자체
  예외는 `EXCEPTION`으로 각각 구분되어 반환됨(모두 예외 없이).
- **테스트는 페이크/주입 러너만 사용**: 실제 `adb`/실제 LDPlayer는 어디
  에서도 호출되지 않음. `SubprocessAdbRunner` 관련 테스트도
  `subprocess.run` 자체를 monkeypatch로 대체.
- **금지 항목 미구현**: OCR, 이미지 템플릿 매칭, 미션/게임 로직, GUI,
  로그인/재연결, 전역 마우스, 웹 DOM, 자격증명 저장 — 이 코드베이스
  어디에도 없음(grep으로 재확인 가능: `ocr`, `template`, `mission`,
  `login`, `reconnect`, `pyautogui`, `mouse` 등 관련 코드/의존성 전무).

### 실제 변경 파일

```
 src/ldmanager/adb.py           (수정 — capture_binary 추가, validate_serial 공유화)
 src/ldmanager/coordinates.py   (신규)
 src/ldmanager/screenshot.py    (신규)
 src/ldmanager/guarded_touch.py (신규)
 tests/fakes.py                 (수정 — capture_binary 지원, ExceptionRaisingCaptureRunner 추가)
 tests/test_adb.py              (수정 — capture_binary argv/분리 테스트 4개 추가)
 tests/test_coordinates.py      (신규, 26개)
 tests/test_screenshot.py       (신규, 9개)
 tests/test_guarded_touch.py    (신규, 15개)
 README.md                      (수정 — TP-003 섹션/구조 갱신)
 docs/HANDOFF_CODE.md           (수정 — 본 절 추가)
```

건드리지 않은 것(회귀 보존 확인): `config.py`, `logs.py`, `redaction.py`,
`paths.py`, `diagnostics.py`, `discovery.py`, `.gitignore`, `cli.py`,
`models.py` — 코드 변경 없음. `configs/config.example.yaml`도 이번
단계에서는 변경하지 않았다(아래 한계 3번 참고 — 캡처 인자/화면 크기는
현재 함수 인자로만 전달되며 config 스키마에 아직 노출되지 않음).

### 테스트 명령 / 결과

```
.venv\Scripts\python.exe -m pytest -v
```

결과: **159 passed**, 0 failed, 0 skipped (이전 105 + 이번 TP-003 신규
54: test_adb.py +4, test_coordinates.py +26, test_screenshot.py +9,
test_guarded_touch.py +15 = 54). 실행 후 `git status --short`로
저장소에 의도치 않은 파일이 남지 않았음을 확인함(모든 신규 테스트는
인메모리 페이크 러너만 사용).

### 커밋 해시

- 이전(게이트, QA PASS 대상): `a4dce6d` (TP-002-RW-01, QA PASS 보고 `a3eb77f`)
- 이번 TP-003 커밋: `8b1687b` — "TP-003: per-instance ADB screenshot +
  guarded relative-touch foundation" (브랜치 `kpj0526/Code`). 본 문서의
  해시 기록 갱신은 그 뒤의 후속 커밋.

### 한계 (Limitations)

1. **실제 LDPlayer/실제 ADB 미검증**: 모든 캡처/터치 로직은
   `FakeAdbRunner`/`ExceptionRaisingCaptureRunner`로만 검증되었다. 실제
   PNG 디코딩(픽셀 유효성, 해상도 일치 등)이나 실제 `input tap`의 기기
   반응은 전혀 시험되지 않았다 — PNG 검증은 매직 헤더 존재 여부만 본다
   (아래 4번 참고).
2. **화면 크기(`ScreenSize`) 자동 조회 없음**: `wm size` 같은 명령으로
   기기의 실제 해상도를 조회하는 기능은 구현하지 않았다. 호출자가
   `ScreenSize`를 직접 공급해야 한다 — 잘못된 해상도를 넘기면 상대
   좌표가 엉뚱한 픽셀로 변환될 수 있다(좌표 자체의 `[0,1]` 검증과는
   별개의 책임).
3. **config.yaml에 아직 노출되지 않음**: 캡처 인자(`DEFAULT_CAPTURE_ARGS`),
   재시도/타임아웃 상한, 화면 크기는 모두 함수 기본값/인자이며
   `configs/config.example.yaml`에는 아직 추가하지 않았다 — 이번
   단계에서는 "설정 가능한 정책"보다 "안전한 기반 구현"을 우선했다.
   설정화가 필요하면 다음 단계에서 `config.py`에 섹션을 추가해야 한다.
4. **PNG 검증은 매직 헤더까지만**: 실제 PNG 청크 구조(IHDR 등)나
   해상도/손상 여부까지는 검사하지 않는다 — "바이트가 PNG처럼 시작하는가"
   만 확인하는 얕은 검증이다.
5. **재시도 사이 페이싱은 호출자 책임**: `sleep_fn`은 기본이
   no-op이므로, 실제 운영에서 캡처/장치 사이에 의미 있는 지연을 두려면
   호출자가 `time.sleep` 등을 명시적으로 주입해야 한다(이번 기반은
   페이싱 정책을 강제하지 않는다).
6. **`guarded_touch`는 사전/사후조건 훅의 "의미"에 관여하지 않음**:
   훅이 실제로 무엇을 검증하는지(신뢰도 임계값, 이미지 비교 등)는
   전적으로 미래 단계/호출자의 책임이며, 이번 기반은 훅의 반환값
   (True/False/예외)만 안전하게 처리한다 — OCR/템플릿 매칭 로직은
   의도적으로 포함하지 않았다.
7. Stage 1~3/RW-01~RW-03에서 이미 기록된 한계는 그대로 유효하며 본
   단계와 무관하게 남아 있다.

### QA 중점사항 (요청)

- [ ] "가드 계약"의 각 실패 지점(사전조건 거짓/예외, 사전 캡처 실패/
      손상, 터치 명령 자체 실패, 사후조건 거짓/예외, 사후 캡처 실패)에서
      `runner.calls`(탭 호출)가 정확히 의도된 개수(0 또는 1)인지, 그리고
      어떤 경우에도 탭이 2회 이상 발생하지 않는지 QA 자체 시나리오로
      재확인
- [ ] `RelativeCoordinate`/`ScreenSize`가 범위를 벗어나거나 비정상적인
      값(NaN/Inf/문자열/bool/0/음수/실수 픽셀)을 생성 시점에 확실히
      거부하는지 경계값 위주로 재확인
- [ ] `capture_binary`가 항상 정확히 하나의 명시적 시리얼로만 스코프
      되고, 서로 다른 시리얼의 캡처 호출이 `capture_calls`에서 섞이지
      않는지 diff/테스트로 재확인
- [ ] PNG 바이트 검증(매직 헤더만 확인하는 얕은 검증)이 실제 운영에서
      충분한지, 아니면 다음 단계에서 더 엄격한 검증(예: 최소 크기,
      IHDR 파싱)이 필요한지 Manager와 협의
- [ ] 이 코드베이스에 OCR/템플릿 매칭/미션 로직/GUI/로그인·재연결/
      전역 마우스/웹 DOM/자격증명 저장이 전혀 없는지 diff 및 의존성
      목록(`pyproject.toml`) 재확인
- [ ] Stage 1~3/RW-01~RW-03 전체가 이번 커밋에서도 회귀 없이 통과하는지
      전체 스위트 재실행 확인
- [ ] 화면 크기 자동 조회 부재(한계 2번), config 미노출(한계 3번)이
      다음 단계 계획에 영향이 있는지 Manager와 사전 확인
- [ ] 금지 항목(신규 에이전트/worktree/역할 생성, Manager 문서 수정,
      실제 게임 자동화, 병합)이 이번 단계에도 없는지 diff 재확인

---

## MVP-001: Runnable, configurable MVP

**Manager task packet: MVP-001.** Starting point: Stage 4 (= TP-003)
scope QA PASS `d69bc0b`, Code HEAD `efd3a2f`. Delivered as one
connected commit series prioritizing a runnable flow over exhaustive
refinement, reusing explicit-serial ADB / guarded capture-touch /
config-log-diagnostic protections from prior stages.

**Status: MVP scope delivered and self-tested only. No project AC
PASS claim. Not merged.** Per the packet, QA will smoke-test only and
label `MVP_SMOKE_PASS` / `MVP_SMOKE_FAIL` / `BLOCKED_REAL_ENVIRONMENT`
— this section is not a claim of that outcome.

### What was built

| Requirement (packet) | Delivered as | Notes |
|---|---|---|
| Runnable Python app | `src/ldmanager/app.py` (`build_controller()` + `main()`) | Wires real config, real `SubprocessAdbRunner`, `PlaceholderRecognizer`, one worker per account, GUI |
| Start script | `scripts/run.bat`, `scripts/run.ps1` | Both call `python -m ldmanager.app` (or the venv's python) |
| PyInstaller Windows build script (or generated exe if practical) | `scripts/build_windows.ps1` + `scripts/entrypoint.py` | **Actually run in this session** — see "PyInstaller build" below |
| Basic native GUI | `src/ldmanager/gui.py` (Tkinter, stdlib — no new GUI dependency) | LD1..LD9 panels + Start All/Stop All |
| LD1-LD9 example config | `configs/config.example.yaml` (pre-existing, unchanged) + `configs/mission.example.yaml` (new) | adb_mapping still all-`null`; mission ROIs are explicit placeholder examples |
| Templates folder | `templates/README.md` | Empty on purpose — no fabricated "success" assets |
| ROI/relative-coordinate/threshold/retry-timeout config | `src/ldmanager/coordinates.py` (`RelativeRegion` added) + `src/ldmanager/mission_config.py` | All validated, none guessed |
| Per-account logs/status | `logs.get_account_logger()` (reused) + `controller.AccountWorkerStatus` | Log reuse from Stage 2/RW-02/RW-03 unchanged |
| Simple run guide | `docs/RUN_GUIDE.md` | Also summarized in README |
| Actual-game-capture checklist | `docs/REAL_CAPTURE_CHECKLIST.md` | 8-section ordered checklist, nothing on it done yet |
| Unimplemented/unverified list | `docs/MVP_UNVERIFIED.md` | Split by "by design" vs. "scope cut" vs. "not verified" |
| Controller, one worker/account, individual+global start/stop, account-local state/error/log | `src/ldmanager/controller.py` (`AccountWorker`, `AccountController`) | Real `threading.Thread` + `threading.Event` per account |
| 5-slot → 200-kill-check → claim → reset state machine | `src/ldmanager/mission.py` (`run_one_cycle`) | Reuses `guarded_touch.perform_guarded_touch` for claim/reset |
| Configurable recognition abstraction, safe unknown/low-confidence | `src/ldmanager/recognition.py` (`Recognizer` protocol, `PlaceholderRecognizer`) | Always returns `UNKNOWN`/0.0 — never a hardcoded match |
| GUI shows LD1-LD9 status/slot/targets/error/log + buttons | `gui.AccountPanel` | Polls `controller.all_statuses()` on a timer |

### Requirement-by-requirement confirmation (mandatory behaviors)

- **Explicit serial, no cross-account command**: every capture/touch still goes through `adb.validate_serial()` + `build_adb_command`/`capture_binary` (Stage 3/TP-003, unchanged). `mission.run_one_cycle` takes one `serial` and never touches another. Tested: `tests/test_mission.py`, plus all prior `tests/test_adb.py` argv-isolation tests (unchanged, still passing).
- **Individual stop only local**: `AccountController.stop_account()` only calls that one worker's `stop()`; verified two independent real threads don't affect each other (`tests/test_controller.py::test_stopping_one_account_does_not_affect_another`).
- **Global stop leaves no automatic touch**: `mission.run_one_cycle` checks `should_stop()` before every capture and every touch (`tests/test_mission.py::test_should_stop_true_from_start_sends_zero_touches`, `test_stop_requested_after_first_slot_halts_with_no_touches_needed`); at the worker/thread level, `tests/test_controller.py::test_global_stop_all_sends_no_further_touch_calls_after_settling` proves no growth in recorded "touch" calls after a joined `stop_all()`.
- **Bounded retries/timeouts**: every mission-cycle loop (slot reroll, kill-check poll, claim/reset verification) is bounded by `MissionConfig`'s `max_*_attempts` fields — never unbounded. Tested directly (`test_recognition_never_matching_is_bounded_not_infinite`, `test_kill_check_never_matching_is_bounded_with_zero_touches`, plus the pre-existing `guarded_touch`/TP-003 bounded-retry tests, unchanged).
- **Recognition failure/unknown has no infinite click**: with `PlaceholderRecognizer` (always `UNKNOWN`), a slot exhausts its bound and the cycle safely stops (`SLOT_RECOGNITION_FAILED`) instead of looping — same test as above.
- **Worker exception containment**: `AccountWorker._loop` catches any exception from its cycle function, records it on that worker's own status, and never propagates — proven with one crashing worker + one normal worker running side by side (`tests/test_controller.py::test_worker_exception_is_contained_and_does_not_affect_other_workers`).
- **Program starts and GUI can construct**: `tests/test_gui.py` constructs a real `LDManagerApp(controller)` (real `tk.Tk()`, confirmed working in this Windows dev environment) without calling `mainloop()`; `tests/test_app.py` proves `build_controller()`/`main()` work against real (temp) config files without touching real ADB or opening a window.
- **Mock cycle reaches core states once**: `tests/test_mission.py::test_mock_cycle_reaches_all_core_states_once` runs one full cycle with a recognizer scripted to match every label, reaching all 5 slots + kill-check + claim + reset, `outcome == COMPLETED`, with exactly 2 touches total (claim + reset; no reroll needed).
- **Faked/injected only, no real device/game/login/reconnect/global mouse/DOM/guessed port/credentials/security bypass**: confirmed by construction — every new test uses `FakeAdbRunner`/`LabelMappingRecognizer`/`PlaceholderRecognizer`; no new dependency touches a display, input device, or network; `SubprocessAdbRunner`/Tk are the only two things that talk to something real, and both are exercised as: (a) `SubprocessAdbRunner` with `subprocess.run` monkeypatched in tests (unchanged from TP-003), never invoked for real inside pytest; (b) Tk is real (a real window toolkit is unavoidable for "GUI can construct"), but no `mainloop()` is ever called by a test.

### Actual files changed/added

```
 New source (src/ldmanager/):
   recognition.py       (Recognizer protocol + PlaceholderRecognizer)
   mission_config.py    (MissionConfig + YAML loader, validated)
   mission.py            (5-slot -> kill-check -> claim -> reset state machine)
   controller.py         (AccountWorker + AccountController)
   gui.py                 (Tkinter GUI)
   app.py                  (real wiring + main())

 Modified source:
   coordinates.py         (+ RelativeRegion, + to_pixel_rect)

 New tests:
   test_recognition.py (3), test_mission_config.py (13), test_mission.py (8),
   test_controller.py (8), test_gui.py (5), test_app.py (3)

 Modified tests:
   fakes.py               (+ LabelMappingRecognizer)
   test_coordinates.py    (+12: RelativeRegion/to_pixel_rect coverage)
   test_gitignore.py      (+5: mission.yaml / mission.example.yaml / PyInstaller artifacts)

 New config/assets:
   configs/mission.example.yaml
   templates/README.md

 New scripts:
   scripts/run.bat, scripts/run.ps1
   scripts/build_windows.ps1
   scripts/entrypoint.py  (PyInstaller-safe absolute-import launcher; see below)

 New docs:
   docs/RUN_GUIDE.md
   docs/REAL_CAPTURE_CHECKLIST.md
   docs/MVP_UNVERIFIED.md

 Modified:
   .gitignore   (+ configs/mission.yaml, + *.spec; build/ and dist/ already ignored)
   pyproject.toml (+ [project.optional-dependencies].build = ["pyinstaller>=6.0"])
   README.md    (MVP-001 banner, Quick Start, project structure, new "실행 가능한 MVP" section)
   docs/HANDOFF_CODE.md (this section)
```

Untouched (regression preserved): `adb.py` (unchanged from TP-003 except
already-covered prior sections), `config.py`, `logs.py`, `redaction.py`,
`paths.py`, `diagnostics.py`, `discovery.py`, `screenshot.py`,
`guarded_touch.py`, `models.py`, `cli.py`.

### PyInstaller build (actually run this session, not merely scripted)

A real build was executed and smoke-tested in this dev environment:

```
.venv\Scripts\python.exe -m pip install -e ".[build]"       # pyinstaller 6.22.2
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --name ldmanager \
    --windowed --paths src scripts\entrypoint.py
```

**First attempt failed** pointing PyInstaller directly at
`src/ldmanager/app.py`: `ImportError: attempted relative import with no
known parent package` (PyInstaller runs the target script as `__main__`
with no package context, breaking `app.py`'s `from .config import ...`
style imports). **Fixed** by adding `scripts/entrypoint.py` — a tiny
non-package wrapper that does `from ldmanager.app import main` (absolute
import, works frozen or unfrozen) — and pointing the build at that
instead. `scripts/build_windows.ps1` was updated to match.

Rebuilt successfully: `dist\ldmanager\ldmanager.exe` (~1.6 MB
bootstrap + `_internal\`). **Smoke-tested** by running the exe from an
empty directory (no `configs/config.yaml` present):

```
exit=1
Cannot start ldmanager: Config file not found: ...\configs\config.yaml. ...
```

— confirms the packaged exe's config-missing error path works exactly
like the unfrozen app, exits cleanly (no hang, no crash dialog), and no
window was left open (verified via `tasklist`/`taskkill` — a first,
accidental hung-window run during debugging was killed immediately;
see Limitations). **The "launch with a valid config and see the real
GUI window" path was deliberately not exercised from the built exe** in
this session, to avoid opening an uncontrolled on-screen window on the
host machine — that path is instead covered by `tests/test_gui.py`/
`tests/test_app.py` against the unfrozen app.

### Full test command / result

```
.venv\Scripts\python.exe -m pytest -v
```

Result: **216 passed**, 0 failed, 0 skipped (159 prior [Stage 1-3 +
RW-01..RW-03] + 57 new/changed this MVP: 40 in six new test files +
12 in `test_coordinates.py` + 5 in `test_gitignore.py`). Re-run 8x
consecutively during development to rule out the GUI-construction
flakiness described below (all 8 runs: 216/216 passed). `git status
--short` confirmed no stray files (`build/`, `dist/`, `logs/`,
`diagnostics/` all correctly git-ignored) after both the test run and
the PyInstaller build.

A real, reproducible flakiness was found and fixed during this session
(not a product bug, a test-fixture bug): `tests/test_gui.py` originally
created a fresh `tk.Tk()` root per test (function-scoped fixture);
constructing/destroying multiple Tk roots in quick succession within
one process intermittently raised `_tkinter.TclError` from Tcl/ttk
theme re-initialization. Fixed by making the fixture module-scoped (one
shared root for the whole file) — confirmed stable across 8 consecutive
full-suite runs after the fix.

### Commit(s)

- `ff6648d` — "MVP-001: runnable, configurable MVP (controller/mission/GUI/build)"
  (branch `kpj0526/Code`, gate `efd3a2f`). This HANDOFF hash-record
  update is the follow-up commit immediately after it. Not merged.

### Limitations

1. **Recognition is entirely a placeholder.** `PlaceholderRecognizer`
   never analyzes pixels; every recognition call returns `UNKNOWN`/0.0.
   Against a real screen, every mission cycle will exhaust its slot
   reroll bound and stop with `slot_recognition_failed` — this is the
   *intended* safe behavior of this MVP, not a bug, but it means **no
   real gameplay progress is possible until a real recognizer is
   implemented** (see `docs/REAL_CAPTURE_CHECKLIST.md` §4).
2. **`mission.example.yaml`'s ROIs/coordinates are illustrative, not
   calibrated.** They were never measured against a real screenshot.
3. **No automatic screen-resolution discovery.** `screen_size` is
   entered by hand; nothing runs `adb shell wm size` automatically.
4. **PyInstaller build verified only for the "config missing" error
   path**, not for successfully opening the real GUI window from the
   frozen exe (see above — deliberately not exercised to avoid an
   uncontrolled on-screen window during this session). The build is
   also only verified on this one dev machine, not on a clean end-user
   Windows install, and not as a fully offline-portable artifact.
5. **A real GUI window was briefly, unintentionally left open** during
   PyInstaller debugging (the first, broken build attempt actually
   crashed with an ImportError as designed — but a stray `ldmanager.exe`
   process was observed running past a 30s timeout during that same
   investigation and was force-closed via `taskkill` before it could be
   confirmed whether a visible window had actually appeared on screen).
   No further build/run attempt in this session left a process running
   — every subsequent invocation was verified to exit and confirmed
   absent via `tasklist` immediately after. Documented here in the
   interest of not hiding an imperfect step, even though the final
   delivered state has no lingering process.
6. **Idle delay between cycles is fixed (`DEFAULT_IDLE_DELAY_SECONDS =
   1.0`), not configurable via YAML yet.** Only mission-cycle retry/
   timeout bounds are in `mission.yaml`; the worker's own inter-cycle
   pacing is a Python constant in `app.py`.
7. **No diagnostic screenshot capture is wired into the mission cycle**
   — captures happen only transiently in memory for recognition; the
   pre-existing `diagnostics.py` path/metadata planning from an earlier
   stage is not connected to `mission.py`.
8. **GUI has no settings editor, no log viewer beyond one recent line
   per panel, no persistence of status across restarts.**
9. All limitations recorded in every prior TP-00x/RW-0x section of this
   document remain valid and are not superseded by MVP-001.

See `docs/MVP_UNVERIFIED.md` for the complete, categorized list (by
design / scope cut / not verified) and `docs/REAL_CAPTURE_CHECKLIST.md`
for the ordered path from here to something that could touch a real
game.

### Focused QA smoke instructions

QA is smoke-testing only per the packet (label
`MVP_SMOKE_PASS`/`MVP_SMOKE_FAIL`/`BLOCKED_REAL_ENVIRONMENT`; no AC
claims). Suggested minimal smoke path:

1. `pip install -e ".[dev]"` then `pytest` — expect 216 passed, 0
   failed. Re-run once or twice if any `tkinter`/`ttk` error appears in
   `test_gui.py` (see Limitations/flakiness note above — should be
   fixed, but this environment's Tk behavior may differ).
2. Copy both example configs (`configs/config.example.yaml` →
   `config.yaml`, `configs/mission.example.yaml` → `mission.yaml`);
   leaving `adb_mapping` all `null` is fine for this smoke check.
3. Run `python -m ldmanager.app` (or `scripts\run.bat`). Expect: a
   window opens showing 9 panels (LD1..LD9) plus Start All/Stop All,
   each panel showing "stopped" with Start/Stop buttons. Close the
   window normally.
4. Click **Start** on one panel. Expect: status flips to "running",
   and — because `adb_mapping` is unset/`PlaceholderRecognizer` never
   matches — within a few seconds the status should show an error
   (blank-serial `ValueError`, contained) or a `slot_recognition_failed`
   outcome, **never** a hang or a crash of the whole window. Click
   **Stop** on that same panel; confirm it stops without affecting the
   other 8 (still "stopped", untouched).
5. Optionally: run `scripts\build_windows.ps1`, then run the resulting
   `dist\ldmanager\ldmanager.exe` from a directory **with no
   `configs/config.yaml`** and confirm it exits promptly (code 1) with
   a clear stderr message rather than hanging or crashing silently
   (mirrors step 3.1 of this session's own verification above).
6. Confirm no real ADB/LDPlayer/game/login/global-mouse/DOM/credential
   code exists by spot-checking `src/ldmanager/` for any of those
   concepts (there should be none — grep for `pyautogui`, `pynput`,
   `selenium`, `requests`, `socket`, `password`, `token` outside of the
   existing redaction/config-rejection code, and find nothing new).

If step 3/4 cannot be exercised in the QA environment (no display, no
`adb`, etc.), that is exactly the `BLOCKED_REAL_ENVIRONMENT` case the
packet anticipates — steps 1 and 6 (and reading this HANDOFF section)
should still be possible anywhere.

---

## MVP-001-CV: Free regional-bounty five-slot mission-cycle extension

**Manager task packet: MVP-001-CV.** Queued immediately after MVP-001
(`ff6648d`/`f6af8ee`, confirmed by Manager as the submitted safe unit).
Implemented in the same Code worktree, same session, without
discarding or resetting MVP-001. QA will run a **combined MVP smoke**
(MVP-001 + MVP-001-CV together); this section is not an AC-PASS claim.

**Status: mock/configurable extension delivered and self-tested only.
AC-58..60 explicitly cannot pass without a customer/real environment
(see table). Not merged.**

### What changed structurally vs. MVP-001

MVP-001 shipped a simplified, generic 5-slot → single kill-check →
claim → reset cycle (`mission.py`/`mission_config.py`). MVP-001-CV adds
a **new, separate** module pair — `bounty_config.py` /
`bounty_mission.py` — that models the *actual* free regional-bounty
flow described in the customer video: per-slot select+classify,
structural (never cost-based) refresh-popup verification, a
two-condition mission-acceptance check, an explicit 0-199/200 gate
before any complete/reward action, and the full
complete→reward→claim→result→close→list→re-refresh→re-accept sequence.
`app.py` now wires the **new** bounty flow as the real app's cycle
function; the earlier `mission.py`/`mission_config.py` are **kept,
unchanged, and still fully tested** (backward compatible, not merged
into or replaced in place) but are no longer reachable from `app.py`.
`controller.py`/`gui.py` required **no changes** — `AccountWorker`'s
cycle-function contract is duck-typed on `.outcome`, so the richer
`BountyCycleResult` slots in without modifying worker/GUI/log wiring
("Keep GUI/status/log integration" — confirmed unchanged, all prior
`tests/test_controller.py`/`tests/test_gui.py` pass unmodified).

### AC-31..60 traceability (best-effort)

> As with every prior AC-numbered section in this document, the
> official AC catalog text is not available in this worktree. The
> mapping below follows the packet's own bullet order; QA should
> reconcile against the authoritative AC-31..60 definitions.

| AC | Requirement (from packet) | Evidence |
|---|---|---|
| AC-31 | Per account: select/check slots 1..5 | `bounty_mission._accept_or_refresh_slot()` — one `runner.run()` tap per slot via `slot_select_points[i]`, one per slot 1..5 |
| AC-32 | Classify slot status | `_mission_is_acceptable()` capture+check immediately after selection, before deciding refresh vs. accept |
| AC-33 | Open refresh only when needed | Refresh loop entered only when the immediate post-select check is not already acceptable |
| AC-34 | Identify refresh popup **structurally**, never by fixed/displayed cost | `_verify_refresh_popup()`: two independent labels (`refresh_popup_anchor_label`, `refresh_popup_title_label`); neither field is a cost value (`test_refresh_popup_fields_are_not_a_cost_field_by_construction`); `test_popup_detection_is_unaffected_by_variable_cost_signal` proves detection works with no "cost" label present at all |
| AC-35 | Tap confirm only if popup verified | Confirm (`refresh_confirm_point`) tapped only after `popup_verified` is truthy; `test_popup_not_structurally_verified_never_confirms` proves confirm is never sent otherwise |
| AC-36 | Inspect new mission after refresh | `_mission_is_acceptable()` re-run immediately after each confirm |
| AC-37 | Accept/preserve only when BOTH phrase AND qty 200 recognized | `_mission_is_acceptable()` requires `phrase.matched and quantity.matched` — two independent recognizer calls, `and`-combined |
| AC-38 | Phrase-only match must reject | `test_phrase_only_match_is_rejected_bounded_reroll` |
| AC-39 | Quantity-only match must reject | `test_quantity_only_match_is_rejected_bounded_reroll` |
| AC-40 | Otherwise: bounded reroll | `max_refresh_attempts` bound in `BountyMissionConfig`; `test_slot_refresh_is_bounded_when_never_acceptable` |
| AC-41 | Move to next slot only after verified acceptance | Slot loop `return`s `SLOT_ACCEPT_FAILED` (aborting the whole cycle, not silently skipping) if a slot never becomes acceptable — never advances on an unverified slot |
| AC-42 | After all five: observe kill progress | Kill-progress polling loop runs only after the slot `for` loop completes all 5 |
| AC-43 | 0-199/200 must never tap complete/reward | `test_kill_progress_incomplete_never_taps_complete_or_reward` — asserts `len(runner.calls) == 5` (only the 5 slot-selects; zero complete/reward/claim taps) |
| AC-44 | Only 200/200 **or** explicit complete state may proceed | `eligible = progress.matched or complete_badge.matched`; `test_kill_progress_via_explicit_complete_badge_is_also_eligible` proves the badge path alone is sufficient |
| AC-45 | Select mission for complete | `select_complete_point` tap, gated on `eligible` |
| AC-46 | Click complete | `complete_button_point` tap |
| AC-47 | Verify reward screen | Bounded `reward_screen_roi`/`reward_screen_label` check before claim |
| AC-48 | Claim | `claim_point` tap, only after `reward_ok` |
| AC-49 | Verify result screen | Bounded `result_screen_roi`/`result_screen_label` check after claim |
| AC-50 | Close result | `close_result_point` tap, only after `result_ok` |
| AC-51 | Mission list return verified | Bounded `mission_list_roi`/`mission_list_label` check after close |
| AC-52 | Re-refresh completed slot(s) | Second pass over all 5 slots via the same `_accept_or_refresh_slot()` helper after the claim flow |
| AC-53 | Accept new target | Same both-conditions check reused for the re-refresh pass |
| AC-54 | Repeat | `run_one_cycle()` returns `COMPLETED_CYCLE`; the caller (worker loop, unchanged from MVP-001) calls it again |
| AC-55 | Every action = capture → expected condition → one guarded touch → observe | Every `runner.run()` call site in `bounty_mission.py` is preceded by a condition check (selection is the one unconditional action, immediately followed by a capture+check) and every meaningful state transition is re-verified by a fresh capture afterward |
| AC-56 | Config carries paths/ROIs/coordinates/thresholds/retries/timeouts, transparent placeholders | `bounty_config.py` + `configs/bounty.example.yaml` — 20+ explicit fields, all placeholder example values, documented as such in comments |
| AC-57 | Never rely on one OCR output alone | Enforced structurally: acceptance = 2 recognizer calls (phrase+qty), popup = 2 recognizer calls (anchor+title), eligibility = 2 recognizer calls (progress OR badge) — no single-call decision point in the whole flow |
| **AC-58** | Real popup structural detection verified against actual customer environment | **Not verified — cannot pass without customer environment.** Only proven against `LabelMappingRecognizer`/`PlaceholderRecognizer` fakes in this session |
| **AC-59** | Real dual-condition (phrase + 200) recognition verified against actual game screens | **Not verified — cannot pass without customer environment.** Same limitation |
| **AC-60** | Full real reward/claim/result flow verified against actual customer environment | **Not verified — cannot pass without customer environment.** Same limitation |

Mock-test categories the packet required, and where each lives:
variable-cost-independence → AC-34 row; phrase-only/200-only reject →
AC-38/AC-39 rows; no complete/reward at 0-199 → AC-43 row; bounded
reroll → AC-40 row; full one-cycle state flow →
`test_full_cycle_reaches_completed_state_once`; account isolation/no
cross-serial → `test_two_accounts_use_independent_runners_and_serials`;
safe error on unknown screen →
`test_capture_unavailable_mid_slot_is_reported_without_crashing` (and,
structurally, every "not matched" branch throughout — an unrecognized
screen is never treated as a green light).

### Actual files changed/added

```
 New source (src/ldmanager/):
   bounty_config.py    (BountyMissionConfig + validated YAML loader)
   bounty_mission.py   (the actual free-regional-bounty state machine)

 Modified source:
   app.py               (build_controller()/main() now wire bounty_* instead
                         of mission_*; mission.py/mission_config.py untouched
                         and no longer imported by app.py)

 New tests:
   test_bounty_config.py (12), test_bounty_mission.py (11)

 Modified tests:
   test_app.py           (fixtures now write bounty.yaml, not mission.yaml)
   test_gitignore.py     (+2: bounty.yaml ignored, bounty.example.yaml tracked)

 New config:
   configs/bounty.example.yaml

 Modified:
   .gitignore            (+ configs/bounty.yaml)
   README.md             (MVP-001-CV banner, new "무료 지역 현상금 5-슬롯
                          흐름" section, project structure, Quick Start)
   docs/RUN_GUIDE.md      (bounty.yaml steps, updated "what Start does")
   docs/REAL_CAPTURE_CHECKLIST.md (new CV-specific §0, updated §2/§3)
   docs/MVP_UNVERIFIED.md (new "MVP-001-CV specific" section)
   docs/HANDOFF_CODE.md   (this section)
```

Untouched (regression preserved): `mission.py`, `mission_config.py`
(kept, tested, just unwired from `app.py`), `adb.py`, `config.py`,
`logs.py`, `redaction.py`, `paths.py`, `diagnostics.py`, `discovery.py`,
`screenshot.py`, `guarded_touch.py`, `coordinates.py`, `recognition.py`,
`controller.py`, `gui.py`, `models.py`, `cli.py`, all `scripts/*`.

### Commit(s)

- `6f32610` — "MVP-001-CV: free regional-bounty five-slot mission-cycle
  extension" (branch `kpj0526/Code`, gate `ff6648d`/`f6af8ee`). This
  HANDOFF hash-record update is the follow-up commit immediately after
  it. Not merged.

### Full test command / result

```
.venv\Scripts\python.exe -m pytest -v
```

Result: **241 passed**, 0 failed, 0 skipped (216 prior [MVP-001 +
everything before it] + 25 new/changed this extension: 12 in
`test_bounty_config.py` + 11 in `test_bounty_mission.py` + 2 in
`test_gitignore.py`). Re-run 3x consecutively: 241/241 each time. `git
status --short` confirmed no stray files after the run.

### Limitations

1. **AC-58..60 cannot pass without a customer/real environment** — see
   table above. Everything in this extension is verified only against
   `LabelMappingRecognizer`/`PlaceholderRecognizer` fakes and a
   `FakeAdbRunner`.
2. **`bounty.example.yaml`'s ROIs/coordinates/labels are illustrative,
   not calibrated** — never measured against a real screenshot or a
   real customer-video frame.
3. **The "classify status" step is a binary check** (already-acceptable
   vs. needs-refresh), not a richer multi-state classifier (e.g.
   distinguishing "empty slot" from "wrong mission" from "locked").
   This was a deliberate simplification to keep the mock tractable; the
   packet's "classify status" language is satisfied at this level but a
   real implementation may want finer-grained states.
4. **Live "current phase" is not surfaced to the GUI during a running
   cycle** — `on_phase` callback exists in `bounty_mission.run_one_cycle()`
   but `app.py`/`controller.py` don't wire it through to
   `AccountWorkerStatus.current_slot` yet (this gap already existed in
   MVP-001's `mission.py`/`on_slot_start`, carried forward unchanged;
   `current_slot` is only ever reset to `None` after a cycle completes,
   never updated live mid-cycle). GUI still correctly shows
   running/stopped/cycle-count/last-outcome/last-error/last-log-line.
5. **Popup structural verification uses exactly two fixed landmark
   fields**, not an arbitrary configurable list — sufficient for this
   mock and for the "never by cost" requirement, but a real popup might
   need more (or different) landmarks; extending `BountyMissionConfig`
   would be straightforward but wasn't done speculatively.
6. **No dependency was added** for this extension (still just PyYAML +
   pytest [+ optional pyinstaller]) — real recognition (AC-58/59) will
   require adding one per `docs/REAL_CAPTURE_CHECKLIST.md` §4.
7. All limitations recorded in every prior TP-00x/RW-0x/MVP-001 section
   of this document remain valid and are not superseded by
   MVP-001-CV.

### Focused QA smoke instructions (combined MVP-001 + MVP-001-CV)

1. `pip install -e ".[dev]"` then `pytest` — expect **241 passed**, 0
   failed.
2. Copy `configs/config.example.yaml` → `config.yaml` and
   `configs/bounty.example.yaml` → `bounty.yaml` (not
   `mission.example.yaml` — that belongs to the now-unwired earlier
   flow). `adb_mapping` all `null` is fine for this smoke check.
3. Run `python -m ldmanager.app` (or `scripts\run.bat`). Expect the
   same 9-panel + Start All/Stop All window as MVP-001's smoke test.
4. Click **Start** on one panel. Expect a contained error (blank-serial)
   or, once a serial is configured against nothing real, a
   `refresh_popup_not_verified`/`slot_accept_failed` outcome within a
   few seconds — never a hang, never a crash, never more than the
   bounded number of taps. Click **Stop**; confirm only that panel
   stops.
5. Spot-check `src/ldmanager/bounty_mission.py` and
   `src/ldmanager/bounty_config.py` for the same forbidden-concept
   absence as MVP-001 (no OCR/template library, no
   pyautogui/pynput/selenium/requests/socket, no credential handling).
6. If a real customer environment/video reference is available to QA:
   AC-58/59/60 are the only items that could even theoretically be
   assessed there — everything else (AC-31..57) is fully covered by
   the automated mock suite and does not require one.

As with MVP-001, `BLOCKED_REAL_ENVIRONMENT` is the expected/acceptable
outcome for anything requiring real `adb`/a display/a real game screen
in the QA environment — steps 1 and 5 should be possible anywhere.

---

## UI-ADB-001: GUI-driven LD1..LD9 ADB registration

**User-approved packet UI-ADB-001.** Queued after REL-0.1.0 release
prep (build/test verification only, no code changes — see that
section). Implemented in the same Code worktree, on top of clean
`c42289c`, without discarding prior work. Goal: the customer registers
LD1..LD9 ADB serials **from the GUI**, never by hand-editing YAML or
using a terminal.

**Status: implemented and self-tested only. Not merged, not
tagged/pushed/published** (per REL-0.1.0's note that Manager handles
release integration — unchanged by this packet).

### What was built

| Requirement (packet) | Delivered as |
|---|---|
| Global "Refresh ADB devices" | `LDManagerApp._on_refresh_devices()` — calls `discovery.discover_devices(runner)` (read-only `adb devices`), never `runner.run()` |
| Each LD panel shows mapping status | `AccountPanel.set_mapping_status()` — persisted serial + live `ConnectionStatus` + detail text |
| Select a discovered serial OR enter one explicitly | `ttk.Combobox` (editable, not read-only) populated from the last refresh's device list |
| Save / Clear | `AccountPanel` Save/Clear buttons → `LDManagerApp._on_save_mapping()`/`_on_clear_mapping()` → `config_mapping.save_account_serial()` |
| Persist valid mapping to ignored local config, reload panel state | `config_mapping.py` reads/writes `configs/config.yaml` (already git-ignored); every save/clear ends with `_apply_current_mapping_to_panels()` re-rendering from the (freshly re-read-on-success) mapping |
| Reuse existing explicit mapping validation | `config_mapping.save_account_serial()` calls `config.validate_adb_mapping()` (unknown-key/type checks, reused unmodified) + `adb.validate_serial()` (blank/whitespace check, reused unmodified) + an added duplicate-across-accounts check (see below) |
| Never auto-assign discovered devices | Combobox only *suggests*; the value actually saved is always exactly what `serial_var.get()` returns (user-picked or user-typed) — no code path writes a discovered serial without that round-trip through the widget |
| Reject blank/duplicate/malformed/unavailable visibly per account, prevent that account's start | Blank/duplicate/malformed → `MappingSaveResult(ok=False, ...)` shown via `panel.mapping_error_var` (per-panel, red text), nothing written. "Unavailable" (not found/offline/unauthorized/unknown/discovery-unavailable) → `ConnectionStatus != OK` → Start button left `disabled` (ttk-level; `.invoke()` is then a no-op) |
| Refresh/save issue no tap, start no worker | Refresh calls only `list_devices()`; Save/Clear call only `config_mapping.save_account_serial()` (pure file I/O) — neither ever calls `runner.run()` or `controller.start_account()`/`start_all()`. Tested directly (`test_refresh_devices_updates_serial_choices_with_no_tap_or_worker`, `test_save_and_clear_never_tap_or_start_a_worker`) |
| Preserve other accounts' mappings | `save_account_serial()` reads the full current mapping, mutates exactly one key, writes back all nine — tested (`test_save_preserves_other_accounts_mappings`, GUI-level `test_clear_removes_mapping_and_preserves_other_accounts`) |

### Design notes

- **`discovery.py` refactor** (no behavior change to the existing runner-driven path — see regression note below): extracted a pure `compute_account_connection_statuses(adb_mapping, devices)` from `build_account_connection_statuses(adb_mapping, runner)`, so the GUI can recompute per-account status from an **already-fetched** device list (cached from the last "Refresh ADB devices" click) without re-invoking `adb devices` on every save/clear. `build_account_connection_statuses()` now delegates to the pure function when discovery succeeds, and is otherwise unchanged.
  - **Regression found and fixed during this refactor** (caught before it shipped, not by pre-existing tests): a first-draft version of the split accidentally reclassified an *unmapped* account as `DISCOVERY_UNAVAILABLE` whenever discovery failed, instead of keeping it `UNMAPPED` (the original, correct behavior — an unmapped account's status doesn't depend on whether discovery succeeded). Fixed to preserve the exact original branching order; added
    `test_unmapped_account_stays_unmapped_even_when_discovery_fails` as a permanent regression guard.
- **Start-gating default is safe**: every panel's Start button is constructed already `disabled` and only enabled by `set_mapping_status()` when status is exactly `ConnectionStatus.OK` — a freshly-saved mapping does **not** auto-enable Start; a subsequent Refresh must confirm it live.
- **Save vs. Clear are distinct actions**: Save rejects a blank/whitespace value outright (visible per-account error); Clear is the dedicated action to remove a mapping and always succeeds (barring a write error).
- **Duplicate check is new, minimal logic** (not present in `config.validate_adb_mapping`, which only validates individual entries/unknown keys — duplicate detection across a *complete* 9-entry mapping already existed in `discovery.validate_complete_adb_mapping`, but that requires all nine to be non-null, which doesn't hold for an incremental GUI save flow). `config_mapping.save_account_serial()` adds a straightforward "does this serial already belong to a different account key" check against the current on-disk mapping before writing.
- **YAML round-trip re-serializes the file** (`yaml.safe_load` + `yaml.safe_dump`) — this preserves all other keys/sections (`logging`, `diagnostics`, etc.) and all nine `adb_mapping` entries, but does **not** preserve human-written comments if the user had copied the commented `config.example.yaml` and hand-edited it before ever using the GUI. Documented as a limitation (below) and in `docs/RUN_GUIDE.md`.

### Actual files changed/added

```
 New source (src/ldmanager/):
   config_mapping.py   (load_current_adb_mapping/save_account_serial;
                        pure config file I/O + validation, no ADB)

 Modified source:
   discovery.py   (+ compute_account_connection_statuses(); refactor of
                   build_account_connection_statuses(), same public
                   behavior, regression caught+fixed+tested)
   gui.py         (AccountPanel gets serial combobox + mapping status +
                   Save/Clear + Start-gating; LDManagerApp gets Refresh
                   ADB devices + adb_runner/config_path params +
                   mapping state/reload wiring)
   app.py         (main() now passes a SubprocessAdbRunner +
                   resolve_config_path() into LDManagerApp for the
                   Refresh button; build_controller()'s signature/
                   contract is unchanged)

 New tests:
   test_config_mapping.py (15: load defaults, save creates file, save+
   reload round-trip, blank/whitespace/malformed/duplicate rejection,
   same-value-to-same-account is not a duplicate, preserves other
   accounts' mappings, preserves unrelated config sections, clear
   removes/no-ops harmlessly/is never subject to duplicate-check,
   pre-existing malformed config blocks save with a clear error)

 Modified tests:
   test_discovery.py (+3: compute_* matches build_* for the same
   devices, compute_* never takes a runner, unmapped-stays-unmapped-
   under-discovery-failure regression guard)
   test_gui.py (+7 net, rewritten: start-blocked-before-OK,
   start/stop-work-once-OK [fixes an outdated assumption from before
   Start-gating existed], refresh updates serial choices with no tap/
   worker, save persists + Start stays blocked until next refresh, save
   rejects blank, save rejects duplicate without overwriting, clear
   removes + preserves other accounts, save+clear never tap or start a
   worker) — now uses a module-scoped tmp_path-based config_path +
   FakeAdbRunner fixture instead of a bare in-memory controller, so no
   test ever reads/writes the real repository's config.yaml
```

Untouched (regression preserved): `config.py`, `adb.py` (both reused,
not modified), `mission.py`/`mission_config.py`/`bounty_config.py`/
`bounty_mission.py`, `logs.py`, `redaction.py`, `paths.py`,
`diagnostics.py`, `screenshot.py`, `guarded_touch.py`, `coordinates.py`,
`recognition.py`, `controller.py` (no changes needed — still
duck-typed), `models.py`, `cli.py`, all `scripts/*`, all `configs/*`.

### Commit(s)

- `5b0862b` — "UI-ADB-001: GUI-driven LD1-LD9 ADB registration" (branch
  `kpj0526/Code`, on top of clean `c42289c`). This HANDOFF hash-record
  update is the follow-up commit immediately after it. Not tagged, not
  pushed, not published.

### Full test command / result

```
.venv\Scripts\python.exe -m pytest -v
```

Result: **266 passed**, 0 failed, 0 skipped (241 prior [MVP-001-CV +
everything before it] + 25 new/changed this packet: 15 in
`test_config_mapping.py` + 3 in `test_discovery.py` + 7 net in
`test_gui.py`). Re-run 4x consecutively during development: 266/266
each time (the module-scoped Tk fixture pattern from MVP-001 continues
to avoid the multi-`tk.Tk()` flakiness). `git status --short` confirmed
no stray files.

### Limitations

1. **Hand-written YAML comments are lost** on any GUI Save/Clear (file
   is re-serialized via `yaml.safe_dump`) — values/sections are all
   preserved, formatting/comments are not. Documented in
   `docs/RUN_GUIDE.md`.
2. **"Malformed" detection is scoped to what `adb.validate_serial()`
   already checks** (blank or containing whitespace) — there is no
   broader ADB-serial-format validator, since real serials have no
   single universal shape (`host:port`, `emulator-NNNN`, USB device
   IDs, ...). A syntactically-plausible-but-wrong serial (e.g. a typo)
   will save successfully and only surface as `device_not_found` on the
   next Refresh.
3. **No automatic Refresh on save/clear or on app launch.** The user
   must click "Refresh ADB devices" explicitly (at least once, and
   again after any mapping change) before Start becomes available for
   an account — by design (no ADB call happens without an explicit
   click), but means a first-time user must remember this two-step
   flow (Save, then Refresh) to actually enable Start.
4. **Discovered-device list is cached client-side between Refresh
   clicks.** If a device goes offline moments after a Refresh, the
   panel won't reflect that until the next Refresh — there is no
   background polling (intentional: avoids issuing ADB calls the user
   didn't ask for).
5. **No confirmation dialog before Clear** — clicking Clear removes
   that account's mapping immediately (still only that one account;
   still reversible by re-saving the same or a different serial).
6. All limitations recorded in every prior TP-00x/RW-0x/MVP-001/
   MVP-001-CV section of this document remain valid and are not
   superseded by UI-ADB-001.

### Known real-environment gaps (for Manager)

- Registration flow (Refresh/Save/Clear/Start-gating) has only been
  exercised against `FakeAdbRunner` — never a real `adb` binary or a
  real LDPlayer instance. Real `adb devices` output shape/timing
  against this project's parser (`adb.parse_adb_devices_output`) was
  already a known gap from TP-002/TP-003 and remains unverified here.
- No real multi-instance registration walkthrough (9 real LDPlayer
  windows, 9 real serials, real Refresh/Save cycles) has been
  performed.

### QA focus points

- Save/Clear rejection is **visible per account** and **never** writes
  a partial/invalid mapping (blank, malformed, duplicate) — verify
  against `configs/config.yaml` directly after an attempted bad save.
- Start is truly gated: saving a serial alone must not enable Start;
  only a subsequent Refresh confirming `ok` does. Stopping/clearing one
  account must never affect another (re-verify the MVP-001/MVP-001-CV
  controller-level guarantees still hold with the new mapping UI
  layered on top).
- Refresh/Save/Clear must never appear in any ADB "tap" log and must
  never start a worker — spot-check via the same
  `pyautogui`/`pynput`/`selenium`/socket/credential grep used in prior
  QA smoke steps, plus confirm `FakeAdbRunner.calls` (touches) stays
  empty across a Refresh/Save/Clear sequence in the automated suite
  (already asserted by `test_save_and_clear_never_tap_or_start_a_worker`
  — QA may want to reproduce manually too).

---

## REL-0.1.0-PKG-01: packaged distribution had no first-run configs

**Release defect packet REL-0.1.0-PKG-01.** Manager verified the
published ZIP contained `ldmanager.exe`/`_internal` but no `configs/`
files; since `app.py` requires `configs/config.yaml` +
`configs/bounty.yaml` to start, a customer extracting the ZIP and
double-clicking the exe got a console error and no GUI at all — not
launchable "out of the box." Fixed in the same Code worktree, on top
of clean `817183b`.

**Status: implemented and verified (including an actual built-exe
launch). Not tagged/pushed/published** — per this packet and the prior
REL-0.1.0 packet, Manager handles release integration.

### Fix: two complementary layers

1. **App-safe first-run bootstrap** (`src/ldmanager/bootstrap.py`,
   new) — `main()` now calls `bootstrap_default_configs()` before
   `build_controller()`. It creates `configs/config.yaml` from
   `configs/config.example.yaml`, and `configs/bounty.yaml` from
   `configs/bounty.example.yaml`, **only when the real file doesn't
   already exist** — it never overwrites an existing (possibly
   user-edited/already-registered) config. Every copied `adb_mapping`
   entry is `null` (nothing guessed); neither example file contains a
   credential (both already pass `config.py`'s/`bounty_config.py`'s
   own sensitive-key rejection, unmodified, before and after the
   copy). The example *source* files are located next to the running
   executable (`sys.executable`'s directory when frozen, via
   `app_base_dir()`) so they're found regardless of the process's
   working directory; the *target* location still uses the existing,
   unmodified `resolve_config_path()`/`resolve_bounty_config_path()`
   (CWD/env-var-based) so bootstrap and the normal config loader always
   agree on where the file lives.
2. **Packaging fix** (`scripts/build_windows.ps1`) — after PyInstaller
   finishes, the script now copies `configs/config.example.yaml`,
   `configs/bounty.example.yaml`, and the whole `templates/` folder
   into `dist/ldmanager/` (siblings of `ldmanager.exe`), and generates
   `dist/ldmanager/README_FIRST_RUN.txt`. This is what actually makes
   the bootstrap step above have something to bootstrap *from* once
   the exe is run outside this dev environment (a ZIP of
   `dist/ldmanager/` is now self-contained). Only `*.example.yaml` is
   ever copied — never a real, possibly-filled-in local `config.yaml`/
   `bounty.yaml` from the developer's own machine (guarded by
   `tests/test_release_packaging.py`).

### Actual files changed/added

```
 New source (src/ldmanager/):
   bootstrap.py   (app_base_dir(), bootstrap_default_configs())

 Modified source:
   app.py   (main() calls bootstrap_default_configs() first; prints
             its messages; otherwise unchanged)

 New tests:
   test_bootstrap.py (11): app_base_dir() frozen/unfrozen, creates both
   configs from examples, all-null adb_mapping, no sensitive key
   (verified via a real load_config() call, not text scanning),
   byte-identical to source examples, never overwrites an existing
   config.yaml/bounty.yaml (both directions), leaves the other file
   alone when only one is missing, safe no-op when no example is
   bundled, safe no-op (empty message list) on a second run.
   test_release_packaging.py (7): build script exists and references
   both example files + templates + $DistRoot\configs/\templates,
   build script never copies a bare (non-.example) config, build
   script generates the first-run README, source example configs/
   templates actually exist, RUN_GUIDE documents the bootstrap flow.

 Modified tests:
   test_app.py (+2 new tests; existing 3 fixed): ALL tests in this
   file now `monkeypatch.chdir(tmp_path)` -- see "regression found"
   below. New: first-run bootstrap -> build_controller() succeeds
   end-to-end (simulates a freshly extracted ZIP using this repo's own
   real example files copied into an isolated tmp_path); bootstrap
   never disturbs an already-registered config.yaml.

 Modified:
   scripts/build_windows.ps1 (packages configs/*.example.yaml +
   templates/ + generates README_FIRST_RUN.txt into dist/ldmanager/
   after the PyInstaller step)
   docs/RUN_GUIDE.md (rewrote §2 "Configure" to lead with bootstrap;
   removed a duplicated "2a" block introduced while editing; expanded
   §8 "Build" with the dist/ldmanager/ folder layout and bootstrap
   behavior for the packaged exe)
   docs/HANDOFF_CODE.md (this section)
```

Untouched: `config.py`, `bounty_config.py` (both reused unmodified by
bootstrap.py), `discovery.py`, `config_mapping.py`, `gui.py`,
`controller.py`, `mission.py`/`mission_config.py`, `bounty_mission.py`,
`adb.py`, `logs.py`, `redaction.py`, `paths.py`, `diagnostics.py`,
`screenshot.py`, `guarded_touch.py`, `coordinates.py`, `recognition.py`,
`models.py`, `cli.py`, `scripts/run.bat`/`run.ps1`/`entrypoint.py`, all
`configs/*.example.yaml` content, `templates/README.md` content.

### Regression found and fixed during this packet (test isolation, not a product bug)

While first running the full suite after adding bootstrap, two
`test_app.py` tests started failing because bootstrap correctly found
and copied **this actual repository's own real
`configs/*.example.yaml`** (since those tests ran from the repo root
with no `monkeypatch.chdir`, and `app_base_dir()` falls back to CWD
when unfrozen) — one of those runs briefly left a real, untracked
`configs/bounty.yaml` sitting in the actual repo working directory
(git-ignored, so never at risk of being committed, but still a real
on-disk side effect from a test run). Found, deleted, and fixed
properly: every test in `test_app.py` now isolates `CWD` via
`monkeypatch.chdir(tmp_path)`, which — as a welcome side effect — also
closes a pre-existing, previously-undocumented gap from MVP-001/
MVP-001-CV where `test_build_controller_succeeds_with_valid_configs_and_covers_all_accounts`
could leave real (empty) `logs/LD1..LD9/*.log` files in the repo root
too (same root cause: an unmounted CWD default). Verified clean via
`git status --short --ignored` after re-running the full suite
multiple times post-fix.

### Actual build + launch verification (this session)

```
scripts\build_windows.ps1
```
completed successfully. `dist\ldmanager\` afterward:
```
ldmanager.exe                        2,089,484 bytes
_internal\...                        (PyInstaller runtime)
configs\config.example.yaml          (template only)
configs\bounty.example.yaml          (template only)
templates\README.md
README_FIRST_RUN.txt
```
No `configs\config.yaml`/`configs\bounty.yaml` shipped (as intended —
only bootstrap, at first run, creates those).

**Fresh-extraction launch test**: copied the entire `dist\ldmanager\`
folder to a clean temp directory (`%TEMP%\ldmgr_zip_sim_pkg01`,
containing only what a customer's extracted ZIP would have — no
pre-existing `config.yaml`/`bounty.yaml`), then launched
`ldmanager.exe` from that folder via `Start-Process` (tracked by exact
PID, not an image-name kill):

- Process was **still running 4 seconds later**, with
  `MainWindowTitle = 'ldmanager (MVP)'` — direct confirmation the GUI
  window actually opened, not just that the process didn't crash.
- `configs\config.yaml` and `configs\bounty.yaml` were both freshly
  created by bootstrap.
- `configs\config.yaml`'s `adb_mapping` verified to have **all nine
  entries (`LD1`..`LD9`) as `null`** — no ADB workers/taps were ever
  possible since nothing was mapped, satisfying "no real ADB/workers."
- Cleanly terminated via `Stop-Process -Id <PID> -Force`; confirmed
  gone via `Get-Process`/`tasklist` afterward — no lingering process.
- Temp simulation directory removed afterward.

A second, complementary live-exe check (pre-seed an already-registered
`config.yaml`, launch, confirm it's byte-unchanged after) was started
but hit an environment/tooling path-permission error unrelated to
ldmanager itself (a `Remove-Item`/protected-path guard in this
session's sandbox) partway through and was not completed within this
session's time budget, per an explicit user instruction to stop
further live-exe verification once the primary fresh-extraction
evidence was judged sufficient. The "never overwrite an existing
config" guarantee is still verified — just at the automated-test level
rather than an additional live-exe run: `test_bootstrap.py`'s
`test_bootstrap_never_overwrites_an_existing_config`/
`..._bounty_config`/`..._leaves_config_untouched_when_only_bounty_is_missing`,
plus `test_app.py`'s
`test_bootstrap_does_not_disturb_an_already_registered_config`.

### Full test command / result

```
.venv\Scripts\python.exe -m pytest -v
```

Result: **286 passed**, 0 failed, 0 skipped (266 prior [UI-ADB-001 +
everything before it] + 20 new/changed: 11 in `test_bootstrap.py` + 7
in `test_release_packaging.py` + 2 new in `test_app.py`). `git status
--short --ignored` confirmed no stray files in the repo after the
suite run, the build, and both live-exe checks.

### Commit(s)

- `58eefc1` — "REL-0.1.0-PKG-01: bootstrap first-run configs, fix ZIP
  packaging" (branch `kpj0526/Code`, on top of clean `817183b`). This
  HANDOFF hash-record update is the follow-up commit immediately after
  it. Not tagged, not pushed, not published.

### Build artifact (this session)

- Path: `dist\ldmanager\ldmanager.exe` (plus `_internal\`,
  `configs\*.example.yaml`, `templates\`, `README_FIRST_RUN.txt` —
  all siblings, forming the full ZIP-ready `dist\ldmanager\` folder)
- Size: 2,089,484 bytes
- SHA-256: `959efc305eae22721b6374de23da8f21d4978ae06578dc8bc4b645afd0c9b5e5`
- `dist\`/`build\`/`*.spec` remain git-ignored, as before — this
  artifact is not part of the commit.

### Limitations

1. **CWD-dependence for a non-standard launch remains** (documented,
   not fixed — same underlying design as `resolve_config_path()`
   throughout the project): bootstrap always finds the bundled
   `*.example.yaml` files next to the exe, but creates
   `configs/config.yaml`/`configs/bounty.yaml` relative to the
   process's *working directory*. For the standard double-click launch
   these are the same folder. A shortcut with a custom "Start in"
   folder, or a command-line launch from elsewhere, would create the
   config there instead — still self-consistent (bootstrap and the app
   always agree), just not necessarily inside the exe's own folder.
2. **The "existing config untouched" guarantee was not re-confirmed
   against the real built exe in this session** (see above) — only at
   the automated-test level. Recommended as a QA follow-up if a fully
   live confirmation is wanted.
3. **No credential ever flows through bootstrap** by construction (it
   only copies two already-credential-free example files), but this
   also means bootstrap does nothing to help a user who needs to
   supply *real* ADB serials — that's still the GUI's
   Refresh/Save/Clear flow (UI-ADB-001), unchanged by this packet.
4. All limitations recorded in every prior TP-00x/RW-0x/MVP-001/
   MVP-001-CV/UI-ADB-001 section of this document remain valid and are
   not superseded by REL-0.1.0-PKG-01.

### QA focus points

- Extract `dist\ldmanager\` (or a ZIP of it) to a clean machine/folder
  with nothing pre-existing, double-click `ldmanager.exe`, confirm the
  GUI opens with no console/terminal interaction and every account
  shows unmapped/Start-disabled.
- Confirm `configs\config.yaml`/`configs\bounty.yaml` appear next to
  the exe after that first run, with `adb_mapping` all `null`.
- Re-run the exe a second time after registering an account (via
  UI-ADB-001's Save) and confirm that registration is still present —
  i.e., confirm the "never overwrite" guarantee end-to-end from a QA
  seat, closing the one live-exe check not completed in this session.
- Confirm no ADB tap/worker start occurs merely from launching the exe
  fresh (only Refresh/Save/Start, all user-initiated, should ever touch
  ADB or a worker) — consistent with prior packets' same requirement.

---

## REL-UPDATE-003: import + integrate v1.0.1's Test-capture readiness gate

**Manager Task Packet REL-UPDATE-003.** Import candidate from exact
remote tag `v1.0.1` (`299e7a91840505cc90dcbb6b6f9e2ad75ed3b1cf`) into
`kpj0526/Code`, non-destructively, integrating the per-account "Test
capture/template readiness gate" while preserving all existing
approved work.

**Status: merged, verified, remediated, and self-tested only. Not
tagged/pushed/published. Not claiming real LD/game success** — see
Limitations below for exactly what remains unverified.

### Ancestry inspection (done first, per the packet)

```
git fetch origin tag v1.0.1
git rev-parse v1.0.1                              # 299e7a91840505cc90dcbb6b6f9e2ad75ed3b1cf (exact match confirmed)
git merge-base v1.0.1 HEAD                          # a51ef07 (== our HEAD at the time)
git merge-base --is-ancestor v1.0.1 HEAD  -> NO
git merge-base --is-ancestor HEAD v1.0.1  -> YES
```

Our branch HEAD (`a51ef07`, the REL-0.1.0-PKG-01 hash-record commit)
was a **strict ancestor** of `v1.0.1` — the tag's 22 additional commits
(mostly `QA: merge X target`/`QA: record X pass/fail` records from a
parallel QA-side integration branch, plus two `feat:` commits at the
tip) build linearly on top of exactly our own history, adding nothing
that conflicts with it. This meant the merge was **structurally
guaranteed non-destructive**: nothing on `kpj0526/Code` could be lost,
reordered, or overwritten by merging a strict descendant. No
`reset`/force-checkout was used or needed; `git merge --no-ff v1.0.1`
completed with the `ort` strategy and **zero conflicts**.

### What importing v1.0.1 actually brought in

Per `git diff HEAD v1.0.1 --stat` (inspected file-by-file before
merging, per the packet's "inspect diff first" instruction): 46 files,
+1912/-63 lines. Highlights:

- **The requested feature** (`gui.py`, `controller.py`): per-account
  "Test capture" button + readiness gate — see Required Outcomes below.
- **`src/ldmanager/runtime.py`** (new): `AccountMissionRuntime`
  (per-account slot/phase state) + `click_and_verify()` (capture → tap
  → require the expected next template or a changed screen, saving a
  diagnostic capture and failing closed on a stale/unknown screen).
- **`src/ldmanager/calibration.py`** (new): a developer-mode-only real
  PNG crop tool (`crop_template()`) for turning a saved Test-capture
  PNG into a named template asset.
- **`src/ldmanager/recognition.py`**: adds `OpenCVTemplateRecognizer` —
  a *real*, working OpenCV template-matching recognizer (grayscale +
  edge-matching, ROI-scoped, fail-closed on any missing
  dependency/template/undersized ROI). `PlaceholderRecognizer` is
  unchanged and still present.
- **`templates/*.png`** (new, 20 files): real reference screenshots
  from the customer's game (button/slot/progress states) — these are
  real assets, not placeholders, bundled by the merge.
- **`src/ldmanager/adb.py`**: adds `resolve_adb_path()` (PATH/env-var/
  common-LDPlayer-install discovery, never guesses a port) and
  `InputGateAdbRunner` (see Remediation #1 below).
- **`bounty_mission.py`/`bounty_config.py`**: dynamic template-based
  tapping (`_tap_template`/`_tap_any_template`) with automatic fallback
  to the existing fixed-coordinate path when `template_map` is empty —
  **fully backward compatible**, which is why every pre-existing
  fake-runner/placeholder-recognizer test kept passing unmodified.
- `pyproject.toml`: new optional `[recognition]` extra
  (`opencv-python>=4.8`, `numpy>=1.24`) — not a hard dependency.
- Parallel QA-side docs/reports (`docs/ACCEPTANCE_STATUS.md`,
  `docs/PROJECT_SPEC.md`, `docs/TASK_PACKET.md`, `docs/TEST_PLAN.md`,
  `docs/PROGRESS.md`, `reports/QA_REPORT.md`, `CHANGELOG.md`,
  `VERSION`) — merged in as-is; these belong to a separate
  QA/Manager-side documentation convention and were not authored or
  altered by this Code-worktree session. `docs/HANDOFF_CODE.md` itself
  was **not** touched by v1.0.1 — every prior section above this one is
  exactly as this worktree left it.

### Required outcomes: confirmation

| # | Outcome | Where / how verified |
|---|---|---|
| 1 | Start disabled unless mapping OK **and** successful Test capture; LD1 readiness never enables LD2 | `AccountPanel._capture_ready` is a per-instance attribute, never shared; `_on_start()` checks `connection_status is OK and self._capture_ready`. `tests/test_gui.py::test_capture_readiness_is_account_local` sets LD1 ready and asserts LD2's Start stays disabled |
| 2 | Saving/clearing mapping resets only that account's readiness | `LDManagerApp._on_save_mapping`/`_on_clear_mapping` call `panel.set_capture_ready(False)` on **that** `AccountId`'s panel only. `tests/test_gui.py::test_serial_save_clears_capture_readiness` |
| 3 | Capture mismatch saves a diagnostic capture and blocks Start; calibration UI hidden unless developer mode | `LDManagerApp._on_capture_test()` always writes `diagnostics/captures/<LDx>/capture-<ts>.png` before checking the readiness callback, and calls `set_capture_ready(False)` on a non-match. The "Template calibration" button is constructed only `if os.environ.get("LDMANAGER_DEVELOPER_MODE") == "1"` |
| 4 | Full automated suite passes; Windows build succeeds | **302 passed**, 0 failed (see below). `scripts\build_windows.ps1` completed successfully, producing a working exe (see Build below) |
| 5 | HANDOFF updated with task ID/tag/files/tests/artifact/commit/limits/QA focus | This section |
| 6 | Commit on `kpj0526/Code`; no publish/tag/release; no claim of real LD/game success | Done — see Commits below. Explicitly not claimed anywhere in this section |

### Remediation: 3 defects found during diff inspection, fixed before commit

Found by reading the actual diff/content of every changed file before
merging (not merely trusting the diffstat) — exactly what "inspect
ancestry/diff first" is for. Fixed in a **separate commit** on top of
the merge, so the merge commit remains an unmodified record of the
tag's actual content.

1. **Safety gap — `InputGateAdbRunner` defined but never wired.**
   `adb.py` fully implements a live-mode input gate (`run()`/taps
   refused unless `live_enabled`; `list_devices`/`capture_binary`
   always pass through) — but `git grep -n "InputGateAdbRunner"` across
   the whole `v1.0.1` tree found it only in its own definition and one
   comment; `build_controller()` wired the *raw* `SubprocessAdbRunner`
   directly. Combined with outcome #1-3 (Start now genuinely gates on a
   real, working recognizer + real templates), this meant a verified
   Start could already send real ADB taps with **no separate opt-in** —
   in tension with the packet's explicit "do not claim real LD/game
   success." **Fixed**: `build_controller()` now always wraps the real
   runner in `InputGateAdbRunner`, `live_enabled=False` by default,
   opt-in only via a new `LDMANAGER_LIVE_MODE=1` environment variable
   (mirrors the existing `LDMANAGER_DEVELOPER_MODE` pattern already
   used for the calibration UI). Discovery/Refresh/Test-capture are
   unaffected either way (never gated). 5 new unit tests
   (`tests/test_adb.py`) + 3 integration tests (`tests/test_app.py`).
2. **Dead code — runtime-status sync unreachable.** In
   `controller.py`'s `AccountWorker._loop`, the block that copies
   `phase`/`locked_slots`/`slot_states` from the account's
   `AccountMissionRuntime` into `AccountWorkerStatus` (what feeds the
   GUI's phase line) sat *after* an unconditional `break` in the
   error-outcome branch — unreachable on literally every cycle, error
   or not. **Fixed**: moved into the same locked block as the other
   per-cycle status fields, so it runs on every cycle as clearly
   intended. 2 new regression tests (`tests/test_controller.py`),
   covering both a normal and an error-outcome cycle.
3. **Test-file corruption.** `tests/test_gui.py`'s
   `test_refresh_updates_panel_from_status_snapshot` had 3 of its 4
   assertions missing; they turned up appended to the end of an
   unrelated test, `test_serial_save_clears_capture_readiness`, where
   they passed only by accident (shared module-scoped `app` fixture +
   specific execution order left the referenced widgets in the right
   state anyway) — neither test actually verified what its name
   claimed. **Fixed**: each assertion restored to its correct test.

### Actual files changed

**By the merge** (46 files — see diffstat above for the complete,
verbatim list; not re-listed here to avoid duplication).

**By the remediation commit** (`a241c5f`, on top of the merge):
```
 src/ldmanager/app.py         (InputGateAdbRunner wiring + LDMANAGER_LIVE_MODE)
 src/ldmanager/controller.py  (runtime-status sync moved out of dead code)
 tests/test_adb.py            (+5: InputGateAdbRunner unit tests)
 tests/test_app.py            (+3: build_controller() live-mode wiring)
 tests/test_controller.py     (+2: runtime-status sync regression guards)
 tests/test_gui.py            (test content corruption fixed, no new tests)
```

### Test command / result

```
.venv\Scripts\python.exe -m pytest -v
```

Result: **302 passed**, 0 failed, 0 skipped (266 before this packet +
36 net: the merge itself added test_runtime.py [4] and modified
test_gui.py [net +2, before my content-corruption fix] = 292 total
right after merging, then this session's remediation added 10 more
[5 adb + 3 app + 2 controller] = 302). Re-run 4× consecutively
post-merge and again post-remediation: stable every time.

### Build + launch verification (this session)

```
scripts\build_windows.ps1
```
completed successfully — now installs `.[build,recognition]` (adds
`opencv-python`/`numpy`), and PyInstaller's `hook-cv2.py`/`hook-numpy.py`
processed cleanly (bundling the real OpenCV/numpy DLLs this time,
unlike the REL-0.1.0-PKG-01 build). `dist\ldmanager\` now also carries
`configs\*.example.yaml`, `templates\*.png` (real reference images),
`docs\RUN_GUIDE.md`, `docs\REAL_CAPTURE_CHECKLIST.md`, `VERSION`,
`CHANGELOG.md`, and `README_FIRST_RUN.txt`.

**Fresh-extraction launch test** (same protocol as REL-0.1.0-PKG-01):
copied `dist\ldmanager\` to a clean temp directory (no pre-existing
`config.yaml`/`bounty.yaml`), launched `ldmanager.exe` via
`Start-Process` (tracked by exact PID):

- Still running 5 seconds later, `MainWindowTitle = 'ldmanager (MVP)'`
  — GUI genuinely opened, including with the much larger
  OpenCV-bundled build.
- `configs\config.yaml`/`configs\bounty.yaml` both freshly bootstrapped;
  `config.yaml`'s `adb_mapping` verified to have all nine entries
  (`LD1`..`LD9`) as `null`.
- No `LDMANAGER_LIVE_MODE` set — confirmed by design/tests that Start
  therefore cannot issue a real tap even once mapping+capture are
  verified.
- Cleanly terminated via `Stop-Process -Id <PID> -Force`; confirmed
  gone via `Get-Process` afterward; no lingering process (`tasklist`
  clean). Temp simulation directory removed afterward.

### Build artifact (this session)

- Path: `dist\ldmanager\ldmanager.exe` (plus `_internal\` [now
  including bundled OpenCV/numpy], `configs\*.example.yaml`,
  `templates\*.png`, `docs\`, `VERSION`, `CHANGELOG.md`,
  `README_FIRST_RUN.txt`)
- Size: 4,784,289 bytes (exe only); ~170 MB total `dist\ldmanager\`
  folder (OpenCV/numpy DLLs account for the large jump vs. prior
  packets' ~2 MB exe / ~28 MB folder)
- SHA-256: `8939124e3ad958fb47e39979a39bce93437f7ecc86f406f30239f81c331ebd9f`
- `dist\`/`build\`/`*.spec` remain git-ignored — not part of any commit.

### Commits

- `e67fcad` — `Merge tag 'v1.0.1' (299e7a9) into kpj0526/Code --
  REL-UPDATE-003` (the tag's content, unmodified, via `git merge
  --no-ff`, zero conflicts)
- `a241c5f` — `REL-UPDATE-003: remediate 3 defects found during v1.0.1
  diff inspection` (the three fixes above)
- This HANDOFF hash-record update is the follow-up commit immediately
  after `a241c5f`. Not tagged, not pushed, not published, not merged
  into `main`.

### Limitations

1. **Real recognition/template matching is entirely unverified against
   a real game in this session.** `OpenCVTemplateRecognizer` and the 20
   bundled real template PNGs came from the imported candidate; no
   automated test (and no action in this session) exercised them
   against a real captured frame from a real device. Every automated
   test still uses `LabelMappingRecognizer`/`FakeAdbRunner`/
   `PlaceholderRecognizer`-shaped fakes.
2. **`InputGateAdbRunner`'s remediation makes real taps opt-in, not
   impossible.** Setting `LDMANAGER_LIVE_MODE=1` fully re-enables real
   ADB input the moment mapping+Test-capture succeed — this is a
   deliberate, minimal, reversible safety default, not a hard
   architectural barrier. Whoever controls deployment/distribution of a
   real build controls whether that env var is ever set.
3. **No real customer/LDPlayer environment was used anywhere in this
   session** — build + launch verification confirms the packaged exe
   *starts* and *self-bootstraps safely*, not that mission automation,
   recognition accuracy, or the calibration workflow work correctly
   against a real game. This session makes no such claim.
4. **The QA-side parallel documentation** (`docs/ACCEPTANCE_STATUS.md`,
   `docs/PROJECT_SPEC.md`, `docs/TASK_PACKET.md`, `docs/TEST_PLAN.md`,
   `docs/PROGRESS.md`, `reports/QA_REPORT.md`, `CHANGELOG.md`,
   `VERSION`) was imported verbatim and not reviewed/audited by this
   session beyond confirming it doesn't break anything — its content is
   attributable to whatever process produced `v1.0.1`, not to this
   Code-worktree session.
5. **`resolve_adb_path()`'s common-install-location probing**
   (`C:\LDPlayer`, `C:\Program Files\LDPlayer`,
   `C:\Program Files\dnplayerext2`) has not been verified against an
   actual LDPlayer installation in this session.
6. All limitations recorded in every prior TP-00x/RW-0x/MVP-001/
   MVP-001-CV/UI-ADB-001/REL-0.1.0-PKG-01 section of this document
   remain valid and are not superseded by REL-UPDATE-003.

### QA focus points

- Re-verify Required Outcomes 1-3 directly (per-account isolation,
  save/clear resets readiness, calibration hidden without developer
  mode) independently of this session's own test run.
- Confirm `LDMANAGER_LIVE_MODE` is **unset** in whatever environment QA
  smoke-tests in, and confirm that a verified Start (mapping OK +
  successful Test capture, if reachable) does **not** produce any real
  ADB tap in that state — this is the specific gap this session found
  and closed; re-verifying it independently is high-value.
- If a real device/game environment becomes available: this is the
  first packet where `OpenCVTemplateRecognizer` + real templates could
  be meaningfully exercised — but doing so is explicitly **not** claimed
  or requested as complete by this session.
- Confirm the Windows build artifact above launches and self-bootstraps
  identically to the REL-0.1.0-PKG-01 artifact, just larger (OpenCV
  bundled) — no new first-run friction introduced.
- Spot-check that `docs/HANDOFF_CODE.md` (this file) is the only
  Code-worktree documentation convention touched by this session — the
  QA-side docs/reports arrived via the merge, untouched by this
  session, and should be reviewed (if needed) through whatever process
  produced them.

## ADB-PATH-001: customer-visible ADB executable selection

**Manager packet**: `ADB-PATH-001 — customer-visible ADB executable
selection (2026-09-14)`, recorded on the `kpj0526/Manager` branch's
`docs/TASK_PACKET.md` (read there via `git show`, never checked out or
merged into this Code worktree). Trigger: a real customer screenshot
showed `Device discovery failed: ADB device listing failed:
FileNotFoundError` on `v1.0.1` even after manually setting `adb_path`
in `configs/config.yaml` and restarting.

### Status: implemented, tested, built. Not tagged, not pushed, not
published, not merged into `main`.

### Root-cause note (not exhaustively reproduced)

`main()`/`build_controller()` already wired one shared
`InputGateAdbRunner`-wrapped `SubprocessAdbRunner` to both the GUI and
every worker (fixed earlier, in `REL-UPDATE-003`) — so a "GUI uses a
different, unpathed runner" theory was ruled out directly by reading
that wiring. The more likely cause is a manual-YAML-editing pitfall: a
hand-typed, double-quoted Windows path (e.g.
`"C:\LDPlayer\LDPlayer14\adb.exe"`) is not valid YAML — `\L` is not a
recognized escape sequence — so the value that actually loaded may not
have been the path the customer saw on screen. This was not proven
with a literal repro in this session; instead, ADB-PATH-001 removes
the entire manual-YAML-editing step, which is the fix the packet asks
for regardless of the precise original cause.

### Acceptance criteria

| AC | Description | Status |
|----|--------------|--------|
| ADBPATH-01 | GUI shows configured/resolved ADB executable state | Done — new "ADB executable:" row shows the live `configured: ... effective: ... [found/NOT FOUND]` string, recomputed via the existing `resolve_adb_path()` after every load/Save/Clear |
| ADBPATH-02 | User can choose a real local `adb.exe` without terminal/YAML editing; invalid path visibly rejected | Done — Browse opens a native file picker (`.exe` filter); Save validates the typed/picked path exists as a file before writing anything, else shows the error in a dedicated `adb_path_error_var` label and writes nothing |
| ADBPATH-03 | Configured path persists locally and enables read-only discovery after restart | Done — persisted via the existing `adb_path` YAML key (`save_adb_path()`/`load_current_adb_path()` in `config_mapping.py`), read back on next `LDManagerApp` construction |
| ADBPATH-04 | Discovery/path selection produces zero touch/Worker side effects, never assigns a serial automatically | Done — Browse/Save/Clear only ever call `list_devices()` (via the existing `_on_refresh_devices()`), never `run()`/a tap, never start a worker; covered by assertions on `fake_runner.calls` for the new controls specifically |
| ADBPATH-05 | Regression suite/build pass; QA can verify exact Code hash | Done — see Test results / Build artifact below |

### Actual files changed

- `src/ldmanager/adb.py` — added `SubprocessAdbRunner.set_adb_path()`
  (re-resolves and updates `self.adb_path` at runtime, no restart
  needed) and `InputGateAdbRunner.set_adb_path()`/`.adb_path` (a
  defensive pass-through via `getattr` — a wrapped runner without these
  is a safe no-op, never an `AttributeError`).
- `src/ldmanager/config_mapping.py` — added `AdbPathSaveError`,
  `AdbPathSaveResult`, `load_current_adb_path()`, `save_adb_path()`.
  Mirrors the existing `save_account_serial()` pattern: reuses
  `_load_raw_config`/`_write_raw_config`/`resolve_config_path`,
  fail-closed (rejects blank or a path that isn't an existing file,
  writes nothing on rejection), preserves every other top-level config
  section (`adb_mapping`, `logging`, ...) untouched, never deletes any
  file (clearing only ever writes the YAML value to `null`).
- `src/ldmanager/gui.py` — new "ADB executable:" row (`Entry` +
  Browse/Save/Clear buttons) between the global Start All/Stop All row
  and the per-account panel grid, plus a status label
  (configured/effective/found-or-not) and an error label. New handlers
  `_update_adb_path_status()`, `_on_browse_adb_path()`,
  `_on_save_adb_path()`, `_on_clear_adb_path()`. Save/Clear call the
  live runner's `set_adb_path()` (no restart) and then re-run the
  existing, still read-only `_on_refresh_devices()` so the effect is
  visible immediately.
- `tests/fakes.py` — added `adb_path`/`set_adb_path()` to
  `FakeAdbRunner`, mirroring `SubprocessAdbRunner`'s real shape, so GUI
  tests can assert the runner was reinitialized in place.
- `tests/test_adb.py` — 4 new tests for `set_adb_path()` on both
  `SubprocessAdbRunner` and `InputGateAdbRunner`, including that a
  missing explicit path is kept verbatim (never silently swapped to
  `"adb"`) so a later real call fails honestly against the path the
  user actually configured. The one pre-existing no-op test was
  updated to use a bespoke bare double (since `FakeAdbRunner` now has
  both attributes) so it still exercises the true no-`set_adb_path`
  case.
- `tests/test_config_mapping.py` — 9 new tests for
  `load_current_adb_path()`/`save_adb_path()`: missing-file default,
  read-back, blank rejection, missing-file rejection (fail-closed,
  nothing written), directory-not-a-file rejection, persist + reload,
  clear (never deletes the real file), and that `adb_mapping` and
  `adb_path` never clobber each other in the same config file.
- `tests/test_gui.py` — 4 new tests for the Browse/Save/Clear controls:
  Browse fills the entry without any tap; Save of a missing path is
  rejected visibly and persists nothing; Save of a real file persists,
  reinitializes the live runner (`fake_runner.adb_path`), and updates
  the status label, all with zero taps; Clear resets to auto-detect,
  same zero-tap guarantee.
- `docs/HANDOFF_CODE.md` — this section.

### Test results

```
python -m pytest -q
319 passed
```

Run 3x in a row for stability (consistent with this session's
established practice) — all 3 runs: `319 passed`, 0 failures, 0
flakes. (Prior baseline was 302; +4 `test_adb.py`, +9
`test_config_mapping.py`, +4 `test_gui.py` = +17 -> 319.)

Focused runs also independently confirmed:
```
python -m pytest -q tests/test_config_mapping.py       # 24 passed
python -m pytest -q tests/test_gui.py -k "adb_path"     #  4 passed
```

### Build artifact (this session)

- Path: `dist\ldmanager\ldmanager.exe` (plus `_internal\`,
  `configs\*.example.yaml`, `templates\*.png`, `docs\`, `VERSION`,
  `CHANGELOG.md`, `README_FIRST_RUN.txt`)
- Size: 4,809,353 bytes (exe only)
- SHA-256: `5d110c89df7fa23d1a05b62dbcd7caf87214eb7d94d3d2f8b3a751e83e54c56`
- Built via `scripts\build_windows.ps1`; no live-exe launch
  verification was performed in this session (build + full test suite
  were treated as sufficient evidence for this handoff, per the "urgent
  MVP priority, no extra scope" instruction; QA may perform live-launch
  verification independently).
- `dist\`/`build\`/`*.spec` remain git-ignored — not part of any
  commit.

### Commits

- `5ade5dc` — `ADB-PATH-001: GUI-visible ADB executable path selection`
  (implementation + tests + this HANDOFF section, in one commit)
- This hash-record update is the short follow-up commit immediately
  after `5ade5dc`.
- Not tagged, not pushed, not published, not merged into `main`.

### Limitations

1. **The precise original customer root cause (YAML backslash-escaping
   during manual editing) was not literally reproduced in this
   session** — see the root-cause note above. The fix addresses the
   entire class of problem (no more manual YAML editing needed) rather
   than a single confirmed mechanism.
2. **No live-exe launch verification was performed for this packet**
   (unlike `REL-UPDATE-003`, which did a PID-tracked launch/terminate
   check) — only `pytest` + the PyInstaller build itself were run, per
   this task's "urgent MVP priority, no extra scope" instruction. QA
   should perform an independent live-launch check of the new ADB
   executable row.
3. **`resolve_adb_path()`'s common-install-location probing and the
   real LDPlayer `adb.exe` itself remain unverified against an actual
   LDPlayer installation in this session** — same limitation as every
   prior packet; nothing in ADB-PATH-001 changes that.
4. All limitations recorded in every prior section of this document
   remain valid and are not superseded by ADB-PATH-001.

### QA focus points

- Reproduce the original customer flow end-to-end: launch the built
  exe, use Browse to pick a real local `adb.exe`, Save, confirm the
  status row flips to `[found]` and device discovery (Refresh) now
  lists real devices with **no** manual YAML editing at any point.
- Confirm an invalid/missing path (typo, moved file) is rejected
  visibly (`adb_path_error_var`) and that `configs/config.yaml`'s
  `adb_path` value is **not** changed by a rejected Save — re-open the
  file or restart the app to confirm the prior value (or none) is
  still what's active.
- Confirm Clear falls back to auto-detection (`resolve_adb_path()`'s
  PATH/common-install-location search) and that no file on disk is
  ever deleted by Clear — only the YAML value changes.
- Confirm zero-touch: across Browse/Save/Clear and the Refresh they
  trigger, no real ADB tap (`run()`) is ever issued and no worker is
  ever started — this is the core safety property of this packet and
  is covered by automated tests, but an independent live check adds
  confidence.
- Confirm the Windows build artifact above launches and shows the new
  "ADB executable:" row without regressing any prior packet's GUI
  behavior (mapping Save/Clear, Start/Stop gating, Test capture).

## GAME-CAL-001: configurable mission-screen recognition/calibration correction

**Manager task packet**: `GAME-CAL-001` (approved). Customer evidence
(1280x720 captures): LD1/LD3 valid completed Mission > Region > Free
Subjugation screen; LD4 in-progress "130/180" with a "6600" currency
action, plus a completed state. Current Test capture reported a
template mismatch even for valid mapped screens.

### Status: implemented, tested, built. Not tagged, not pushed, not
published, not merged into `main`. Narrowly scoped per Manager's
mid-task priority update -- no reroll/popup automation changes, no new
live automation.

### Root cause (customer-reported mismatch)

The existing Test-capture readiness gate (`app.py`'s `readiness_check`)
only ever looked for four very *specific*, sub-state-only templates (a
refresh-popup title, a reward-result header, a fixed "0/200" quantity
crop). None of those are present on a plain mission-list/detail screen,
and the "0/200" crop is tied to one specific mission's target quantity
-- it can never match a mission whose target is a different number
(e.g. the customer's real "130/180", target 180 not 200). A
correctly-mapped screen therefore reported MISMATCH essentially always.

### Customer clarification (mid-task, addressed in this same commit)

"자유 토벌작전" ("Free Subjugation") is a **mission-list panel title**,
not a global layout anchor -- it only appears for that one objective
type; other mission types show other titles. It must never be used as
a stable screen-layout anchor (that would reject every other mission's
valid screen as a MISMATCH). This is now an explicit, enforced
architectural separation -- see Actual files changed below.

### Acceptance criteria

| Requirement | Status |
|---|---|
| Configurable templates/ROIs/thresholds, calibrated to stable static anchors (Mission/Region/list-detail layout); never reward amount or dynamic progress as sole anchor | Done -- new `stable_screen_anchors`/`min_stable_anchor_matches` (`bounty_config.py`), consulted only for screen-layout confirmation, never for sub-state. Mission-*title* text (e.g. "자유 토벌작전") is explicitly excluded/documented as unsafe for this field. |
| Explicit completed vs. in-progress/currency/unknown/mismatch classification | Done -- `MissionScreenState` enum (`screen_classification.classify_screen`), five-way, ordered COMPLETED > CURRENCY_ACTION > IN_PROGRESS > UNKNOWN, with MISMATCH gated separately by layout anchors. |
| Completion touch only after verified completed state, per-account explicit serial, fresh precondition, verified postcondition | Done -- `complete_mission_if_verified()`: validates serial, freshly captures + classifies COMPLETED, **additionally** freshly verifies the selected mission is the target objective (`assess_mission_target`), re-checks `should_stop()` immediately before the tap, then bounded-retries a fresh postcondition capture confirming the screen left the completed state. |
| Zero touch for 130/180 (progress), 6600/currency, unknown, mismatch; mismatch stays diagnostic/account-local | Done -- each state returns before any capture/tap beyond the precondition check; see fixture tests below. `readiness_check`'s MISMATCH path only ever sets that one account's Test-capture error label. |
| Target acceptance gate explicitly recognizes "모든 몬스터 처치" (configured phrase/criteria); other titles safely non-target/no-touch or follow the bounded flow | Done -- `assess_mission_target()` (shared implementation; `bounty_mission._mission_is_acceptable` now delegates to it) requires phrase AND quantity (or the combined template) to independently match; a different title is `NON_TARGET_CONFIRMED` (bounded reroll in the live cycle) or `RECOGNITION_FAILED` (fail-closed) -- never a screen-layout MISMATCH. |
| Preserve individual/global stop safety, no input after global stop, bounded retries/timeouts, worker containment, GUI startup | Preserved -- `run_one_cycle`/`AccountWorker`/`AccountController` untouched; `complete_mission_if_verified` checks `should_stop()` before every capture and immediately before the tap; postcondition loop is bounded by `max_postcondition_attempts`. |
| Fixture/mock tests: differentiation, no-touch (progress/currency/unknown/mismatch), serial scope, title variation, regression; Windows build | Done -- see Test results below. |
| `docs/HANDOFF_CODE.md` updated, `NEEDS_REAL_TEST` retained; no push/tag/publish; no live game-success claim | This section; see Limitations. |

### Actual files changed

- `src/ldmanager/screen_classification.py` (**new**) -- `MissionScreenState`
  (COMPLETED/IN_PROGRESS/CURRENCY_ACTION/UNKNOWN/MISMATCH),
  `classify_screen()`, `capture_and_classify()`, `MissionAssessment` +
  `assess_mission_target()` (mission-title/OCR classification, shared
  with `bounty_mission.py`), `complete_mission_if_verified()` (the
  gated completion-touch primitive). No frame capture or tap happens
  anywhere in this module except that one function's own explicitly
  guarded tap.
- `src/ldmanager/bounty_config.py` -- new optional `BountyMissionConfig`
  fields: `stable_screen_anchors` (+ `AnchorSpec`), `min_stable_anchor_matches`,
  `currency_action_labels` (defaults to the existing four
  `button_refresh_*` variants), `in_progress_roi`/`in_progress_label`.
  All optional/backward-compatible (empty/unset = that check is
  skipped, never fabricated); `load_bounty_config()` parses and
  validates each, including that `in_progress_roi`/`in_progress_label`
  are only ever set together.
- `src/ldmanager/bounty_mission.py` -- `MissionAssessment` and
  `_mission_is_acceptable()`'s body moved to `screen_classification.py`
  (single shared implementation instead of two copies that could
  silently drift); `_mission_is_acceptable()` is now a one-line
  delegation, behavior unchanged (confirmed by the full, unmodified
  `test_bounty_mission.py` suite still passing). `run_one_cycle()`
  itself was **not** otherwise modified -- zero regression risk to its
  large existing tested state machine.
- `src/ldmanager/app.py` -- `readiness_check` (the customer-reported
  Test-capture gate) now calls `classify_screen()` instead of the old
  four-specific-template OR-check; MISMATCH is the only case reported
  as not-ready, with the specific anchor-count reason in the message.
- `configs/bounty.example.yaml` -- documents the new optional fields
  with placeholder values/commented examples, explicitly warning
  against using a mission-title panel label (e.g. "자유 토벌작전") as a
  `stable_screen_anchors` entry.
- `tests/test_screen_classification.py` (**new**, 26 tests) --
  `classify_screen` five-way differentiation (including priority
  ordering, partial `min_stable_anchor_matches`, legacy
  no-anchors-configured passthrough, and that a different mission title
  never causes MISMATCH); `capture_and_classify` capture-failure vs.
  success; `complete_mission_if_verified` zero-touch for
  in-progress/currency/unknown/mismatch/capture-failure/blank-serial/
  should-stop (both before capture and after precondition), a
  confirmed-target-and-completed real touch with verified postcondition,
  bounded postcondition failure (tap sent, `ok=False`), per-account
  serial isolation, and two title-variation no-touch regressions
  (uncertain-recognition fail-closed, and confident non-match).

### Test results

```
python -m pytest -q
345 passed
```

Run 3x in a row: `345 passed` every time, 0 failures, 0 flakes. (Prior
baseline 319 + 26 new `test_screen_classification.py` tests = 345; the
full existing `test_bounty_mission.py`/`test_app.py`/`test_gui.py`
suites are unmodified and still pass unchanged.)

### Build artifact (this session)

- Path: `dist\ldmanager\ldmanager.exe` (plus `_internal\`,
  `configs\*.example.yaml`, `templates\*.png`, `docs\`, `VERSION`,
  `CHANGELOG.md`, `README_FIRST_RUN.txt`)
- Size: 4,820,957 bytes
- SHA-256: `f389375ebe37de00950ec2fc1035229bf301dd0df9b54a8f6611bcc1f2aeef37`
- Built via `scripts\build_windows.ps1`. No live-exe launch verification
  or real-device run was performed (see Limitations/NEEDS_REAL_TEST).
- `dist\`/`build\`/`*.spec` remain git-ignored -- not part of any commit.

### Commits

- `6fa6d39` — `GAME-CAL-001: configurable mission-screen recognition/calibration`
  (implementation + tests + this HANDOFF section, in one commit)
- This hash-record update is the short follow-up commit immediately
  after `6fa6d39`.
- Not tagged, not pushed, not published, not merged into `main`.

### Limitations -- NEEDS_REAL_TEST

1. **No real device, no real template/anchor calibration, and no real
   game screen was used anywhere in this session.** `classify_screen`,
   `assess_mission_target`, and `complete_mission_if_verified` are
   exercised exclusively by in-memory fake/mock recognizers
   (`LabelMappingRecognizer` and small bespoke test doubles) against a
   minimal placeholder PNG. Real-device recognition accuracy against
   the customer's actual 1280x720 captures -- including whether the
   *new* `stable_screen_anchors`/`in_progress_*` templates this packet
   introduces can even be reliably calibrated from those screens --
   remains **`NEEDS_REAL_TEST`**, exactly as it has for every prior
   recognition-related packet in this document.
2. **No `stable_screen_anchors`/`in_progress_roi`/`in_progress_label`
   values were added to the real, git-ignored `configs/bounty.yaml`** --
   only the tracked `configs/bounty.example.yaml` documents the new
   optional fields with placeholders. A customer/QA environment must
   still calibrate real crops from real captures before these new
   checks do anything beyond "skipped" in a live run.
3. **This session makes no claim that the customer's original
   FileNotFoundError-adjacent Test-capture mismatch is now resolved
   end-to-end against their real client** -- only that the specific,
   identified *class* of bug (readiness gated on sub-state-only/
   digit-specific templates instead of stable screen-layout anchors) is
   fixed in code and covered by fixture tests. QA/customer must
   recalibrate real anchor templates and re-verify against the actual
   LD1/LD3/LD4 captures.
4. **`run_one_cycle()`'s live completion path was intentionally left
   unmodified** in this narrowly-scoped packet -- it already
   independently satisfies "no touch below completion, bounded" (prior,
   already-tested behavior) but does not yet call the new
   `complete_mission_if_verified()` primitive itself. Wiring that in is
   future work, not claimed done here.
5. All limitations recorded in every prior section of this document
   remain valid and are not superseded by GAME-CAL-001.

### QA focus points

- Independently verify the exact Code commit hash below.
- Re-run `pytest -q` (expect `345 passed`) and `tests/test_screen_classification.py`
  specifically (26 tests) to confirm the five-way classification,
  zero-touch guarantees, and title-variation regressions.
- Using the real customer captures (LD1/LD3/LD4), manually crop real
  `stable_screen_anchors` (Mission tab / Region tab / list-detail
  frame -- explicitly NOT the "자유 토벌작전" panel title) and a real
  `in_progress_roi`/`in_progress_label` template, add them to a local
  `configs/bounty.yaml`, and confirm Test-capture now reports the
  correct classification (not MISMATCH) for all three real screens.
- Confirm a non-"모든 몬스터 처치" mission (different title) on a real
  device is never tapped by `complete_mission_if_verified`, even if it
  visually shows a completed badge.
- Confirm zero real ADB taps occur for the 130/180 in-progress screen
  and the 6600-currency screen specifically, matching the customer's
  evidence screenshots.
- Confirm the Windows build artifact above launches without regressing
  any prior packet's GUI behavior.

## GAME-CAL-001 REAL-CAPTURE REWORK: calibrate from real customer PNGs

**Trigger**: `v1.0.3-rc.1` was withdrawn — the actual customer Test
capture still reported "Only 0/2 stable screen anchors matched" against
the prior GAME-CAL-001 commit's `stable_screen_anchors`, which had never
been calibrated against any real image (only mock/fake-recognizer
fixtures existed at that point). Manager/customer supplied 3 real,
original, unmodified 1280x720 LDPlayer captures and required real-asset
calibration + a reproducible test proving them recognized before any
completion claim.

### Status: implemented, tested (against real assets), built. Not
tagged, not pushed, not published, not merged into `main`.

### Real captures used (documented provenance)

Copied verbatim into `tests/fixtures/game_cal_001/source/` — see that
directory's `PROVENANCE.md` for the full table (exact pixel regions,
what each derived crop is used for, what remains uncalibrated):

| File | Shows |
|---|---|
| `completed_target.png` | 임무 > 지역 > 자유 토벌작전 detail, 모든 몬스터 처치, **완료** (completed), 완료 button visible |
| `in_progress_target.png` | Same mission type, different instance: 모든 몬스터 처치, **(16/165)**, currency action cost 4400 |
| `non_target.png` | A **different** mission: 야왕궁 토벌작전, 냉혈사 처치, **(0/450)**, currency action cost 4400, plus a 순간 이동 (teleport) button |

### Root cause of the withdrawal (real measurement, not guesswork)

Direct measurement against the real captures found the true defect:
`OpenCVTemplateRecognizer`'s per-image `cv2.equalizeHist` normalization
(applied independently to a small template and to the much larger
frame/ROI it's searched in) *degrades* an otherwise-exact match — a
pixel-perfect crop matched via raw (non-equalized) grayscale scored
`0.9999`/`1.0`, the *same* match after equalization scored only
`0.68`-`0.81` (below the `0.8` threshold). Simply recalibrating ROIs
against real pixels was not sufficient by itself; the recognizer's own
matching method needed the same real-data proof.

### Fixes

1. **`src/ldmanager/recognition.py`** — `OpenCVTemplateRecognizer.recognize()`
   now evaluates a third candidate: plain (non-equalized) grayscale
   `TM_CCOEFF_NORMED`, alongside the existing histogram-equalized and
   Canny-edge candidates, taking whichever of the three scores highest
   (never averaged, never removing either existing candidate — pure
   addition, so no existing behavior can regress). Verified against the
   3 real captures: true matches now score `~0.9994-1.0`, confidently
   different content scores `~0.45-0.52` — a huge, real margin at the
   existing `0.8` threshold.
2. **`configs/bounty.example.yaml`** — `screen_size` corrected to
   `1280x720` (the real captures' actual resolution; was a placeholder
   `960x540`, which would have produced wrongly-scaled real tap
   coordinates). `stable_screen_anchors` replaced with the two real,
   calibrated anchors (`mission_header`, `mission_objective_label`) —
   confirmed present, identically, on all 3 real captures regardless of
   mission title. `complete_state_roi`/`complete_state_label`
   recalibrated to the real "완료" badge crop and its real ROI.
   `currency_action_labels` set to the real `currency_action_4400` crop
   (confirmed present on both real non-completed captures).
   `template_map` gained the 5 new real-crop entries. The pre-existing
   `button_complete` template (from an earlier, separately-sourced
   packet) was independently confirmed, via direct measurement against
   these same 3 real captures, to also correctly detect the real
   completed state (`0.90` vs `~0.69`) — a useful cross-check, left in
   place as the (still-correct) primary completed-signal path.
3. **New real template crops**, derived (cropped, lossless) from the
   real captures, added to both `tests/fixtures/game_cal_001/templates/`
   and the shipped `templates/`: `mission_header.png`,
   `mission_objective_label.png`, `complete_badge.png`,
   `currency_action_4400.png`, `mission_target_phrase.png` (the "모든
   몬스터 처치" objective phrase alone, no digits/quantity — wired via
   `screen_classification.py`'s single-template target fast path,
   renamed from the old, misleadingly-digit-specific
   `target_all_monsters_0_of_200` key to `mission_target_phrase` to
   match what it actually is now).
4. **`src/ldmanager/screen_classification.py` / `bounty_mission.py`** —
   only the key rename above; no behavioral logic changes beyond what
   REAL-CAPTURE REWORK's prior GAME-CAL-001 commit already established.
5. **`tests/fixtures/game_cal_001/`** — the 3 real source PNGs +
   `PROVENANCE.md` (exact pixel regions, what's still `NEEDS_REAL_TEST`)
   + the 5 derived template crops, as controlled fixture resources.
6. **`templates/README.md`** — corrected a stale claim ("nothing reads
   from this directory yet") and documented which files are real vs.
   still-placeholder.

### Preserved safety requirements (all verified against the real captures)

- Variable mission titles never cause `MISMATCH`: `completed_target.png`
  and `in_progress_target.png` share one title ("자유 토벌작전"),
  `non_target.png` has a completely different one ("야왕궁 토벌작전") —
  all three classify as not-`MISMATCH` (test-proven).
- Both real non-completed captures (16/165 target-in-progress, 0/450
  non-target) produce **zero** ADB calls of any kind through
  `complete_mission_if_verified()` (test-proven, `runner.calls == []`).
- 순간 이동 (the teleport button visible only in `non_target.png`) is
  not a configured/searched label anywhere in this project — it cannot
  be tapped by any code path here, real or mock.
- Only the real completed + target-confirmed capture produces a tap,
  scoped to the one explicit serial passed in (test-proven).

### Actual files changed

- `src/ldmanager/recognition.py` — raw-grayscale third matching
  candidate (additive).
- `src/ldmanager/screen_classification.py`,
  `src/ldmanager/bounty_mission.py` — `mission_target_phrase` key
  rename (prose/key only).
- `configs/bounty.example.yaml` — real `screen_size`,
  `stable_screen_anchors`, `complete_state_roi/label`,
  `currency_action_labels`, and 5 new `template_map` entries.
- `templates/mission_header.png`, `templates/mission_objective_label.png`,
  `templates/complete_badge.png`, `templates/currency_action_4400.png`,
  `templates/mission_target_phrase.png` (new, real crops).
- `templates/README.md` — corrected stale claim.
- `tests/fixtures/game_cal_001/` (new) — `source/` (3 real captures),
  `templates/` (5 derived crops), `PROVENANCE.md`.
- `tests/test_screen_classification_real_assets.py` (new, 13 tests) —
  loads the real source PNGs + the real `OpenCVTemplateRecognizer` +
  the real shipped `configs/bounty.example.yaml`; proves: real captures
  are genuine 1280x720 PNGs; none of the 3 ever `MISMATCH`; the
  completed capture classifies `COMPLETED`+`TARGET_CONFIRMED` and the
  other two never do; both non-completed captures are `TARGET_CONFIRMED`
  or correctly `NON_TARGET_CONFIRMED` as appropriate; and
  `complete_mission_if_verified()` taps only the real completed capture
  (exactly once, correct serial) and produces zero calls for both real
  non-completed captures.
- `tests/test_bounty_config.py` — 2 existing tests updated for the
  corrected real `screen_size` (960->1280); no other existing test
  files touched, and no existing test's *assertions* changed beyond
  that literal resolution value.

### Test results

```
python -m pytest -q
358 passed
```

Run 3x in a row: `358 passed` every time, 0 failures, 0 flakes. (Prior
baseline 345 + 13 new `test_screen_classification_real_assets.py` = 358.)
Focused run: `pytest -q tests/test_screen_classification_real_assets.py`
→ `13 passed`, confirming the real-asset proof independently.

### Build artifact (this session)

- Path: `dist\ldmanager\ldmanager.exe` (plus `_internal\`,
  `configs\*.example.yaml`, `templates\*.png` — including the 5 new
  real crops — `docs\`, `VERSION`, `CHANGELOG.md`,
  `README_FIRST_RUN.txt`)
- Size: 4,821,052 bytes
- SHA-256: `c7ff93fdfa2823381aa306a32b35f0696bc311451db86d20b85c67d02a8cbf3c`
- Built via `scripts\build_windows.ps1`. No live-exe launch or real
  LDPlayer/ADB run was performed.
- `dist\`/`build\`/`*.spec` remain git-ignored — not part of any commit.

### Commits

- `4688104` — `GAME-CAL-001 REAL-CAPTURE REWORK: calibrate from real
  customer PNGs` (implementation + real-asset fixtures + tests + this
  HANDOFF section, in one commit)
- This hash-record update is the short follow-up commit immediately
  after `4688104`.
- Not tagged, not pushed, not published, not merged into `main`.

### Limitations -- NEEDS_REAL_TEST (unchanged posture, narrower gaps)

1. **Only one currency cost (4400) has a real example.** A mission
   whose currency-action cost differs is not covered by
   `currency_action_4400.png` alone — same OR-list pattern as
   `button_refresh_4400/6600/9900/14900` would need more real crops to
   extend. See `PROVENANCE.md`.
2. **No distinct real "in progress" (non-currency) indicator exists**
   in the supplied captures; `in_progress_roi`/`in_progress_label`
   remain uncalibrated by design (both real non-completed examples
   safely classify as `CURRENCY_ACTION` instead — still zero-touch).
3. **Only the initial Mission > Region > detail view is covered.** The
   refresh-popup/reward/claim/result/mission-list screens used by the
   rest of `bounty_mission.run_one_cycle` have no real capture in this
   fixture set and remain placeholder-calibrated.
4. **No live device, no real ADB pipeline, and no real completion tap
   against an actual LDPlayer instance was exercised anywhere in this
   packet** — every test in `test_screen_classification_real_assets.py`
   loads a static real PNG entirely offline; `FakeAdbRunner` stands in
   for the ADB transport (it is real *image* data flowing through a
   real recognizer, not a real *device*).
5. All limitations recorded in every prior section of this document
   (including the earlier `GAME-CAL-001` section immediately above)
   remain valid except where explicitly narrowed here.

### QA focus points

- Independently verify the exact Code commit hash below.
- Re-run `pytest -q` (expect `358 passed`) and
  `tests/test_screen_classification_real_assets.py` specifically (13
  tests) — these load the real supplied PNGs directly from disk, so a
  broken calibration in `configs/bounty.example.yaml` will fail this
  file, not just a mock-based one.
- On a real device at the customer's actual 1280x720 resolution,
  confirm Test capture reports `stable screen anchors matched` (not
  MISMATCH) for a real, live captured frame of this same screen —
  this session's evidence is from 3 static supplied PNGs, not a live
  ADB capture.
- Confirm zero real ADB taps for a real 16/165-style in-progress screen
  and a real non-target-title screen, matching this session's offline
  proof.
- Confirm the Windows build artifact above launches and packages the 5
  new real template PNGs under `dist\ldmanager\templates\`.

## REL-003: replacement customer-test prerelease (v1.0.3-rc.2)

**Manager task packet**: `REL-003` (approved). User explicitly
authorized immediate customer-test deployment. Supersedes the
withdrawn `v1.0.3-rc.1` (see the `GAME-CAL-001 REAL-CAPTURE REWORK`
section immediately above this one for the fix that made this
replacement release possible).

### Status: published as a GitHub prerelease. CUSTOMER-TEST / MVP.
`NEEDS_REAL_TEST` — not final, no claim of live game success.

### Source

- Source commit (exact build input, no src changes since):
  `c814ae850f3cd89e9c5e0feefc451e9c90d7aeff` (`c814ae8`)
- Implementation commit: `4688104` (`GAME-CAL-001 REAL-CAPTURE REWORK:
  calibrate from real customer PNGs`)
- This section's own commit is tagged along with the release (a
  docs-only commit -- it changes no `src/` file, so the built artifact
  is unaffected; verified via `git diff --stat 4688104..HEAD -- src/`
  before tagging, output empty).

### Release

- Tag: `v1.0.3-rc.2` (did not previously exist; confirmed via `git tag -l`
  and `gh release list` before creating it)
- GitHub prerelease URL: https://github.com/kpj0526/LDplayer/releases/tag/v1.0.3-rc.2
- Marked explicitly: **CUSTOMER-TEST / MVP**, **NEEDS_REAL_TEST**, not
  final -- see the release body for the exact limitations text (mirrored
  below).
- Does **not** republish, retag, or edit the withdrawn `v1.0.3-rc.1` --
  that release remains untouched, still marked WITHDRAWN, and its asset
  hash (`4764fe903d4c2f7d5f7d4f1904d4e53d6ee0b964bc2d622d050a4c46960da959`)
  is not reused anywhere in this one.

### Build + package

- Built via `scripts\build_windows.ps1` from the exact source commit
  above (clean working tree, no uncommitted changes).
- `ldmanager.exe`: 4,821,052 bytes, SHA-256
  `ab693fff9e1a7ba78759add60b11b860ee9ca5d9d561582b574291344f9332bf`
  -- **distinct** from the withdrawn release's exe/zip hash.
- Packaged ZIP: `ldmanager-v1.0.3-rc.2-windows.zip`, 67,644,387 bytes,
  SHA-256 `174c34b625ad2087c5a070e604fbb8880e4f9d2935ec8e85829ab10844a4f6da`.
  Layout: a single top-level `ldmanager\` folder containing
  `ldmanager.exe`, `_internal\` (bundled Python/OpenCV/Tk runtime),
  `configs\*.example.yaml`, `templates\*.png` (**including the 5 real,
  customer-capture-calibrated crops**: `mission_header.png`,
  `mission_objective_label.png`, `complete_badge.png`,
  `currency_action_4400.png`, `mission_target_phrase.png`), `docs\
  RUN_GUIDE.md` + `docs\REAL_CAPTURE_CHECKLIST.md`, `VERSION`,
  `CHANGELOG.md`, `README_FIRST_RUN.txt` -- verified present via
  `unzip -l` before upload (not assumed).
- Zip and exe hashes both independently confirmed distinct from the
  withdrawn `v1.0.3-rc.1` asset.

### Commits / tag / push

- This handoff-update commit (docs-only) is on `kpj0526/Code`.
- Tag `v1.0.3-rc.2` created at this commit.
- Pushed: `kpj0526/Code` branch and the `v1.0.3-rc.2` tag only -- no
  other branch/tag was pushed or touched, `main` was not touched.

### Limitations (mirrored in the release body)

1. **CUSTOMER-TEST / MVP build, not a final release.** No claim of
   real LD/game completion success anywhere in this build, its
   templates, or this document.
2. **`NEEDS_REAL_TEST`**: the 5 real calibration templates are verified
   against 3 static, customer-supplied 1280x720 PNGs offline (see the
   `GAME-CAL-001 REAL-CAPTURE REWORK` section above) -- not against a
   live ADB capture from an actual running LDPlayer instance. No live
   ADB/LDPlayer/game session was operated anywhere in producing this
   release.
3. Only one currency-action cost (4400) and one mission-title pairing
   have real calibration; other missions/costs/screens in the five-slot
   flow remain placeholder-calibrated (unchanged from the section
   above).
4. All limitations recorded in every prior section of this document
   remain valid and are not superseded by this release.

### Customer safe-test steps (mirrored in the release body)

1. Extract the ZIP anywhere and run `ldmanager.exe` -- first launch
   self-creates `configs\config.yaml`/`configs\bounty.yaml` from the
   bundled examples; nothing is pre-filled or auto-detected as "ready."
2. Map **exactly one** account's ADB serial explicitly (Refresh ADB
   devices, then pick/type the serial for that one LDx panel, Save) --
   do not map all nine at once for a first test.
3. Use **Test capture** on that one account before doing anything else,
   and confirm the panel reports the screen as recognized (not a
   mismatch) before considering Start.
4. Begin with that **one** account only -- do not Start All.
5. **Stop immediately** if the panel reports a mismatch, an unknown
   screen, or any error -- do not continue running, and save/send the
   diagnostic capture it writes under `diagnostics\captures\<LDx>\`.
6. This build does not prove, and must not be treated as proving, that
   any real in-game action (mission completion, claim, etc.) succeeds
   on a live account -- treat any observed tap purely as a recognition/
   calibration test, not a production automation run.

### QA focus points

- Independently verify the exact asset SHA-256 above against the
  published release download, not against this document alone.
- Confirm the release is marked prerelease (not "Latest"), and that its
  body includes the CUSTOMER-TEST/MVP + NEEDS_REAL_TEST language and
  the safe-test steps above verbatim or equivalently.
- Confirm `v1.0.3-rc.1` is untouched (still WITHDRAWN, not edited, not
  retagged) and that its asset hash does not appear anywhere in this
  release's metadata.
- Confirm only `kpj0526/Code` and the `v1.0.3-rc.2` tag were pushed --
  no change to `main` or any other branch/tag.

## LIVE-SERIAL-001: repair live per-account serial propagation

**Manager task packet**: `LIVE-SERIAL-001` (approved corrective
packet). Customer live reproduction: LD1's GUI displayed mapping
``emulator-5554`` and was started; the worker crashed:

```
controller.py:127 _loop -> app.py:80 _cycle -> bounty_mission.py:373
run_one_cycle -> _accept_or_refresh_slot -> _tap_template -> _recognize
-> screenshot.py:71 capture_screenshot -> adb.py:149 validate_serial ->
ValueError: Invalid ADB serial: ''
```

### Status: implemented, tested, regression-verified. Not built (not
requested for this corrective packet), not tagged, not pushed, not
published. `v1.0.3-rc.2` is untouched.

### Root cause

`app.py`'s `_make_cycle_fn(account_id, serial, ...)` closed over a
plain **string** `serial`, resolved exactly **once**, when
`build_controller()` ran (typically at app launch, before any real
mapping exists -- bootstrap creates a null mapping). A later GUI Save
(`gui.py`'s `_on_save_mapping` -> `ldmanager.config_mapping.
save_account_serial`) correctly persists the new serial to
`configs/config.yaml` on disk, and the GUI panel correctly displays it
-- but the already-built worker's cycle function had no way to learn
about it: it kept using the original, blank string captured at
construction time. Clicking Start then ran a cycle whose very first
capture attempt (`_tap_template` -> `_recognize` ->
`capture_screenshot`) called `validate_serial("")`, raising. The
worker's outer exception handler contained the crash (it didn't take
down the app), but as an **uncaught exception** propagating through six
stack frames -- not the "fail account-locally BEFORE any capture/ADB/
touch call, as a contained result" behavior this packet requires.

### Fix

- **`src/ldmanager/app.py`** -- new `LiveSerialRegistry`: a small,
  thread-safe, per-`AccountId` string store. `build_controller()` now
  constructs one, seeds it from the config file (same as before), and
  exposes it as `controller.serial_registry` (mirrors the existing
  `controller.adb_runner`/`controller.readiness_check` bolt-on
  pattern from ADB-PATH-001/GAME-CAL-001 -- `AccountController`'s own
  class in `controller.py` is untouched). `_make_cycle_fn` no longer
  takes a plain string: it takes the registry, and reads
  `serial_registry.get(account_id)` **fresh, on every single call** --
  never cached, never captured once. A blank/absent result returns a
  structured `BountyCycleResult(BountyOutcome.CAPTURE_UNAVAILABLE, (),
  "<LDx>: no ADB serial configured...")` immediately -- zero
  capture/ADB/touch calls, no exception.
- **`src/ldmanager/gui.py`** -- new optional `serial_registry`
  constructor parameter (duck-typed: only `.set(account_id, serial)`
  is ever called; `None` is a safe no-op, preserving every existing
  caller). `_on_save_mapping`/`_on_clear_mapping` now call
  `self._serial_registry.set(account_id, ...)` immediately after a
  successful save/clear -- scoped to exactly that one `account_id`,
  never any other account's live value. `main()` wires
  `controller.serial_registry` through to `LDManagerApp`.
- No change to `bounty_mission.py`'s capture/recognize/tap helpers
  (`_recognize`, `_tap_template`, `_tap_any_template`,
  `_verify_refresh_popup`, ...) -- they already correctly receive and
  propagate the single `serial` parameter passed into `run_one_cycle`
  with no defaulting/inference/reuse; the bug was entirely upstream, in
  what value reached `run_one_cycle` in the first place. Fixing the
  source (the registry) transitively fixes every downstream helper.
- `controller.py` itself is **unchanged** -- `AccountWorker`/
  `AccountController`'s classes, and their own existing test suite,
  are untouched; the fix stays entirely in the wiring layer (`app.py`)
  plus the GUI's save/clear handlers, consistent with controller.py's
  own documented scope ("no ADB command construction... lives here").

### Acceptance criteria

| Requirement | Status |
|---|---|
| Configured LD1 `emulator-5554` reaches every cycle helper/capture/tap argv | Done -- `test_configured_serial_reaches_every_capture_and_tap_argv` asserts every recorded `FakeAdbRunner` call (both `capture_calls` and tap `calls`) uses exactly that serial, through the real `_make_cycle_fn` -> `run_one_cycle` -> `_accept_or_refresh_slot` -> `_tap_template`/`_recognize` -> `capture_screenshot` chain. |
| Blank/omitted serial causes zero ADB/capture/touch calls and a contained account error | Done -- `test_blank_registry_entry_causes_zero_adb_calls_and_a_contained_error`, `test_omitted_serial_after_explicit_clear_also_causes_zero_calls`: `runner.calls == []`, `runner.capture_calls == []`, a structured `CAPTURE_UNAVAILABLE` result (never an exception). `test_worker_started_with_blank_serial_is_contained_never_crashes_the_app` proves the same through a real `AccountWorker` thread. |
| No cross-account use | Done -- `test_registry_is_strictly_per_account_no_cross_account_use`, `test_two_accounts_share_one_registry_but_never_cross_use_serials` (two live accounts, two runners, each only ever receives its own serial). |
| Individual/global stop behavior preserved | Done -- `test_stopping_one_account_does_not_affect_another_with_live_registries`, `test_global_stop_all_still_sends_no_further_calls_with_a_live_registry` (same contracts as the pre-existing `test_controller.py` suite, now exercised alongside a live registry). |
| The exact customer crash scenario, end to end | Done -- `test_gui_save_after_build_lets_a_fresh_start_use_the_new_serial_no_restart`: builds a cycle function while the registry is still blank (matching `build_controller()`'s real timing), then live-updates the registry (matching a GUI Save) with **no rebuild**, then starts the worker -- confirms `errored is False`, the real serial reaches every ADB call, and the cycle completes normally. |
| GUI-facing propagation itself | Done -- `tests/test_gui.py`: `test_save_mapping_updates_the_live_serial_registry`, `test_clear_mapping_updates_the_live_serial_registry_to_blank`, `test_a_rejected_save_never_reaches_the_live_serial_registry`, `test_gui_without_a_serial_registry_never_raises_on_save_or_clear` (backward compatibility for a caller that never passes one). |

### Actual files changed

- `src/ldmanager/app.py` -- `LiveSerialRegistry` class; `_make_cycle_fn`
  reads it live; `build_controller()` constructs/seeds/exposes it;
  `main()` wires it into `LDManagerApp`.
- `src/ldmanager/gui.py` -- new `serial_registry` constructor param;
  `_on_save_mapping`/`_on_clear_mapping` propagate to it after a
  successful save/clear; module docstring updated.
- `tests/test_live_serial_propagation.py` (new, 13 tests) -- registry
  unit behavior, `_make_cycle_fn` isolation tests (blank vs.
  configured), the full customer-timeline `AccountWorker` reproduction,
  cross-account isolation, and individual/global stop preservation.
- `tests/test_gui.py` -- new `_FakeSerialRegistry` test double +
  `fake_serial_registry` fixture wired into the shared `app` fixture;
  4 new tests for the GUI-facing half of the propagation (including a
  no-registry backward-compatibility check that reuses the shared `app`
  fixture rather than a second `Tk()` root, avoiding this file's
  already-documented Tcl/Tk multi-root flakiness).

### Test results

```
python -m pytest -q
375 passed
```

Run 6x in a row: `375 passed` every time, 0 failures, 0 flakes, 0
warnings. (Prior baseline 358 + 13 `test_live_serial_propagation.py` +
4 `test_gui.py` = 375.) An initial version of the customer-timeline
`AccountWorker` reproduction test was itself flaky (a race where a
second mission cycle could start and be interrupted before the test
thread called `stop()`, overwriting `last_outcome`); fixed by having
the wrapped cycle function request its own worker's stop from inside
the worker thread, immediately after the first cycle returns, before
`AccountWorker._loop` re-checks its `while` condition -- confirmed
stable across 5 additional repeated runs of that file alone before
being folded back into the full-suite stability runs above.

### Commits

- `966ff15` — `LIVE-SERIAL-001: repair live per-account serial
  propagation` (implementation + tests + this HANDOFF section, in one
  commit)
- This hash-record update is the short follow-up commit immediately
  after `966ff15`.
- Not tagged, not pushed, not published. `v1.0.3-rc.2` (tag, release,
  and its asset) is completely untouched by this packet.

### Limitations

1. **No live ADB, LDPlayer, or game session was used anywhere in this
   packet** -- every test uses `FakeAdbRunner`/`LabelMappingRecognizer`
   against an in-memory mock five-slot cycle. The fix is verified at
   the level of "does the correct serial string reach every recorded
   ADB call," not against a real device.
2. **No Windows build was produced for this packet** (not requested in
   the approved task packet -- corrective code fix only, explicitly not
   altering the released `v1.0.3-rc.2`). QA reverifying this fix against
   a packaged build should build fresh from this commit using
   `scripts\build_windows.ps1`.
3. This fix addresses the specific propagation gap the customer hit
   (serial captured once at controller-build time). It does not
   introduce any new capability, screen, or recognition behavior --
   `bounty_mission.py`'s own mission-cycle logic is unchanged.
4. All limitations recorded in every prior section of this document
   remain valid and are not superseded by this packet.

### QA focus points

- Independently verify the exact Code commit hash below.
- Re-run `pytest -q` (expect `375 passed`) and
  `tests/test_live_serial_propagation.py` specifically (13 tests),
  ideally several times in a row, given the timing-sensitive nature of
  the real-`AccountWorker`-thread reproduction test.
- Reproduce the original customer sequence manually if a real
  LDPlayer/ADB environment is available: launch the app (fresh, null
  mapping), map LD1 to a real serial via the GUI, Save, then Start
  **without restarting the app** -- confirm no `ValueError: Invalid ADB
  serial` and that the worker's first cycle actually uses the
  just-saved serial (e.g. via its log/diagnostics).
- Confirm `v1.0.3-rc.2`'s tag, release, and asset hash are all
  unchanged from the `REL-003` section above.

## REL-004: customer-test prerelease with the LIVE-SERIAL-001 fix (v1.0.3-rc.3)

**Trigger**: user confirmed the published `v1.0.3-rc.2` release predated
the `LIVE-SERIAL-001` fix (a real customer crash: `ValueError: Invalid
ADB serial: ''` when Start was clicked shortly after a GUI mapping
Save, because the worker's cycle function had captured its serial once
at `build_controller()` time and never learned about the later Save).
User explicitly asked to publish the newer, fixed state as the new
customer-test prerelease ("새롭게된걸로변경해" — "change it to the
newer one").

### Status: published as a GitHub prerelease. CUSTOMER-TEST / MVP.
`NEEDS_REAL_TEST` — not final, no claim of live game success.

### Source

- Source commit (exact build input, working tree clean): `7cbd5d5`
  (`docs: record LIVE-SERIAL-001 commit hash in handoff`)
- Implementation commit: `966ff15` (`LIVE-SERIAL-001: repair live
  per-account serial propagation`)
- No `src/` changes between `966ff15` and the tagged commit (`git diff
  --stat 966ff15..HEAD` touches only `docs/HANDOFF_CODE.md`) --
  confirmed before building.

### Release

- Tag: `v1.0.3-rc.3` (did not previously exist)
- GitHub prerelease URL: https://github.com/kpj0526/LDplayer/releases/tag/v1.0.3-rc.3
- Marked explicitly: **CUSTOMER-TEST / MVP**, **NEEDS_REAL_TEST**, not
  final -- same limitations/safe-test-steps language as `REL-003`,
  updated to call out the serial-propagation fix.
- Supersedes `v1.0.3-rc.2` for customer testing going forward; `rc.2`
  itself is untouched (not edited, not retagged, not withdrawn -- its
  own limitation was narrower: it worked correctly as long as an
  account was mapped and saved *before* `build_controller()` ran, i.e.
  before the app's first launch after a config reset -- LIVE-SERIAL-001
  is specifically about a Save happening *after* the app is already
  running).

### Build + package

- Built via `scripts\build_windows.ps1` from the exact source commit
  above (clean working tree).
- `ldmanager.exe`: 4,823,381 bytes, SHA-256
  `a080e1388108e50f63b42fec90990da852ee64812398030bf9e2dc9dff7fe526`
  -- distinct from both `v1.0.3-rc.2`'s exe hash
  (`ab693fff9e1a7ba78759add60b11b860ee9ca5d9d561582b574291344f9332bf`)
  and the withdrawn `v1.0.3-rc.1`'s.
- Packaged ZIP: `ldmanager-v1.0.3-rc.3-windows.zip`, 67,644,402 bytes,
  SHA-256 `62a8bf9d8b474698d6b0ac28bf9f8b473e887246bc9875fab102c8afca72b6bb`
  -- distinct from `v1.0.3-rc.2`'s zip hash
  (`174c34b625ad2087c5a070e604fbb8880e4f9d2935ec8e85829ab10844a4f6da`).
  Contents verified via `unzip -l` before upload: `ldmanager.exe`, all
  5 real calibration templates (`mission_header.png`,
  `mission_objective_label.png`, `complete_badge.png`,
  `currency_action_4400.png`, `mission_target_phrase.png`),
  `docs\RUN_GUIDE.md` + `docs\REAL_CAPTURE_CHECKLIST.md`,
  `configs\*.example.yaml`, `VERSION`, `CHANGELOG.md`,
  `README_FIRST_RUN.txt`.

### Commits / tag / push

- This handoff-update commit (docs-only) is on `kpj0526/Code`.
- Tag `v1.0.3-rc.3` created at this commit.
- Pushed: `kpj0526/Code` branch (including the two LIVE-SERIAL-001
  commits that were sitting local-only before this task) and the
  `v1.0.3-rc.3` tag only -- no other branch/tag touched, `main` not
  touched.

### What's new vs. v1.0.3-rc.2

- The `LIVE-SERIAL-001` fix (see that section above): a mapping Save
  made *after* the app is already running now reaches an already-built
  worker's very next cycle immediately -- no app restart required, and
  a still-blank/not-yet-saved account fails as a contained, zero-touch
  result instead of an uncaught `ValueError`.
- No other behavioral change since `v1.0.3-rc.2`.

### Limitations (mirrored in the release body)

1. **CUSTOMER-TEST / MVP build, not a final release.** No claim of
   real LD/game completion success anywhere in this build.
2. **`NEEDS_REAL_TEST`**: recognition/calibration is verified against 3
   static, customer-supplied 1280x720 PNGs offline (`GAME-CAL-001
   REAL-CAPTURE REWORK`), and the serial-propagation fix is verified
   with fake ADB/recognizer doubles (`LIVE-SERIAL-001`) -- neither was
   exercised against a live ADB capture from a running LDPlayer
   instance. No live ADB/LDPlayer/game session was operated anywhere in
   producing this release.
3. Only one currency-action cost and one mission-title pairing have
   real calibration; other missions/costs/screens remain placeholder.
4. All limitations recorded in every prior section of this document
   remain valid and are not superseded by this release.

### Customer safe-test steps (mirrored in the release body)

1. Extract the ZIP anywhere and run `ldmanager.exe`.
2. Map **exactly one** account's ADB serial explicitly (Refresh ADB
   devices, then pick/type the serial for that one LDx panel, Save).
3. Use **Test capture** on that one account before doing anything else,
   and confirm the panel reports the screen as recognized (not a
   mismatch) before considering Start.
4. Begin with that **one** account only -- do not Start All.
5. Start can now safely follow a Save made in the same session, with no
   app restart needed (the fix this release adds).
6. **Stop immediately** if the panel reports a mismatch, an unknown
   screen, or any error -- save/send the diagnostic capture written
   under `diagnostics\captures\<LDx>\`.
7. This build does not prove, and must not be treated as proving, that
   any real in-game action succeeds on a live account.

### QA focus points

- Independently verify the exact asset SHA-256 above against the
  published release download.
- Confirm the release is marked prerelease, includes the
  CUSTOMER-TEST/MVP + NEEDS_REAL_TEST language, and calls out the
  LIVE-SERIAL-001 fix.
- Confirm `v1.0.3-rc.1` and `v1.0.3-rc.2` are both untouched.
- Reproduce the original crash scenario if a real environment is
  available: map an account *after* the app is already running, Save,
  then Start without restarting -- confirm no `ValueError` and that the
  correct serial is used.

## TAP-FALLBACK-CRASH-001: fix UnboundLocalError on a real dynamic-tap miss

**Trigger**: user-supplied live screenshot of the running app (on
`v1.0.3-rc.2`). LD1's Test capture succeeded (`Screen verified:
completed (mission_header, mission_objective_label, button_complete)`,
mapping `emulator-5558 [ok]`), but the account panel showed:

```
ERROR
UnboundLocalError: cannot access local variable 'select' where it is
not associated with a value
```

### Status: implemented, tested, regression-verified.

### Root cause

`bounty_mission.py`'s dynamic-tap/fixed-fallback pattern, used
throughout `run_one_cycle`/`_accept_or_refresh_slot`, has this shape:

```python
dynamic_select = _tap_template(runner, serial, config, recognizer, "mission_slot_unselected")
if dynamic_select is None:
    select = runner.run(...)          # select is only ever assigned here
    selected_ok = select.ok
else:
    selected_ok = dynamic_select
if not selected_ok:
    ... f"... (rc={select.returncode})" ...   # referenced unconditionally
```

`_tap_template`/`_tap_any_template` return exactly one of three things:
`None` (the label isn't configured in `template_map` at all -- legacy/
fixture mode), `False` (a real capture happened but no confident match,
or the located tap itself failed), or `True` (the tap succeeded). The
failure-detail f-string assumed `select`/`open_popup`/`confirm` was
always assigned, but it is **only** assigned in the `dynamic_* is None`
branch. Once a real `mission_slot_unselected` template is configured
(as it has been since the original customer-video asset set) and the
live frame simply doesn't show a confident match for it -- e.g. the
account is sitting on a *different* screen, such as the already-
completed detail view in the customer's screenshot -- `_tap_template`
correctly returns `False`, the `else` branch runs, `select` is never
created, and the very next line's `select.returncode` raises
`UnboundLocalError`. This is a real, previously-undetected defect that
predates every packet in this document except its accidental exposure:
it stayed dormant as long as a "no confident match" ADB response was
rare/never hit in whatever was previously tested, and became visible
the moment a real, correctly-calibrated template started returning a
genuine `False` against a real capture.

The exact same shape exists at two more call sites in the same
function: the refresh-popup-open tap (`open_popup.returncode`) and the
refresh-confirm tap (`confirm.returncode`). The other four dynamic-tap
sites in `run_one_cycle` (select-complete, complete, claim, close) use
a plain string detail message with no `.returncode` reference, so they
were never affected.

### Fix

`src/ldmanager/bounty_mission.py` -- all three affected sites now build
a `*_detail` string that is assigned on **both** branches: `f"rc={...}"`
when the fixed-point fallback actually ran, or a fixed, honest
"template-based tap: no confident match, or the located tap itself
failed" string when the dynamic (template) path was taken (there is no
ADB `returncode` to report there -- either no confident match was found
at all, or the tap dispatched from that match itself failed). No
control flow, no outcome, no touch/capture behavior changed -- this is
purely a "the failure-detail message must never reference a value that
was never computed" fix.

### Regression tests

`tests/test_bounty_mission.py` -- new `_ConfidentNoMatchRecognizer`
test double (reports a genuinely confident `NO_MATCH`, not `UNKNOWN`,
so `_mission_is_acceptable` reaches `NON_TARGET_CONFIRMED` rather than
short-circuiting to `RECOGNITION_FAILED` -- needed to actually reach
the refresh-open/confirm steps in a test) plus 3 new tests, one per
affected call site, each configuring a real template for that one
asset with a recognizer that confidently does not match it:

- `test_slot_select_dynamic_template_no_match_is_a_structured_error_not_a_crash`
- `test_refresh_open_dynamic_template_no_match_is_a_structured_error_not_a_crash`
- `test_refresh_confirm_dynamic_template_no_match_is_a_structured_error_not_a_crash`

Each asserts `run_one_cycle` does **not** raise, returns
`BountyOutcome.CAPTURE_UNAVAILABLE` with the expected failure-detail
text, reproducing the exact customer crash shape for all three call
sites (not just the one the customer happened to hit first).

### Test results

```
python -m pytest -q
378 passed
```

Run 3x in a row: `378 passed` every time, 0 failures. (Prior baseline
375 + 3 new tests = 378.)

### Commits

- `ae0de2e` — `TAP-FALLBACK-CRASH-001: fix UnboundLocalError on a real
  dynamic-tap miss` (implementation + tests + this HANDOFF section, in
  one commit)
- This hash-record update is the short follow-up commit immediately
  after `ae0de2e`.

### Limitations

1. No live ADB/LDPlayer/game session was used to reproduce this --
   fixed and verified entirely from the customer's screenshot plus
   direct source-code tracing and fake-recognizer regression tests.
2. This fix addresses the specific "unassigned variable referenced in
   a failure-detail message" defect at exactly the three call sites
   that had it. It does not change any recognition/calibration/
   completion-gating behavior from prior packets.
3. All limitations recorded in every prior section of this document
   remain valid and are not superseded by this packet.

### QA focus points

- Independently verify the exact Code commit hash below.
- Re-run `pytest -q` (expect `378 passed`), especially
  `tests/test_bounty_mission.py -k dynamic_template_no_match` (3
  tests).
- On a real device if available: reproduce the original customer
  condition (an account sitting on a screen where `mission_slot_
  unselected` doesn't confidently match, e.g. an already-completed
  mission detail view) and confirm the account panel now shows a plain
  "select tap failed (template-based tap: ...)" error message instead
  of an `UnboundLocalError` traceback.

## SLOT-SELECT-CALIBRATION-001: slot selection is now always position-based

**Trigger**: after `TAP-FALLBACK-CRASH-001` shipped (`v1.0.3-rc.4`), the
user reported Start still didn't work on a real device -- no more
crash, but a `capture_unavailable` error, even with LD1 sitting on the
real 임무 목록 (mission list) screen. A new real 1280x720 capture was
supplied to diagnose it further.

### Status: implemented, tested, regression-verified.

### Root cause (deeper than TAP-FALLBACK-CRASH-001)

`TAP-FALLBACK-CRASH-001` fixed the crash itself, but the underlying
call it wrapped -- `_tap_template(runner, serial, config, recognizer,
"mission_slot_unselected")` -- was still structurally unable to
succeed in production. Two independent problems, both found by
measuring the real supplied capture
(`tests/fixtures/game_cal_001/source_extra/mission_list_row1_completed.png`):

1. **The configured crop bakes in the mission title text** ("자유
   토벌작전") -- the exact anti-pattern `GAME-CAL-001` already
   eliminated elsewhere in this project. A different mission title
   would never match it at all.
2. **Template matching cannot express "the Nth row".** `_tap_template`
   searches the *entire frame* for the single highest-confidence match
   and taps wherever that lands. With 4-5 visually identical
   "자유 토벌작전" rows on screen, this mechanism has no way to
   distinguish slot 1 from slot 3 -- it can only ever say "somewhere a
   matching row exists," never "row `slot_index` specifically."
   Worse: once `config.template_map` has *any* real entries (as
   production always does), `_tap_template` treats an unconfigured or
   non-matching label as a confident, hard `False` -- it never silently
   falls back to a fixed point. So simply leaving
   `mission_slot_unselected`/`mission_slot_selected` out of
   `template_map` (which the prior packet already did) does **not**
   restore the old fixed-point behavior; it still returns `False`, so
   Start would remain non-functional (safely erroring, but never
   actually selecting a slot) without a deeper fix.

### Fix

`src/ldmanager/bounty_mission.py` -- slot selection
(`_accept_or_refresh_slot`) and "select the completed mission"
(`run_one_cycle`) no longer attempt template matching at all. Both now
tap `config.slot_select_points[slot_index - 1]` /
`config.select_complete_point` directly and unconditionally --
position-based tapping is the mechanism actually suited to "pick the
Nth row of a list," and template matching's earlier
dynamic-with-fixed-fallback design is retained only where it's the
right tool (refresh-open, refresh-confirm, accept, complete-button,
claim, close -- each targets one specific, visually distinct button,
not one of several identical-looking rows).

`configs/bounty.example.yaml` -- `slot_select_points`/
`select_complete_point` replaced with **real, measured** coordinates:
row-band boundaries were found by scanning mean column brightness (not
eyeballed) across the real capture's list column, giving row centers
y = 0.3069 / 0.4194 / 0.5333 / 0.6458 / 0.7597 (x = 0.1172 throughout).
The prior placeholder values (evenly spaced 0.20/0.35/0.50/0.65/0.80)
were off by up to 0.11 -- comfortably enough to miss a ~0.097-tall row
band entirely, which independently explains why slot selection could
never have worked correctly even before any template was involved.
`mission_slot_unselected`/`mission_slot_selected` remain deliberately
unmapped, now with an explicit comment explaining why real crops should
not be added for them without solving problem (2) above first.

### Regression tests

- `tests/test_bounty_mission.py`:
  - `test_slot_select_is_always_position_based_never_template_matched`
    -- a confidently-non-matching recognizer (which would have blocked
    the old template-based select) no longer blocks slot selection at
    all; the cycle proceeds past it to the next real check.
  - `test_slot_select_tap_uses_the_exact_configured_slot_select_point`
    -- asserts the recorded tap argv matches
    `slot_select_points[0]` exactly.
- `tests/test_bounty_config.py`:
  - `test_example_bounty_config_slot_select_points_are_real_calibrated_values`
    -- guards the shipped example config against silently drifting back
    to the old placeholder values.
  - `test_example_bounty_config_never_maps_the_unreliable_slot_templates`
    -- guards against re-adding `mission_slot_unselected`/
    `mission_slot_selected` to `template_map` (now dead weight; would
    mislead a future calibration effort).
- `tests/fixtures/game_cal_001/source_extra/mission_list_row1_completed.png`
  (new) + `PROVENANCE.md` updated with the measured row-band evidence.

### Test results

```
python -m pytest -q
381 passed
```

Run 3x in a row: `381 passed` every time, 0 failures. (Prior baseline
378 + 1 net new `test_bounty_mission.py` test (one replaced by two) + 2
new `test_bounty_config.py` tests = 381.)

### Commits

- `d30534e` — `SLOT-SELECT-CALIBRATION-001: slot selection is now
  always position-based` (implementation + tests + this HANDOFF
  section, in one commit)
- This hash-record update is the short follow-up commit immediately
  after `d30534e`.

### Limitations

1. `select_complete_point` still always taps the row-1 position --
   it does not yet track *which* of the 5 locked slots actually became
   eligible/complete (same limitation the old placeholder implicitly
   had; not newly introduced or newly fixed here).
2. No live ADB/LDPlayer/game session was used to verify this fix --
   the real capture was static (customer-supplied), and every test uses
   `FakeAdbRunner`. Position-based tapping's real-world accuracy against
   the customer's actual live client is `NEEDS_REAL_TEST`.
3. The refresh-popup/reward/claim/result screens later in the same
   five-slot flow remain uncalibrated placeholders -- this packet did
   not touch them.
4. All limitations recorded in every prior section of this document
   remain valid and are not superseded by this packet.

### QA focus points

- Independently verify the exact Code commit hash below.
- Re-run `pytest -q` (expect `381 passed`).
- On a real device: with LD1 on the real 임무 목록 screen, click Start
  and confirm slot 1 is actually tapped (visually, or via the
  diagnostic capture written after the tap) at the real row-1 position,
  not somewhere else, and that the flow proceeds past slot selection
  rather than immediately failing again.

## DIAGNOSTIC-DETAIL-001: surface the real failure reason, not just the outcome

**Trigger**: after `SLOT-SELECT-CALIBRATION-001` shipped
(`v1.0.3-rc.5`), the user reported LD1 still stopped with a generic
`capture_unavailable` (cycles: 2, `locked: 0/5`) on a real device. The
GUI/log showed only `"capture_unavailable: account worker stopped"` --
tracing the code confirmed `bounty_mission.run_one_cycle`'s own
specific, per-step failure reason (`BountyCycleResult.detail`, e.g.
`"Slot 1: select tap failed (rc=1)."`) was computed but **never
surfaced anywhere** -- not the GUI, not the per-account log file. This
made the customer's real failure impossible to diagnose from a
screenshot alone.

### Status: implemented, tested, regression-verified. Pure
observability fix -- no capture/ADB/touch/outcome behavior changed.

### Fix

`src/ldmanager/controller.py` -- `AccountWorker._loop` now reads
`getattr(result, "detail", "")` (duck-typed, exactly like the existing
`outcome`/`.value` handling -- a result with no `.detail` at all is a
safe no-op, never an error) and appends it to:
- `status.last_error` (error-outcome cycles)
- every `_append_log(...)` line (error and non-error cycles alike)
- the per-account log file (`self._logger.error`/`.info`, now with a
  `detail=%s` field) -- already passes through the existing
  `SensitiveDataRedactionFilter` exactly like every other logged
  message, so this doesn't bypass any existing secret-redaction
  safeguard.

### Regression tests

`tests/test_controller.py` -- new `_DummyOutcomeWithDetail` test
double + 3 tests:
- `test_error_cycle_detail_reaches_last_error_and_recent_log`
- `test_non_error_cycle_detail_also_reaches_recent_log`
- `test_a_result_without_detail_is_a_safe_noop_never_raises` (backward
  compatibility with every existing plain `_DummyOutcome`-shaped fake
  used throughout the rest of this file/project)

### Test results

```
python -m pytest -q
384 passed
```

Run 3x in a row: `384 passed` every time, 0 failures. (Prior baseline
381 + 3 new tests = 384.)

### Commits

- `4224ccc` — `DIAGNOSTIC-DETAIL-001: surface the real failure reason,
  not just outcome` (implementation + tests + this HANDOFF section, in
  one commit)
- This hash-record update is the short follow-up commit immediately
  after `4224ccc`.

### Limitations

1. This is purely an observability fix. It does not change, and is not
   claimed to fix, whatever the customer's real underlying
   `capture_unavailable` cause turns out to be on their live device --
   that remains open, and this fix exists specifically so the *next*
   occurrence is diagnosable from the GUI/log directly instead of
   needing a screenshot round-trip.
2. No live ADB/LDPlayer/game session was used to verify this --
   verified with fake cycle-result doubles only.
3. All limitations recorded in every prior section of this document
   remain valid and are not superseded by this packet.

### QA focus points

- Independently verify the exact Code commit hash below.
- Re-run `pytest -q` (expect `384 passed`).
- On a real device: reproduce any error condition and confirm the GUI
  panel's error text and the per-account log file now both show a
  specific reason (e.g. "Slot 1: select tap failed (rc=...)") rather
  than just a bare outcome name like "capture_unavailable".

## STDERR-DETAIL-001: include the real ADB stderr text, not just rc=N

**Trigger**: `DIAGNOSTIC-DETAIL-001` (`v1.0.3-rc.6`) let the user see the
first real, specific failure from their live device:
`"Slot 1: select tap failed (rc=125)."` — but a bare return code alone
still wasn't enough to know *why* the tap failed.

### Status: implemented, tested, regression-verified. Pure
observability fix -- no capture/ADB/touch/outcome behavior changed.

### Fix

`src/ldmanager/bounty_mission.py` -- new `_short()` helper (trims/
one-lines a raw ADB `stderr` string, safe on empty/`None`). The three
select/refresh-open/refresh-confirm tap-failure details (already fixed
for the `UnboundLocalError` in `TAP-FALLBACK-CRASH-001`) and the
select-complete tap-failure detail (added in
`SLOT-SELECT-CALIBRATION-001`) now all include `stderr=...` alongside
`rc=...`. This text still passes through the per-account logger's
existing `SensitiveDataRedactionFilter` once `controller.py` logs it
(`DIAGNOSTIC-DETAIL-001`) -- unchanged safety posture, an ADB tap's
stderr is not expected to ever contain credential-shaped text but the
filter remains the actual safety net regardless.

### Regression tests

`tests/test_bounty_mission.py` --
`test_select_tap_failure_detail_includes_the_real_adb_stderr`: a canned
`AdbCommandResult(returncode=125, stderr="error: device offline")` for
the exact slot-1 select tap argv, asserting both `"rc=125"` and
`"error: device offline"` appear in the result detail.

### Test results

```
python -m pytest -q
385 passed
```

Run 3x in a row: `385 passed` every time, 0 failures. (Prior baseline
384 + 1 new test = 385.)

### Commits

- `9f765de` — `STDERR-DETAIL-001: include the real ADB stderr text, not
  just rc=N` (implementation + tests + this HANDOFF section, in one
  commit)
- This hash-record update is the short follow-up commit immediately
  after `9f765de`.

### Limitations

1. Pure observability fix. Does not fix or claim to fix the customer's
   real `rc=125` cause on their live device -- exists so the actual ADB
   error text is visible for the next diagnosis step.
2. No live ADB/LDPlayer/game session was used to verify this -- a
   canned fake `AdbCommandResult` was used, not a real `rc=125` capture
   from the field.
3. All limitations recorded in every prior section of this document
   remain valid and are not superseded by this packet.

### QA focus points

- Independently verify the exact Code commit hash below.
- Re-run `pytest -q` (expect `385 passed`).
- On the customer's real device: reproduce the `rc=125` select-tap
  failure and confirm the GUI/log now show the actual `stderr` text
  from `adb shell input tap`, not just the bare return code.

## REWARD-SCREEN-CALIBRATION-001: real calibration for the reward-claim screen

**Trigger**: after `SLOT-SELECT-CALIBRATION-001` + `DIAGNOSTIC-DETAIL-001`
+ `STDERR-DETAIL-001` shipped, the user enabled `LDMANAGER_LIVE_MODE=1`
and ran a real live cycle: all 5 slots were genuinely accepted
(`locked: 5/5`), the real complete tap was sent, and the account
reached the actual "보상 받기" (Get Reward) screen for the first time --
then stalled on `reward_verify_failed` ("Reward screen never verified
within 3 attempt(s).").

### Status: implemented, tested, regression-verified.

### Root cause

`reward_screen_roi`/`reward_screen_label`/`claim_point`/
`button_claim_reward` had never been calibrated against any real
capture -- only the initial Mission > Region > detail screen was
(`GAME-CAL-001`). The customer supplied a real 1280x720 Test-capture of
the actual reward screen (`tests/fixtures/game_cal_001/source_extra/
reward_screen.png`), enabling the same real-crop calibration approach
used throughout this project.

### Fix

Two real crops taken from the supplied capture (measured pixel bands,
verified by direct visual inspection):
- `reward_odds_label.png` -- the "확률" (odds/probability) label:
  generic reward-screen UI chrome, present regardless of mission title,
  confirmed (real `OpenCVTemplateRecognizer`) to match only this real
  capture and none of the other 4 real captures on file.
- `reward_claim_button.png` -- the real "보상 받기" button, replacing
  the old `button_claim_reward` template_map entry's never-validated
  placeholder file (same config key, so no call-site changes needed).

`configs/bounty.example.yaml`: `reward_screen_roi`/`reward_screen_label`
now point at the real odds-label crop/ROI; `claim_point` set to the
real, measured button center (fixed fallback only -- the dynamic
`button_claim_reward` template is tried first).

### Regression tests

`tests/test_reward_screen_real_assets.py` (new, 5 tests) -- loads the
real reward-screen capture + the real recognizer + the real shipped
config: confirms it's a genuine 1280x720 PNG; confirms
`reward_screen_label` matches only that capture and never any of the
other 4 real captures on file (explicit false-positive guard); same
for the `button_claim_reward` template.

### Test results

```
python -m pytest -q
390 passed
```

Run 3x in a row: `390 passed` every time, 0 failures. (Prior baseline
385 + 5 new tests = 390.)

### Commits

- `622d7ad` — `REWARD-SCREEN-CALIBRATION-001: real calibration for the
  reward-claim screen` (implementation + tests + this HANDOFF section,
  in one commit)
- This hash-record update is the short follow-up commit immediately
  after `622d7ad`.

### Limitations

1. Only the reward-claim screen is now real-calibrated. The
   result-screen/close/mission-list-return steps later in the same
   flow remain uncalibrated placeholders -- the next real blocker, if
   any, is most likely there.
2. `button_claim_reward`'s real-vs-false-capture confidence margin is
   narrower (~0.77 vs ~1.0) than the other real crops in this project
   (~0.45-0.52 vs ~1.0) -- both the real "완료" button and the real
   "보상 받기" button apparently share similar gold-bordered button
   graphic styling. Still correctly classified at the configured 0.8
   threshold, but a smaller margin than ideal; worth reconfirming if a
   real live run ever produces a surprising false match here.
3. This calibration came from ONE real capture supplied by the
   customer via a phone-camera video, then a clean in-app Test-capture
   of the same screen -- the clean capture (not the video) is what was
   actually used for pixel measurement.
4. All limitations recorded in every prior section of this document
   remain valid and are not superseded by this packet.

### QA focus points

- Independently verify the exact Code commit hash below.
- Re-run `pytest -q` (expect `390 passed`) and
  `tests/test_reward_screen_real_assets.py` specifically.
- On a real device: confirm a full live cycle (with `LDMANAGER_LIVE_MODE=1`)
  now proceeds past the reward-claim step instead of stalling on
  `reward_verify_failed`, and confirm the next real blocker (if any) is
  in the result/close/mission-list steps, which remain uncalibrated.

## COMPLETE-DETAIL-001: actionable detail for complete/claim/close, + a false-positive safety check

**Trigger**: after `REWARD-SCREEN-CALIBRATION-001` shipped, the user's
live run progressed further and then stalled with a bare
`"Complete tap failed."` -- no rc/stderr, no reason. Given the
possibility that this indicated an unsafe false-positive completion
trigger, this was investigated as a safety question first, before
being treated as a plain observability gap.

### Status: implemented, tested, regression-verified. Includes a
verified safety finding (no false positive) plus a message-consistency
fix.

### Safety investigation (no code change resulted from this alone)

Checked whether the existing `button_complete.png` template (an older,
pre-`GAME-CAL-001` asset never previously cross-checked against these
specific real screens) was producing a false positive on a genuinely
incomplete mission. The customer supplied two more real captures: a
target-200 in-progress mission (`51/200`, cost-4400 currency action --
a new target quantity, distinct from the 165/180/450 examples already
on file) and a different mission's reward-preview/close screen. Direct
measurement (`tests/fixtures/game_cal_001/PROVENANCE.md`) shows
`button_complete.png` scores 0.774 on both -- safely below the 0.8
threshold, correctly not matched. Across all 7 real captures now on
file, it matches only screens with a genuinely visible "완료" button.
**Conclusion: no false positive; the completion gate is not tapping
blindly.**

### Actual root cause

The already-documented `select_complete_point` limitation ("always
taps row 1", `SLOT-SELECT-CALIBRATION-001`) manifesting live: kill-
progress eligibility can be confirmed correctly (a real completed
mission genuinely visible somewhere), but if that mission isn't at row
1, the fixed `select_complete_point` tap lands on a *different*,
still-incomplete mission's detail -- which correctly has no
"button_complete" to find. The old bare `"Complete tap failed."`
message gave no way to tell this safe-refusal case apart from a real
problem.

### Fix

`src/ldmanager/bounty_mission.py` -- the Complete/Claim/Close-result
tap-failure details now distinguish, the same way the earlier
Select/Refresh-open/Refresh-confirm fixes did (`STDERR-DETAIL-001`):
`rc=..., stderr=...` when a real fixed-point ADB tap was sent and
failed, vs. an explicit `"no confident button_complete/button_claim_
reward/button_close_reward match on the current screen"` when the
dynamic template search itself found nothing -- for `button_complete`
specifically, the message also names the likely cause
(`select_complete_point` may not be showing the eligible mission).

### Regression tests

`tests/test_bounty_mission.py` --
`test_complete_tap_no_confident_match_gives_an_actionable_reason_not_a_bare_failure`:
reaches the complete-tap step via a genuine kill-progress-counter
eligibility match, with `button_complete` configured but not matching
the frame -- asserts the new, actionable detail text.

### Test results

```
python -m pytest -q
391 passed
```

Run 3x in a row: `391 passed` every time, 0 failures. (Prior baseline
390 + 1 new test = 391.)

### Commits

- `20fc1b8` — `COMPLETE-DETAIL-001: actionable detail for
  complete/claim/close + safety check` (implementation + tests + this
  HANDOFF section, in one commit)
- This hash-record update is the short follow-up commit immediately
  after `20fc1b8`.

### Limitations

1. **The underlying `select_complete_point` "always row 1" gap is
   NOT fixed by this packet** -- only made diagnosable. A live run
   where the eligible mission genuinely isn't at row 1 will still stop
   at this step (safely, correctly refusing to tap) rather than
   completing it. Properly fixing that requires tracking *which*
   locked slot became eligible and selecting that specific position --
   a larger change not made here.
2. No live ADB/LDPlayer/game session was used to verify the message
   fix itself -- verified with fake doubles. The false-positive safety
   check, however, used two real customer-supplied captures.
3. All limitations recorded in every prior section of this document
   remain valid and are not superseded by this packet.

### QA focus points

- Independently verify the exact Code commit hash below.
- Re-run `pytest -q` (expect `391 passed`).
- On a real device: if a live run reaches "Complete tap failed" again,
  confirm the new detail text explains it and that no unintended tap
  occurred (a manual visual check that the on-screen mission state is
  unchanged from before the attempt).
- Independently review whether `select_complete_point`'s "always row 1"
  limitation should now be prioritized as its own follow-up packet --
  this session left it diagnosable but unresolved.

## COMPLETE-SLOT-TRACKING-001: complete the slot that's actually eligible

**Trigger**: user directive to fix the `select_complete_point`
"always row 1" limitation for real (flagged but not fixed in
`SLOT-SELECT-CALIBRATION-001`/`COMPLETE-DETAIL-001`), with an explicit
requirement to keep multi-account (LD1..LD9) isolation correct.

### Status: implemented, tested, regression-verified.

### Root cause (confirmed against real evidence)

A slot's completion state is only visible in **that slot's own opened
detail view** — confirmed from every real capture on file: the
mission-list rows themselves carry no per-row completion indicator.
The previous design ran ONE full-screen completion check against
whatever was currently displayed, then unconditionally re-selected
**row 1's fixed position** to complete — correct only when the
eligible mission happened to be at row 1.

### Fix

`src/ldmanager/bounty_mission.py`'s kill-progress polling now visits
**every still-candidate locked slot individually** on each bounded
poll attempt: a plain select/navigation tap (never complete/claim) to
open that slot's own detail, then the same kill-progress-counter /
complete-badge check as before, scoped to that one slot. The exact
`slot_index` that qualifies is remembered, and the completion step
re-selects **that same slot** (never a different, possibly
still-incomplete one) before tapping complete. `0-199/200` still never
taps complete/claim — only the added navigation (select) taps are new,
and only ever to *look*, consistent with every other safety guarantee
in this project.

`select_complete_point` is no longer consulted by the live completion
path (kept in the config schema for backward compatibility only,
documented as such in both `bounty_config.py` and
`configs/bounty.example.yaml`).

### Regression tests

`tests/test_bounty_mission.py`:
- `test_completion_targets_the_slot_that_actually_became_eligible_not_row_1`
  -- a `_SlotAwareRunner`/`_SlotAwareRecognizer` pair models a real
  screen where only slot 3's own detail shows completion; asserts the
  tap immediately preceding the complete-button tap is slot 3's
  position, never slot 1's.
- `test_kill_progress_polling_never_crosses_accounts_with_multiple_ld_instances`
  -- two independent accounts (own runner/serial/recognizer), each with
  a DIFFERENT eligible slot (2 and 4), run one after another: every
  recorded tap for each stays scoped to that account's own serial, and
  each completes its own correct slot, never the other's -- the
  explicit LD1..LD9 multi-instance safety check this packet was asked
  to include.
- Two pre-existing tests (`test_full_cycle_reaches_completed_state_once`,
  `test_kill_progress_incomplete_never_taps_complete_or_reward`) had
  their exact tap-count assertions updated to reflect the new,
  correctly-larger (but still fully bounded) per-slot polling call
  pattern -- their pass/fail *behavior* is unchanged, only the literal
  count of navigation taps.

### Test results

```
python -m pytest -q
393 passed
```

Run 3x in a row: `393 passed` every time, 0 failures. (Prior baseline
391 + 2 new tests = 393.)

### Commits

- `991d22d` — `COMPLETE-SLOT-TRACKING-001: complete the slot that's
  actually eligible` (implementation + tests + this HANDOFF section,
  in one commit)
- This hash-record update is the short follow-up commit immediately
  after `991d22d`.

### Limitations

1. Per-slot polling means up to `slot_count` extra select/navigation
   taps per poll attempt (bounded by `max_kill_progress_poll_attempts`)
   -- more real ADB traffic than before, though still entirely
   navigation, never complete/claim, and still fully bounded.
2. No live ADB/LDPlayer/game session was used to verify this fix --
   verified with fake/stateful test doubles that model "only one
   specific slot's detail shows completion," not a real device.
3. All limitations recorded in every prior section of this document
   remain valid and are not superseded by this packet.

### QA focus points

- Independently verify the exact Code commit hash below.
- Re-run `pytest -q` (expect `393 passed`).
- On a real device: with 2+ locked slots where the eligible one is NOT
  row 1, confirm the flow now actually reaches and completes the
  correct mission instead of safely stalling at "Complete tap failed."
- With 2+ real LD instances mapped, confirm no cross-account
  interference during a live run.

## RESULT-CLOSE-CALIBRATION-001: real calibration for the result/close screen

**Trigger**: after `COMPLETE-SLOT-TRACKING-001` shipped, the user's
live run progressed further and then stalled repeatedly on the same
post-claim "결과"/"닫기" (Close) popup screen — `result_screen_roi`/
`label`/`close_result_point`/`button_close_reward` had never been
calibrated against any real capture. The user supplied a fresh real
1280x720 Test-capture of the exact stuck screen.

### Status: implemented, tested, regression-verified. Includes a
correction to an earlier documentation mistake (see below).

### Correction to `COMPLETE-DETAIL-001`'s fixtures

While saving real captures for that earlier packet's false-positive
safety check, two files were mistakenly saved under inaccurate names:
`in_progress_51_of_200.png` and `close_result_screen.png` both actually
contained the **same** "닫기" result popup — neither was the real
"모든 몬스터 처치 (51/200)" screen shown alongside them at the time (that
frame was never saved). Both files have been removed; the safety
conclusion they were used for (`button_complete.png` does not false-
positive on the real Close popup, confidence 0.774 < 0.8) remains
correct and unaffected, since the popup content they actually did
contain was still tested. See `tests/fixtures/game_cal_001/
PROVENANCE.md` for the full correction.

### Root cause

Investigated whether the "보상 받기" (claim) and "닫기" (close) buttons
could be reliably distinguished by template matching, the same way
`reward_claim_button.png` was calibrated in `REWARD-SCREEN-
CALIBRATION-001`. Even a tight, text-only crop of each (excluding the
shared ornate border) scored too close for safety — a "닫기" crop
scored 0.80 against the real `reward_screen.png`, right at the 0.8
threshold. **These two buttons cannot be reliably told apart by
template matching alone** (identical gold-button frame, only ~2
characters of text differ).

### Fix

Rather than fight an unreliable text-match, two ALREADY-calibrated,
high-margin real anchors are reused instead:
- `result_screen_label` now reuses `reward_odds_label` ("확률") —
  confirmed present on both the reward and result popups
  (~0.81-1.0 confidence) and confirmed absent from every plain
  detail/list real capture (~0.26-0.30).
- `mission_list_label` now reuses `mission_objective_label` ("임무
  목표") — confirmed present on every plain detail/list real capture
  (~0.998-1.0) and confirmed absent from both popups (~0.07) — a far
  more precise "we actually left the popup" signal than the old,
  never-calibrated placeholder ("현상금 목록") ever had.
- `close_result_point` was measured directly from the real capture
  (same position as `claim_point` — same button frame, different game
  state).

`src/ldmanager/bounty_mission.py` — the close step no longer attempts
any `button_close_reward` template search at all (mirroring
`SLOT-SELECT-CALIBRATION-001`'s reasoning): it always taps
`close_result_point` directly, safe because the preceding
`result_screen_label` check already confirmed a real post-complete
popup is showing. `configs/bounty.example.yaml` no longer maps
`button_close_reward` at all (documented why).

### Regression tests

- `tests/test_result_close_real_assets.py` (new, 6 tests) — real
  capture is a genuine 1280x720 PNG; `result_screen_label` matches only
  the real result/close screen and never any plain detail/list real
  capture; `mission_list_label` matches every plain detail/list real
  capture and never the popup; `button_close_reward` confirmed absent
  from the shipped config.
- `tests/test_bounty_mission.py` —
  `test_close_result_tap_uses_the_exact_configured_close_point_never_a_template`:
  confirms the close tap argv matches `close_result_point` exactly.

### Test results

```
python -m pytest -q
400 passed
```

Run 3x in a row: `400 passed` every time, 0 failures. (Prior baseline
393 + 6 + 1 = 400.)

### Commits

- `9c69ec5` — `RESULT-CLOSE-CALIBRATION-001: real calibration for the
  result/close screen` (implementation + tests + this HANDOFF section,
  in one commit)
- This hash-record update is the short follow-up commit immediately
  after `9c69ec5`.

### Limitations

1. This completes real calibration for every step of the five-slot
   flow's happy path that a real live run has reached so far (select,
   accept, complete, reward, claim, result, close). The
   mission-list-return step immediately after close has not itself
   been separately exercised live yet (it reuses the already-verified
   `mission_objective_label` anchor, but the exact next real screen
   after "닫기" has not been directly observed).
2. No live ADB/LDPlayer/game session was used to verify this fix —
   verified against the one real supplied capture, offline.
3. All limitations recorded in every prior section of this document
   remain valid and are not superseded by this packet.

### QA focus points

- Independently verify the exact Code commit hash below.
- Re-run `pytest -q` (expect `400 passed`) and
  `tests/test_result_close_real_assets.py` specifically.
- On a real device: confirm a live run now proceeds past the result/
  close step (tapping the real "닫기" button at the measured position)
  and reaches mission-list verification -- the likely next real
  blocker, if any.

## EARLY-COMPLETE-CHECK-001: don't re-walk slots already known complete

**Trigger**: user question after `RESULT-CLOSE-CALIBRATION-001` shipped:
after closing the result popup once, `runtime.reset_after_verified_
return()` unlocks all 5 slots for the next round, and every slot gets
re-visited to re-confirm its target phrase. If one of those freshly
re-accepted slots was ALREADY complete, the code still ignored that and
ran a whole separate kill-progress polling pass afterward, re-selecting
every locked slot again from scratch just to rediscover what the
accept loop's own already-open view had just shown. Reported as a real
observed inefficiency, not a crash or a stuck point.

### Status: implemented, tested, regression-verified.

### Root cause

`_accept_or_refresh_slot` only ever checks the target phrase/quantity,
never completion — by design, since checking completion is irrelevant
for slots that visibly aren't done yet. But the main accept loop threw
away the view it had just opened for each slot as soon as the phrase
check passed, then handed off to a completely separate "kill-progress:
bounded polling" loop that re-opened (re-tapped) every locked slot all
over again, from slot 1, to find which one (if any) was complete. When
the eligible slot happened to be one accepted early in the round, this
meant a full second sweep across every slot just to re-observe
something already visible one tap earlier.

### Fix

`src/ldmanager/bounty_mission.py`'s `run_one_cycle`: immediately after
a slot is accepted and locked in the main loop, and only while no
eligible slot has been found yet, the SAME already-open view is
re-used (no extra tap) to check `kill_progress_roi`/label and the
completion badge (`button_complete` template if mapped, else
`complete_state_roi`/label) — exactly the same checks the kill-progress
phase would have made. If it matches, `eligible_slot_index` is recorded
right there. The downstream kill-progress polling loop now starts from
`eligible = eligible_slot_index is not None` and breaks immediately if
already eligible, so when a slot's completion was caught during the
accept pass, the entire redundant re-select-and-check sweep across
every locked slot is skipped outright — the flow goes straight to
re-selecting that one known slot for the complete tap.

### Regression tests

- `tests/test_bounty_mission.py` —
  `test_early_complete_check_skips_the_redundant_kill_progress_reselect_pass`
  (new): with slot 1 the eligible one, confirms its detail view is
  opened only twice before the complete tap — once to accept it, once
  to re-select it right before completing — never a third, redundant
  time for a kill-progress-phase re-check.
- `test_full_cycle_reaches_completed_state_once`: tap-count assertion
  updated from `5+1+4+5` (`COMPLETE-SLOT-TRACKING-001`-era, one extra
  kill-progress-phase select for slot 1) down to `5+4+5=14`, since that
  extra select no longer happens.
- All prior COMPLETE-SLOT-TRACKING-001/kill-progress regression tests
  (targeting-the-right-slot, multi-LD-instance isolation, bounded
  polling on incomplete slots) still pass unchanged — this packet only
  removes REDUNDANT work, never changes which slot ends up targeted.

### Test results

```
python -m pytest -q
401 passed
```

Run 3x in a row: `401 passed` every time, 0 failures. (Prior baseline
400 + 1 new test = 401.)

### Commits

- `6035d34` — `EARLY-COMPLETE-CHECK-001: don't re-walk
  slots already known complete` (implementation + tests + this
  HANDOFF section, in one commit)
- Followed by a short "docs: record EARLY-COMPLETE-CHECK-001 commit
  hash in handoff" commit recording the real hash.

### Limitations

1. This is a pure efficiency fix (fewer redundant taps/checks per
   round) — it does not change which slot is targeted for completion,
   does not touch any template/coordinate calibration, and does not
   address any new failure mode.
2. No live ADB/LDPlayer/game session was used to verify this fix —
   verified against the existing fake-runner/recognizer test harness
   only, same as prior packets' unit-level verification.
3. All limitations recorded in every prior section of this document
   remain valid and are not superseded by this packet.

### QA focus points

- Independently verify the exact Code commit hash below.
- Re-run `pytest -q` (expect `401 passed`).
- On a real device with multiple slots already complete at round
  start: confirm the flow reaches "완료" faster (visibly fewer
  select-and-wait steps) than before, without skipping or misfiring on
  any slot.

## REFRESH-CALIBRATION-001: real calibration for the refresh/reroll flow

**Trigger**: after `EARLY-COMPLETE-CHECK-001` shipped, the user
reported a live run stuck on a different mission on a different slot:
"십변도 토벌작전[던전]" / 귀마황 처치 (0/250), a dungeon-type,
never-target mission, with `Slot 3: refresh-open tap failed`.
`refresh_button_point`/`refresh_popup_anchor_roi`/
`refresh_popup_title_roi`/`refresh_confirm_point` had never been
calibrated against any real capture. The user supplied three real
1280x720 captures: two of the region-quest list view (different
slots/missions selected) and one of the actual renewal-confirmation
popup.

### Status: implemented, tested, regression-verified.

### Root cause

Same bug class as `TAP-FALLBACK-CRASH-001`/`SLOT-SELECT-CALIBRATION-
001`, a third time: `button_refresh_4400/6600/9900/14900`/
`button_refresh_confirm` (mapped in `template_map`) are
pre-`GAME-CAL-001` placeholder assets (380x116/180x55 -- the wrong
proportions for a real 1280x720 capture, never real crops). A real
live run proved they never confidently match, and because
`template_map` being non-empty overall makes `_tap_any_template()`/
`_tap_template()` return a hard `False` (not `None`) for an
unconfident match, this silently blocked the fixed-point fallback from
ever running.

### Fix

Real evidence resolved this cleanly:
- `refresh_button_point` is the real, measured center of the
  currency-cost action box -- which turned out to be the EXACT same
  real UI element already calibrated in `GAME-CAL-001` as
  `currency_action_4400.png` (cross-validated via direct template
  match: 0.993 confidence, at the same pixel offset this packet's
  independent hand-measurement found). Confirmed present at the
  identical pixel position across three independent real captures
  (`cv2.absdiff` mean 0.0 between the two new list-view captures at
  that region), so it is positionally fixed regardless of which
  slot/mission is currently selected or its currently displayed price.
- Two real crops from the actual renewal-confirmation popup
  (`region_quest_renew_confirm.png`) now structurally verify the
  popup before ever tapping confirm: `refresh_popup_title_label`
  ("지역 퀘스트를 갱신 하시겠습니까?") and `refresh_popup_anchor_label`
  ("갱신 금액") -- both confirmed to match only this real popup and
  none of the other 9 real captures on file.
- `refresh_confirm_point` was measured directly as the popup's real
  "확인" button center.

`src/ldmanager/bounty_mission.py` -- refresh-open and refresh-confirm
no longer attempt any template search at all (mirroring
`SLOT-SELECT-CALIBRATION-001`/`RESULT-CLOSE-CALIBRATION-001`'s
reasoning): refresh-open always taps `refresh_button_point` directly,
and refresh-confirm always taps `refresh_confirm_point` directly, safe
because the structural popup-verification check runs in between and
refuses to confirm blindly if the real popup isn't actually showing
(`REFRESH_POPUP_NOT_VERIFIED`, never a wrong tap). The now-dead
`_tap_any_template()` helper (no remaining call sites) was deleted.
`configs/bounty.example.yaml` no longer maps
`button_refresh_confirm`/`button_refresh_4400/6600/9900/14900` at all,
and no longer carries two stray, never-referenced literal-Korean-text
template_map entries ("지역 퀘스트 갱신"/"확인" -> a different stale
asset) left over from an earlier, unrelated attempt.

### Regression tests

- `tests/test_refresh_popup_real_assets.py` (new, 7 tests) -- real
  captures are genuine 1280x720 PNGs; `refresh_popup_title_label`/
  `refresh_popup_anchor_label` match only the real renewal-confirm
  popup and never any of the 9 other real captures; `refresh_button_
  point` lands inside the real `currency_action_4400` template's
  bounding box on both real list-view captures (0.98+ confidence);
  the 5 stale refresh-button templates confirmed absent from the
  shipped config.
- `tests/test_bounty_config.py` --
  `test_example_bounty_config_refresh_fields_are_real_calibrated_values`,
  `test_example_bounty_config_never_maps_the_stale_refresh_button_templates`.
- `tests/test_bounty_mission.py` -- replaced the two now-obsolete
  "dynamic template no-match" tests (their premise no longer exists)
  with `test_refresh_open_is_always_position_based_never_template_
  matched`, `test_refresh_open_tap_failure_detail_includes_the_real_
  adb_stderr`, and `test_refresh_confirm_is_always_position_based_
  never_template_matched`; updated
  `test_slot_select_is_always_position_based_never_template_matched`'s
  assertion (it now reaches -- and correctly fails at -- the popup's
  own structural verification, not a since-removed "refresh-open"
  template check).

### Test results

```
python -m pytest -q
411 passed
```

Run 3x in a row: `411 passed` every time, 0 failures. (Prior baseline
401 + 6 new bounty_mission + 2 new bounty_config + ... see file diff;
net +10 across the two obsolete tests replaced by three, plus 7 new
real-asset tests and 2 new config-guard tests.)

### Commits

- `PLACEHOLDER_COMMIT_HASH` -- `REFRESH-CALIBRATION-001: real
  calibration for the refresh/reroll flow` (implementation + tests +
  this HANDOFF section, in one commit)
- Followed by a short "docs: record REFRESH-CALIBRATION-001 commit
  hash in handoff" commit recording the real hash.

### Limitations

1. The exact game action that opens the renewal-confirm popup is
   inferred from real evidence (the currency-action box is positionally
   fixed and present on every real capture checked), not directly
   observed as one continuous tap-then-popup interaction -- the
   captures were supplied as separate reference screenshots, not a
   recorded sequence. If `refresh_button_point` turns out not to open
   this exact popup on some other real screen state, the structural
   popup-verification check immediately downstream fails closed
   (`REFRESH_POPUP_NOT_VERIFIED`, never a wrong tap) rather than
   silently misbehaving.
2. No live ADB/LDPlayer/game session was used to verify this fix --
   verified against the real supplied captures, offline.
3. All limitations recorded in every prior section of this document
   remain valid and are not superseded by this packet.

### QA focus points

- Independently verify the exact Code commit hash below.
- Re-run `pytest -q` (expect `411 passed`) and
  `tests/test_refresh_popup_real_assets.py` specifically.
- On a real device: confirm a live run now proceeds past a non-target
  slot's refresh/reroll step (tapping the real currency-action box,
  then the real renewal-confirm popup's "확인") instead of failing at
  "refresh-open tap failed" -- the likely next real blocker, if any, is
  whether the tapped currency-action box actually opens this exact
  popup on every mission type (dungeon-type included), per Limitation 1
  above.
