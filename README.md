# LDplayer

`ldmanager` — LDPlayer 다중 계정(LD1~LD9) 관리 도구.

> **현재 단계: TP-003 — 계정별 ADB 스크린샷 캡처 + 가드된 상대 좌표
> 터치 기반(foundation).**
> 이것은 게임 자동화가 아닙니다. OCR/템플릿 매칭/미션 로직/GUI/로그인·
> 재연결/전역 마우스/웹 DOM/자격증명 저장은 이 프로젝트 어디에도
> 구현되어 있지 않습니다. 실제 LDPlayer/실제 ADB 장치를 이용한 통합
> 검증도 수행되지 않았습니다(페이크 러너 기반 자동 테스트만 실행함).

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
4. `logging`(로그 디렉터리/회전/보존) / `diagnostics`(진단 스크린샷 경로
   루트) 섹션은 생략하면 안전한 기본값이 적용됩니다.
5. **비밀번호·토큰·API 키 등 자격증명으로 보이는 키가 하나라도 있으면
   설정 로드가 거부됩니다.** 이 프로젝트는 `config.yaml`에 어떤 형태로도
   자격증명을 저장하지 않습니다.
6. `adb_mapping`은 항상 사용자가 직접 채우는 값입니다. `adb devices`
   디스커버리는 현재 보이는 장치를 보고할 뿐, 계정에 자동으로 배정하지
   않습니다. LD1~LD9 discovery/연결 상태 확인 플로우를 실제로 쓰려면
   아홉 항목 전부를 서로 다른 시리얼로 채워야 하며(`ldmanager.discovery.
   ensure_complete_adb_mapping()`), 누락/중복/9개가 아닌 구성은 ADB를
   호출하기 전에 거부됩니다.

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
  models.py       # AccountId, AccountState enum, Account/registry 골격
  config.py       # 설정 경로 탐색/로딩/검증, 민감정보 필드 거부
  logs.py         # 계정별(LD1~LD9) task/error 로그 분리, 회전/보존 정책,
                  # 자격증명 레드액션(msg/args + exc_info/트레이스백)
  diagnostics.py  # 진단 스크린샷 경로/메타데이터 생성 (실제 캡처 없음)
  paths.py        # 안전한 파일명/경로 검증 유틸리티
  redaction.py    # 자격증명형 텍스트 레드액션(로그 전용)
  adb.py          # 주입 가능한 ADB 러너(텍스트 + 바이너리 캡처), `adb
                  # devices` 파싱, 단일 시리얼 범위 명령 구성
  discovery.py    # LD1~LD9 매핑 검증 + 러너 기반 연결 상태 조회
  coordinates.py  # 기기-내부 상대 좌표([0,1]) 검증 + 픽셀 변환(전역
                  # 마우스/고정 외부 좌표 없음)
  screenshot.py   # 계정별 스크린샷 바이너리 캡처 + PNG 바이트 검증
  guarded_touch.py  # 캡처→사전조건→단일 터치→캡처→사후조건 가드 상태
                    # 머신 (게임 자동화 아님, OCR/템플릿/미션 없음)
  cli.py          # 최소 CLI 진입점 (실제 자동화 없음)
configs/
  config.example.yaml  # adb_mapping / logging / diagnostics 템플릿
tests/
  test_models.py
  test_config.py
  test_logs.py
  test_diagnostics.py
  test_paths.py
  test_redaction.py
  test_gitignore.py
  test_adb.py
  test_discovery.py
  test_coordinates.py
  test_screenshot.py
  test_guarded_touch.py
  fakes.py        # FakeAdbRunner/BrokenAdbRunner/ExceptionRaisingCaptureRunner
docs/
  HANDOFF_CODE.md  # 단계별 구현/테스트 인수인계 기록
```

## 로그 / 진단 스크린샷 (stage 2)

- 로그는 `<logging.root_dir>/<LDx>/task.log`(INFO/WARNING)와
  `<logging.root_dir>/<LDx>/error.log`(ERROR 이상)로 계정별·종류별 분리
  저장되며, 크기 기준 회전(`max_bytes`, `backup_count`)과 별도로
  `purge_expired_logs()`가 `retention_days`보다 오래된 회전 로그 파일을
  정리합니다(자동 실행되지 않음 — 호출 시점은 이후 단계/운영 스크립트가
  결정).
- 진단 스크린샷은 이 단계에서 **경로와 JSON 메타데이터만** 생성합니다
  (`diagnostics.build_screenshot_request()` /
  `diagnostics.write_metadata_sidecar()`). 실제 ADB 캡처(PNG 바이트 생성)는
  구현되어 있지 않습니다.

## LD1~LD9 discovery + ADB 매핑 (stage 3)

- `ldmanager.adb.AdbRunner`는 딱 두 메서드(`list_devices()`,
  `run(serial, args)`)만 있는 최소 인터페이스입니다. `run()`은 항상 명시적인
  `serial`을 요구하며(`build_adb_command()`가 `["adb", "-s", <serial>, ...]`
  형태로만 명령을 구성), 실제 구현체 `SubprocessAdbRunner`가 유일하게
  프로세스를 실행합니다. touch/tap/screenshot/게임 조작/로그인/재연결
  명령은 이 프로젝트 어디에도 없습니다.
- `ldmanager.discovery.validate_complete_adb_mapping()` /
  `ensure_complete_adb_mapping()`은 `adb_mapping`이 정확히 LD1~LD9,
  전부 서로 다른 시리얼로 채워져 있는지만 검사합니다(ADB 호출 없음).
  누락/중복/9개가 아닌 구성은 즉시 거부됩니다.
- `ldmanager.discovery.build_account_connection_statuses()`는 (검증된
  매핑이든 아니든) 계정별로 정확히 하나의 상태를 반환합니다:
  `ok` / `unmapped` / `device_not_found` / `device_offline` /
  `device_unauthorized` / `device_state_unknown` / `discovery_unavailable`.
  디스커버리가 확인한 장치를 매핑되지 않은 계정에 **자동 배정하지
  않습니다** — 사용자가 채운 매핑만 신뢰합니다.
- 실제 LDPlayer/실제 ADB 장치를 이용한 통합 검증은 이번 단계에도
  수행되지 않았습니다(페이크 러너 기반 자동 테스트만 실행함). "실제
  LDPlayer 연동이 된다"는 주장은 하지 않습니다.

## 스크린샷 캡처 + 가드된 터치 기반 (TP-003)

- `ldmanager.adb.AdbRunner`에 `capture_binary(serial, args)`가
  추가되었습니다(바이너리 전용, 텍스트 디코딩 없음). `run()`과 마찬가지로
  항상 명시적·비공백 시리얼 하나로만 범위가 고정됩니다.
- `ldmanager.screenshot.capture_screenshot()`은 캡처된 바이트가 PNG
  매직 헤더로 시작하는지 검사합니다. 러너 실패/빈 출력/손상된 바이트/
  러너 예외는 모두 예외를 던지지 않고 `ScreenshotCaptureResult(ok=False,
  error=...)`로 반환됩니다.
- `ldmanager.coordinates.RelativeCoordinate`는 `[0.0, 1.0]` 범위의
  기기-내부 상대 좌표만 허용합니다(생성 시점에 즉시 검증 — 잘못된 좌표는
  객체조차 만들어지지 않음). `ScreenSize` + `build_tap_args()`가 이를
  `shell input tap <x> <y>` 인자로 변환합니다. **전역 데스크톱 마우스나
  고정된 외부 좌표 개념은 어디에도 없습니다.**
- `ldmanager.guarded_touch.perform_guarded_touch()`가 가드 계약을
  구현합니다:
  `캡처 → 사전조건 훅 → (수락 시에만) 시리얼 하나에 정확히 한 번 터치
  → 캡처 → 사후조건 훅`.
  사전조건이 거짓/예외이거나, 캡처가 끝내 실패/손상 상태면 **터치는 전혀
  전송되지 않습니다.** 터치 이후 사후조건이 거짓/예외/캡처실패로
  끝나도 **터치를 반복 전송하지 않습니다** — 캡처/검증 재시도만
  `max_capture_attempts`/`max_postcondition_attempts`로 상한이 걸린 채
  반복되고, 결과는 항상 계정 로컬의 구조화된 `GuardedTouchResult`로
  반환됩니다(예외 전파 없음).
- 이 계층 어디에도 OCR, 이미지 템플릿 매칭, 미션/게임 로직, GUI, 로그인/
  재연결, 전역 마우스 제어는 구현되어 있지 않습니다 — "정확히 지정된
  시리얼에 정확히 하나의 좌표로 하나의 탭을 보낼지 말지 결정하는" 골격
  까지만입니다.
- 이번 단계도 전부 페이크 러너로만 검증되었습니다 — 실제 `adb`/실제
  LDPlayer 화면으로 시험된 바 없습니다.
