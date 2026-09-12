# LDplayer

`ldmanager` — LDPlayer 다중 계정(LD1~LD9) 관리 도구.

> **현재 단계: TP-001 stage 1 — 프로젝트 골격만 구현됨.**
> 실제 LDPlayer/게임 조작, 자격증명 처리, 웹 DOM 제어, 전역 마우스 제어는
> 이 단계에 포함되지 않습니다. 이후 단계에서 확장됩니다.

## 요구 사항

- Python 3.10 이상

## 설치

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -e ".[dev]"
```

## 설정

1. `configs/config.example.yaml`을 `configs/config.yaml`로 복사합니다.
   (`configs/config.yaml`은 `.gitignore`에 포함되어 커밋되지 않습니다.)
2. `adb_mapping`의 `LD1`~`LD9` 값을 본인 환경의 실제 ADB `host:port`로
   채웁니다. 기본값은 모두 `null`이며, 이 프로젝트는 포트를 추측하거나
   하드코딩하지 않습니다 — 반드시 직접 지정해야 합니다.
3. 설정 파일 경로는 `LDMANAGER_CONFIG` 환경변수로 재정의할 수 있습니다.

## 테스트 실행

```bash
pytest
```

## 골격 CLI 실행 (참고용)

```bash
python -m ldmanager.cli
```

설정 파일이 없으면 에러 메시지만 안내하고, 기본 계정 레지스트리
(LD1~LD9, 상태는 모두 `UNKNOWN`)를 출력합니다. 실제 자동화 동작은
수행하지 않습니다.

## 프로젝트 구조

```
src/ldmanager/
  __init__.py
  models.py   # AccountId, AccountState enum, Account/registry 골격
  config.py   # 설정 경로 탐색 및 로딩 골격 (ADB 매핑 placeholder)
  cli.py      # 최소 CLI 진입점 (실제 자동화 없음)
configs/
  config.example.yaml  # adb_mapping 자리표시자 템플릿
tests/
  test_models.py
  test_config.py
docs/
  HANDOFF_CODE.md  # 단계별 구현/테스트 인수인계 기록
```
