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
