# LDplayer

## 고객 최초 실행

고객은 코드나 템플릿 좌표를 수정하지 않습니다. `ldmanager.exe` 실행 후
LDPlayer를 켜고 각 계정에 ADB serial을 저장한 뒤 **Test capture**를 한 번
누릅니다. 프로그램이 내장 템플릿과 자동 비교해 현재 게임 화면을 확인하면
그 계정의 Start가 활성화됩니다. 일치하지 않으면 저장된 캡처 파일만 지원팀에
전달하면 되며, 고객은 Template calibration을 사용할 필요가 없습니다.

### 화면 확인 실패 시

Start를 누르지 말고 GUI가 표시한 Test capture PNG만 전달합니다. 개발자는
그 PNG로 템플릿을 보완하고 새 배포본을 만듭니다. 고객은 ROI·좌표·임계값을
수정하지 않습니다. 실제 고객 PC에서는 ADB serial 연결, 화면 확인 성공,
LD1 단일 흐름, 이후 LD1~LD9 동시 실행을 순서대로 확인합니다.

`ldmanager` — LDPlayer 다중 계정(LD1~LD9) 관리 도구.

> **현재 단계: MVP-001-CV — 실행 가능한 MVP + 무료 지역 현상금
> 5-슬롯 흐름 확장.**
> GUI로 LD1~LD9 계정을 개별/전체 시작·정지할 수 있고, 각 계정이 실제
> 무료 지역 현상금 흐름(슬롯 선택/확인 → 필요 시 새로고침 → **비용
> 숫자가 아니라 구조적으로** 새로고침 확인 팝업 식별 → 신규 미션
> 검사 → '모든 몬스터 처치' **그리고** 수량 200이 **둘 다** 인식될
> 때만 수락 → 5슬롯 완료 후 킬 진행도 관찰 → 200/200 또는 명시적 완료
> 상태에서만 완료/보상 → 결과 확인 → 닫기 → 목록 복귀 → 재새로고침 →
> 신규 타겟 수락 → 반복)를 사이클로 반복합니다. 인식(OCR/템플릿)은
> **실제로 구현되어 있지 않은 안전한 자리표시자**이며 항상 "인식 안
> 됨"을 반환합니다 — 게임 자동화가 아니라 안전한 실행 가능 골격입니다.
> 실제 LDPlayer/실제 ADB로는 검증되지 않았습니다(전부 페이크/주입
> 러너 기반 자동 테스트로만 검증). 빠른 실행법은
> [`docs/RUN_GUIDE.md`](docs/RUN_GUIDE.md), 실제 게임에 연결하기 전에
> 해야 할 일은 [`docs/REAL_CAPTURE_CHECKLIST.md`](docs/REAL_CAPTURE_CHECKLIST.md),
> 미구현/미검증 전체 목록은 [`docs/MVP_UNVERIFIED.md`](docs/MVP_UNVERIFIED.md)
> 참고.

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

## 빠른 실행 (MVP-001-CV)

```bash
# configs/config.yaml, configs/bounty.yaml 준비 후
python -m ldmanager.app
# 또는 Windows에서: scripts\run.bat  /  scripts\run.ps1
```

(`configs/mission.yaml`은 초기 버전 `mission.py`용이며 실제 앱은 더
이상 읽지 않습니다 — `configs/bounty.yaml`이 실제로 필요한 파일입니다.)

자세한 단계별 안내는 [`docs/RUN_GUIDE.md`](docs/RUN_GUIDE.md) 참고.
Windows 실행 파일 빌드는 `scripts\build_windows.ps1`(PyInstaller).

## 테스트 실행

```bash
pytest
```

## 골격 CLI 실행 (참고용, stage 1부터 존재 — MVP 컨트롤러와 무관)

```bash
python -m ldmanager.cli
```

설정 파일이 없으면 에러 메시지만 안내하고, 기본 계정 레지스트리
(LD1~LD9, 상태는 모두 `UNKNOWN`)를 출력합니다. 실제 자동화 동작은
수행하지 않습니다. MVP GUI/컨트롤러를 실행하려면 위 "빠른 실행" 절의
`python -m ldmanager.app`을 사용하세요.

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
  discovery.py    # LD1~LD9 매핑 검증 + 러너 기반/순수 연결 상태 조회
                  # (compute_account_connection_statuses: 이미 가져온
                  # device 목록으로 재계산, ADB 재호출 없음 — GUI가 사용)
  config_mapping.py  # GUI에서 계정별 ADB 시리얼 저장/삭제(UI-ADB-001) —
                      # 순수 config 파일 I/O + 검증, ADB 호출 전혀 없음
  coordinates.py  # 기기-내부 상대 좌표([0,1]) 검증 + 픽셀 변환(전역
                  # 마우스/고정 외부 좌표 없음)
  screenshot.py   # 계정별 스크린샷 바이너리 캡처 + PNG 바이트 검증
  guarded_touch.py  # 캡처→사전조건→단일 터치→캡처→사후조건 가드 상태
                    # 머신 (게임 자동화 아님, OCR/템플릿/미션 없음)
  recognition.py  # Recognizer 인터페이스 + PlaceholderRecognizer(항상
                  # unknown — 실제 OCR/템플릿 매칭 미구현)
  mission_config.py  # (superseded by bounty_config.py in the real app,
                      # kept/tested) 초기 5-슬롯 ROI/좌표/threshold 설정
  mission.py      # (superseded by bounty_mission.py in the real app,
                  # kept/tested) 초기 5-슬롯→200킬→보상→리셋 상태 머신
  bounty_config.py  # 무료 지역 현상금 흐름 ROI/좌표/label/threshold/
                    # 재시도/타임아웃 설정 로딩(bounty.yaml)
  bounty_mission.py  # 실제 무료 지역 현상금 5-슬롯 상태 머신: 슬롯 선택/
                      # 확인→(구조적 팝업 검증 후)새로고침→둘 다 일치해야
                      # 수락→킬 진행도 관찰(0-199/200은 완료/보상 절대
                      # 없음)→완료→보상→결과→닫기→목록 복귀→재수락
  controller.py   # 계정별 독립 취소 가능 워커 + 컨트롤러(개별/전체
                  # 시작·정지, 예외 격리)
  gui.py          # Tkinter 기반 LD1~LD9 상태/버튼 GUI + ADB 매핑 등록
                  # (Refresh ADB devices, 계정별 시리얼 선택/입력+저장/삭제)
  app.py          # 실행 진입점(config+bounty_config+controller+GUI 연결)
  cli.py          # 최소 CLI 진입점 (stage 1, MVP 컨트롤러와 별개)
configs/
  config.example.yaml   # adb_mapping / logging / diagnostics 템플릿
  mission.example.yaml  # (초기 버전용, 현재 앱에서는 미사용) 템플릿
  bounty.example.yaml   # 무료 지역 현상금 ROI/좌표/label/threshold/
                        # 재시도/타임아웃 템플릿 — 실제 앱이 사용하는 것
templates/
  README.md       # 자리표시자 안내(실제 템플릿 자산 없음)
scripts/
  run.bat / run.ps1        # 시작 스크립트
  build_windows.ps1        # PyInstaller Windows 빌드 스크립트
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
  test_recognition.py
  test_mission_config.py
  test_mission.py
  test_bounty_config.py
  test_bounty_mission.py
  test_config_mapping.py
  test_controller.py
  test_gui.py
  test_app.py
  fakes.py        # FakeAdbRunner/BrokenAdbRunner/ExceptionRaisingCaptureRunner/
                  # LabelMappingRecognizer
docs/
  HANDOFF_CODE.md          # 단계별 구현/테스트 인수인계 기록
  RUN_GUIDE.md             # 간단 실행 가이드
  REAL_CAPTURE_CHECKLIST.md  # 실제 게임 연결 전 체크리스트
  MVP_UNVERIFIED.md        # 미구현/미검증 목록
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

## 실행 가능한 MVP (MVP-001)

- **컨트롤러/워커** (`controller.py`): 계정(LD1~LD9)마다 독립적인
  취소 가능 백그라운드 스레드(`AccountWorker`)를 하나씩 가집니다.
  개별 시작/정지(`start_account`/`stop_account`)와 전체 시작/정지
  (`start_all`/`stop_all`)를 지원하며, 한 계정을 정지해도 다른 계정에는
  전혀 영향이 없습니다. 워커 내부에서 예외가 발생해도 그 계정의
  `last_error`로만 남고 다른 워커나 컨트롤러 전체에는 전파되지
  않습니다.
- **미션 사이클** (`bounty_mission.py`, MVP-001-CV부터 실제 앱이 사용):
  아래 "무료 지역 현상금 5-슬롯 흐름" 절 참고. 초기 버전(`mission.py`,
  5개 슬롯→200킬 체크→보상→리셋)은 그대로 유지/테스트되지만 실제
  `app.py`에서는 더 이상 사용되지 않습니다.
- **인식** (`recognition.py`): `Recognizer` 인터페이스 + 기본 구현
  `PlaceholderRecognizer` — **실제 OCR/템플릿 매칭이 구현되어 있지
  않으며, 항상 `UNKNOWN`/신뢰도 0을 반환**합니다. 성공을 하드코딩하지
  않습니다. 실제 인식기로 교체하는 방법은
  `docs/REAL_CAPTURE_CHECKLIST.md` 4절 참고.
- **설정** (`bounty_config.py`, `configs/bounty.example.yaml`): 경로
  (`templates_dir`)/ROI/좌표/label/threshold/재시도 횟수/타임아웃이 전부
  YAML 설정값입니다 — 코드에 하드코딩된 값 없음.
- **GUI** (`gui.py`): Tkinter(표준 라이브러리, 별도 의존성 없음) 기반.
  LD1~LD9 9개 패널 + 전체 Start All/Stop All/**Refresh ADB devices**.
  각 패널은 상태(running/stopped)/현재 슬롯/사이클 수·마지막 결과/
  마지막 오류/최근 로그 한 줄과 Start/Stop 버튼, 그리고(UI-ADB-001)
  ADB 시리얼 선택/입력 콤보박스 + Save/Clear + 실시간 매핑 상태를
  보여줍니다. 자세한 내용은 아래 "GUI에서 LD1~LD9 등록" 절 참고.
- **실행 진입점** (`app.py`, `scripts/run.bat`, `scripts/run.ps1`):
  `python -m ldmanager.app`. 설정 파일이 없거나 잘못되면 GUI를 열지
  않고 콘솔에 에러만 출력한 뒤 종료 코드 1로 끝납니다.
- **Windows 실행 파일 빌드** (`scripts/build_windows.ps1`): PyInstaller로
  `dist\ldmanager\ldmanager.exe`를 생성합니다. 이 세션에서 실제로
  빌드/검증했는지는 `docs/HANDOFF_CODE.md`의 MVP-001 절을 참고하세요.

**이것은 게임 자동화가 아닙니다.** 실제 인식이 구현되어 있지 않으므로
실제 화면에 대해 실행하면 매 슬롯에서 상한까지 리롤을 시도하다가
안전하게 멈춥니다 — 이는 버그가 아니라 설계된 안전 기본값입니다.
전체 미구현/미검증 목록은
[`docs/MVP_UNVERIFIED.md`](docs/MVP_UNVERIFIED.md)를 참고하세요.

## 무료 지역 현상금 5-슬롯 흐름 (MVP-001-CV)

실제 앱(`app.py`)이 사용하는 미션 사이클입니다(`bounty_mission.py` +
`bounty_config.py` + `configs/bounty.example.yaml`). 고객 영상으로
확인된 실제 흐름을 구조적으로 모델링한 것이며, 여전히 인식은
`PlaceholderRecognizer`(항상 미인식)입니다 — 게임 자동화가 아닙니다.

1. **슬롯 선택/확인 (1~5)**: 각 슬롯을 탭해 선택하고 현재 미션이 이미
   수락 조건을 만족하는지 확인합니다.
2. **필요 시 새로고침**: 조건을 만족하지 않으면 새로고침 버튼을 탭해
   확인 팝업을 엽니다.
3. **팝업을 구조적으로 식별**: 팝업이 실제로 열렸는지는 **표시되는
   비용 숫자가 아니라** 두 개의 독립적인 구조적 랜드마크
   (`refresh_popup_anchor_*`, `refresh_popup_title_*`)로만 판단합니다
   — 비용은 매번 바뀌므로 절대 판단 기준으로 쓰지 않습니다. 두 랜드
   마크가 모두 확인되어야만 확인 버튼을 탭합니다(상한 있는 재시도).
4. **신규 미션 검사 + 수락 판정**: 새로고침 후 나타난 미션에 대해
   **'모든 몬스터 처치' 문구와 수량 '200' 둘 다**가 인식되어야만
   수락합니다 — 어느 한쪽만 인식되어도 수락하지 않고(하나의 OCR
   결과만으로 판단 금지) 리롤을 반복합니다(상한 있음).
5. **다음 슬롯**: 검증된 수락 이후에만 다음 슬롯으로 넘어갑니다.
6. **킬 진행도 관찰**: 5슬롯을 모두 처리한 뒤 200킬 진행도를
   상한 있는 폴링으로 관찰합니다. **0~199/200 구간에서는 완료/보상
   버튼을 절대 탭하지 않습니다.** `200/200` 카운터 **또는** 명시적
   완료 배지, 둘 중 하나라도 확인되어야만 다음 단계로 진행합니다.
7. **완료→보상→수령→결과→닫기→목록 복귀**: 미션을 선택하고 완료
   버튼을 탭한 뒤, 보상 화면을 검증하고서야 수령을 탭하고, 결과
   화면을 검증하고서야 닫으며, 미션 목록 복귀를 검증합니다. 각 단계
   모두 상한 있는 검증을 거칩니다.
8. **재새로고침 + 신규 타겟 수락 + 반복**: 완료된 슬롯들을 다시
   새로고침해 새 타겟을 수락한 뒤(1~5단계 로직 재사용), 호출자
   (워커)가 이 전체 사이클을 반복 호출합니다.

모든 동작은 여전히 "캡처 → 기대 상태/조건 확인 → 명시적 시리얼 하나에
가드된 상대 좌표 터치 한 번 → 관찰"만 반복하며, `should_stop()`은
모든 캡처/터치 직전에 확인됩니다. 초기 단순 버전(`mission.py`)은
호환성을 위해 그대로 유지/테스트되지만 실제 앱에서는 더 이상
사용되지 않습니다. 자세한 AC 매핑/한계/실제 연동에 필요한 작업은
`docs/HANDOFF_CODE.md`의 MVP-001-CV 절과
`docs/REAL_CAPTURE_CHECKLIST.md`를 참고하세요.

## GUI에서 LD1~LD9 등록 (UI-ADB-001)

고객이 YAML을 직접 편집하거나 터미널을 쓸 필요 없이, GUI에서 계정별
ADB 매핑을 등록/해제할 수 있습니다.

- **전역 "Refresh ADB devices" 버튼**: `adb devices`를 읽기만 합니다
  (탭 없음, 워커 시작 없음). 결과로 모든 패널의 시리얼 콤보박스 후보
  목록과 각 계정의 실시간 연결 상태를 갱신합니다.
- **계정별 패널**: 콤보박스에서 발견된 시리얼을 **선택**하거나 직접
  **입력**할 수 있습니다 — 발견된 장치를 자동으로 배정하는 일은
  없습니다. **Save**를 누르면 `ldmanager.discovery`의 기존 명시적
  매핑 검증 로직을 재사용해 검증한 뒤(빈 값/공백만 있는 값/공백이
  섞인 형식/다른 계정과 중복되는 값은 저장 없이 그 패널에 에러로
  표시) 로컬(ignored) `configs/config.yaml`에만 저장하고 패널 상태를
  다시 불러옵니다. **Clear**는 그 계정의 매핑만 제거하며 다른 계정의
  매핑에는 전혀 영향을 주지 않습니다.
- **Save/Clear는 ADB 탭을 절대 보내지 않고 워커도 시작하지 않습니다**
  — 순수 설정 파일 I/O입니다(`ldmanager.config_mapping`).
- **Start 버튼은 안전 기본값으로 비활성화**되어 있으며, 해당 계정의
  매핑이 최신 Refresh 기준으로 `ok` 상태로 교차 검증되어야만
  활성화됩니다 — 저장만 하고 아직 새로고침하지 않았거나, 장치가
  없음/오프라인/미승인/알수없음/디스커버리 실패 상태면 시작할 수
  없습니다.

`ldmanager.discovery.compute_account_connection_statuses()`가
이미 가져온 device 목록으로 상태를 재계산하는 순수 함수라서, Save/
Clear 직후에도 ADB를 다시 호출하지 않고 캐시된 목록 기준으로 패널을
갱신합니다(진짜로 "지금 온라인인지" 확인하려면 Refresh를 다시 눌러야
합니다).

**알려진 한계**: `configs/config.yaml`을 GUI로 저장/삭제하면 YAML이
다시 직렬화되므로, 사람이 손으로 넣은 주석은 보존되지 않습니다.
자세한 내용은 `docs/HANDOFF_CODE.md`의 UI-ADB-001 절 참고.
