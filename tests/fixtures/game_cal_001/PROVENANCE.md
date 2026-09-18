# GAME-CAL-001 real-capture fixtures — provenance

These are the exact, unmodified, real 1280x720 LDPlayer client captures
supplied by the customer for the "REAL-CAPTURE REWORK" follow-up to
GAME-CAL-001, after v1.0.3-rc.1 was withdrawn (customer-reported "Only
0/2 stable screen anchors matched" against real Test-capture output).
They are original in-client screenshots, not phone photos. No player
name, chat, account, or other personal/identifying content is visible
in any of them — only generic in-game Mission UI chrome and mission
text.

## source/ (the 3 original, full, unmodified captures)

| File | Real screen | Objective phrase | Progress | Action shown |
|---|---|---|---|---|
| `completed_target.png` | 임무 (Mission) > 지역 (Region) > 자유 토벌작전, detail panel | 모든 몬스터 처치 | 완료 (complete) | 완료 button |
| `in_progress_target.png` | same modal, different mission instance | 모든 몬스터 처치 | (16/165) | currency action, cost 4400 |
| `non_target.png` | same modal, a *different* mission (야왕궁 토벌작전) | 냉혈사 처치 | (0/450) | currency action (4400) + 순간 이동 button |

These three are used directly (loaded from disk, not re-typed) by
`tests/test_screen_classification_real_assets.py`, which asserts the
expected `MissionScreenState`/`MissionAssessment` classification for
each using the real `OpenCVTemplateRecognizer` — never a fake
always-match recognizer.

## templates/ (derived stable crops, pixel-cropped from `source/` above)

Every file here is a lossless crop of one of the three `source/` PNGs —
no synthetic/hand-drawn pixels, no digit/counter/reward-quantity
content, no mission-title panel text (e.g. never "자유 토벌작전"/"야왕궁
토벌작전" — see `ldmanager/screen_classification.py`'s module docstring
for why). These same files are also copied into the project's real
`templates/` directory so `configs/bounty.example.yaml` can reference
them directly; this copy under `tests/fixtures/` exists so the test
suite has a stable, independent reference that does not depend on
`templates/` being left untouched by some future packet.

| File | Cropped from | Pixel region (of the 1280x720 source) | Used as |
|---|---|---|---|
| `mission_header.png` | `completed_target.png` | x:10-125, y:8-60 | `stable_screen_anchors[0]` — the 임무 (Mission) modal's own icon+title, present on all 3 real captures identically |
| `mission_objective_label.png` | `completed_target.png` | x:320-440, y:475-501 | `stable_screen_anchors[1]` — the "임무 목표" (Mission Objective) row's static UI label, present on all 3 real captures identically |
| `complete_badge.png` | `completed_target.png` | x:590-660, y:522-550 | `complete_state_label` — the "완료" (Complete) badge text, at the same ROI where the other two real captures instead show a "(N/M)" progress counter |
| `currency_action_4400.png` | `in_progress_target.png` | x:830-1020, y:643-698 | `currency_action_labels[0]` — the currency-cost action box (counter + "4400" + icon), confirmed present at the same location on both non-completed real captures |
| `mission_target_phrase.png` | `completed_target.png` | x:300-520, y:515-555 | `mission_target_phrase` — the objective phrase text "모든 몬스터 처치" alone (no digits/quantity), confirmed to match the in-progress-target capture (same phrase) and NOT match the non-target capture (different phrase, "냉혈사 처치") |

Every pixel region above was verified by direct visual inspection of
the crop before being accepted (not assumed), and every classification
claim in the table is independently re-verified by
`tests/test_screen_classification_real_assets.py` against the real
`OpenCVTemplateRecognizer` — not asserted from this document alone.

## What remains NEEDS_REAL_TEST

- Only ONE currency cost (4400) has a real, supplied example — a
  mission whose currency-action cost is a different amount is not yet
  covered by `currency_action_4400.png` alone (see
  `docs/HANDOFF_CODE.md`).
- No distinct, non-digit-specific "in progress" graphic (separate from
  the currency-action box) was present in either real non-completed
  capture, so `in_progress_roi`/`in_progress_label` remain uncalibrated
  (both real non-completed examples classify as `CURRENCY_ACTION`
  instead — still a safe, zero-touch bucket).
- These 3 captures cover only the initial Mission > Region > detail
  view. The refresh-popup/reward/claim/result/mission-list screens used
  by the rest of `bounty_mission.run_one_cycle` are NOT covered by any
  real capture in this fixture set and remain uncalibrated placeholders
  in `configs/bounty.example.yaml`.
- No live device, no real ADB capture pipeline, and no real completion
  tap against an actual LDPlayer instance was exercised anywhere in
  this packet — only these 3 static real PNGs, offline.

## source_extra/ (SLOT-SELECT-CALIBRATION-001)

A 4th real capture, supplied later by the customer after a live crash
report (`UnboundLocalError` on slot selection, see
`docs/HANDOFF_CODE.md`'s `TAP-FALLBACK-CRASH-001` section):

| File | Real screen | Notes |
|---|---|---|
| `mission_list_row1_completed.png` | Same 임무 modal, 임무 목록 (mission list) panel with 5 rows visible (row 1 selected/highlighted, showing its 완료 detail) | Used to measure real pixel row-band boundaries for `slot_select_points`/`select_complete_point` (see `configs/bounty.example.yaml`'s comments for the exact measured Y-boundaries and centers) |

This capture also proved a structural problem with the (never actually
enabled in the shipped example config) `mission_slot_unselected`/
`mission_slot_selected` template idea from the original MVP-001-CV
packet: its crop bakes in the literal mission-title text ("자유
토벌작전"), and even a perfect crop cannot distinguish "row 1" from
"row 3" when both show identical unselected styling — a single
whole-frame template search has no notion of *which* matching row is
the Nth one. `configs/bounty.example.yaml` deliberately leaves both
labels unmapped so slot selection always uses the real,
position-calibrated points instead — the correct tool for "tap the Nth
row of a list."
