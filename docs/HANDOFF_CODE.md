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
