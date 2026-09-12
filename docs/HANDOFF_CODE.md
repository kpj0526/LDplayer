# HANDOFF — Code worktree

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
