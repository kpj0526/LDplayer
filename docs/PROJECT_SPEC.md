# Project Specification

## 목적과 범위

십이지천2M의 자유 토벌작전 임무를 LDPlayer LD1~LD9의 9개 독립 계정에서 관리한다. 계정마다 임무 슬롯 5개를 순서대로 처리하고, `모든 몬스터 처치`와 목표 수량 `200`을 **함께** 판별한 경우에만 임무를 유지한다. 완료(200/200 또는 명확한 완료 표시) → 완료 버튼 → 보상 화면 확인 → 보상 받기 → 결과 확인 → 닫기 → 임무 목록 복귀 → 재갱신의 순환이 MVP 필수 범위다.

## 실행 경계

- Windows 및 LDPlayer LD1~LD9를 사용한다. 각 계정은 서로 다른 ADB serial/port에 명시적으로 매핑한다.
- 캡처와 탭은 항상 해당 계정의 `adb -s <serial>`로만 전달한다. 전역 데스크톱 마우스 좌표는 사용하지 않는다.
- 모든 LDPlayer의 화면 해상도와 게임 UI 설정은 동일해야 한다.
- 자동 로그인, 접속 복구, 사냥터 이동은 범위 밖이다. 접속 종료·ADB 해제·멈춤은 해당 계정만 `ERROR`로 전환하고 사용자가 수동 복구 후 개별 재시작한다.

## 판별과 입력 원칙

화면 요소(슬롯 1~5, 선택 상태, 갱신 버튼/팝업/확인·취소, 새 임무 상세, 목표 문구와 `/200`, 수락, 진행·완료, 완료·보상·결과·닫기·임무 목록)를 각각 별도 대상으로 관리한다. OpenCV 템플릿 매칭과 ROI 판정을 우선 사용하고 필요한 텍스트에는 OCR을 병행한다.

한 번의 OCR 결과만으로 입력하지 않는다. 목표 문구와 `200`을 함께 확인하며, 갱신 비용(4,400/6,600/9,900/14,900 등)은 판별 조건에 사용하지 않는다. 갱신 팝업의 제목·버튼 위치·고정 구조를 독립적으로 확인한 뒤에만 확인을 누른다.

모든 단계는 `캡처 → 현재 화면/조건 확인 → 한 번의 명시적 ADB 탭 → 화면 변화 확인 → 다음 상태` 순서다. 예상하지 못한 화면, 낮은 신뢰도, ADB 오류, 화면 정체 또는 같은 단계의 제한 횟수 초과 실패 시 입력을 중단한다. 모든 재시도와 대기에는 최대 횟수와 타임아웃이 있어야 한다.

## 계정별 상태

`SELECTING_MISSION_SLOT`, `CHECKING_MISSION_STATUS`, `OPENING_REFRESH_CONFIRM`, `CONFIRMING_REFRESH`, `CHECKING_NEW_MISSION`, `ACCEPTING_TARGET_MISSION`, `REJECTING_NON_TARGET_MISSION`, `WAITING_KILL_PROGRESS`, `MISSION_COMPLETED`, `CLICKING_COMPLETE`, `OPENING_REWARD`, `CLAIMING_REWARD`, `CLOSING_REWARD_RESULT`, `RETURNING_TO_MISSION_LIST`, `ERROR`.

LD1~LD9는 각각 독립 Worker, 입력 경로, 시작/정지 신호 및 상태를 가진다. 한 계정 오류는 다른 계정에 영향을 주지 않으며 전체 정지는 모든 자동 입력을 중단한다.

## 현 상태

상태 머신 골격과 단일-serial ADB 입력 분리는 존재하지만, 실제 픽셀을 판별하는 인식기는 아직 구현되지 않았다. 실제 고객 화면의 원본 캡처·템플릿·ROI·해상도 검증 없이는 실게임 동작 또는 MVP 완료를 선언할 수 없다.
