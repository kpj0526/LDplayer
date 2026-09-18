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
| `reward_screen.png` | The actual "보상 받기" (Get Reward) screen -- reached for real after all 5 slots were really accepted and the real complete button was really tapped (REWARD-SCREEN-CALIBRATION-001, see `docs/HANDOFF_CODE.md`) | A real, undoctored Test-capture PNG (1280x720) supplied by the customer after `reward_verify_failed` stalled the cycle -- this screen's `reward_screen_roi`/`reward_screen_label`/`claim_point`/`button_claim_reward` had never been calibrated against any real capture before this. Two real crops were taken from it (see `templates/` table below): the "확률" (odds) label -- generic reward-screen chrome, confirmed absent from every other real capture -- and the "보상 받기" button itself. |

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

### `reward_screen.png`'s derived crops (REWARD-SCREEN-CALIBRATION-001)

| File | Cropped from | Pixel region (of the 1280x720 source) | Used as |
|---|---|---|---|
| `reward_odds_label.png` | `reward_screen.png` | x:595-685, y:198-235 | `reward_screen_label` ("확률") — confirmed (real `OpenCVTemplateRecognizer`, `tests/test_reward_screen_real_assets.py`) to match only `reward_screen.png`, never any of the other 4 real captures |
| `reward_claim_button.png` | `reward_screen.png` | x:551-732, y:487-536 | `button_claim_reward` — the real "보상 받기" button, replacing an old, never-validated placeholder of the same config key; same real cross-check as above |

### Safety verification for `COMPLETE-DETAIL-001` (correction below)

Two captures were supplied by the customer while diagnosing a live
"Complete tap failed" result, to check whether the existing
`button_complete.png` template (an older, pre-`GAME-CAL-001` asset,
never previously cross-checked against these specific screens) was
producing a false positive on a genuinely-incomplete mission. **Both
files were saved under names that turned out to be inaccurate**: two
copies of the SAME "닫기" (Close) result popup (야왕궁 토벌작전) were
saved as `in_progress_51_of_200.png` and `close_result_screen.png` --
neither actually contained the "모든 몬스터 처치 (51/200)" screen shown
alongside it at the time (that specific frame was never saved to
disk). Both mislabeled/duplicate files have since been removed; the
real "닫기" screen they actually contained is now correctly saved as
`result_close_screen.png` (below), and this doesn't change the earlier
safety conclusion, since `button_complete.png` was tested against the
real Close-popup content either way:

`button_complete.png` confidence against the real Close-popup content:
0.774, safely below the 0.8 threshold -- correctly NOT matched. Across
all real captures now on file, `button_complete.png` matches only
screens with a genuinely visible "완료" button. The real cause of
"Complete tap failed" was traced to the (separately fixed)
`select_complete_point` "always row 1" limitation --
`COMPLETE-SLOT-TRACKING-001` in `docs/HANDOFF_CODE.md`.

### `result_close_screen.png` (RESULT-CLOSE-CALIBRATION-001)

The real post-claim "결과"/close screen -- reached for real after a
real claim tap, and where a live run repeatedly stalled (`docs/HANDOFF_CODE.md`'s
`RESULT-CLOSE-CALIBRATION-001` section). Same visual family as
`reward_screen.png` (same emblem/title/"확률" layout) but with only
ONE reward icon and a "닫기" (Close) button instead of "보상 받기".

Investigated whether the "보상 받기"/"닫기" buttons could be reliably
told apart by template matching (to give `result_screen`/
`button_close_reward` their own dedicated real anchor, the same way
`reward_claim_button.png` was calibrated) -- even a tight, text-only
crop of each (no ornate border) scored too close to safely separate
(a "닫기" crop scored 0.80 against the real `reward_screen.png`, right
at the 0.8 threshold). **Conclusion: these two buttons cannot be
reliably told apart by template matching alone** (same gold-button
frame, only ~2 characters of text differ). No derived template crop
was kept for this reason.

Instead: `result_screen_label` reuses `reward_odds_label` ("확률" --
confirmed present on both the reward AND result popups at ~0.81-1.0
confidence, never on a plain detail/list screen at ~0.26-0.30) as
the completion check, and `mission_list_label` was recalibrated to
reuse `mission_objective_label` ("임무 목표" -- confirmed present on
every plain detail/list real capture at ~0.998-1.0, and confirmed to
NOT match either popup at ~0.07, a far larger and safer margin than
the old placeholder "현상금 목록" ever had). `close_result_point` was
measured directly from `result_close_screen.png` (same real,
measured position as `claim_point` -- same button frame, different
game state) and is now used unconditionally (no dynamic template
search at all for this one step -- see
`bounty_mission.py`'s `RESULT-CLOSE-CALIBRATION-001` comment).

### Region-quest list + renewal-confirm popup (REFRESH-CALIBRATION-001)

Three more real captures, supplied by the customer after a live report
of "Slot 3: refresh-open tap failed" on a real, never-target-matching
dungeon-type mission ("십변도 토벌작전[던전]" / 귀마황 처치 (0/250)):

| File | Real screen | Notes |
|---|---|---|
| `region_list_slot3_dungeon.png` | 임무 > 지역 list, slot 3 ("십변도 토벌작전[던전]") selected | Shows the persistent bottom-right currency-cost action box, "0  4400" |
| `region_list_slot1_named_quest.png` | Same list, slot 1 ("야왕궁 토벌작전") selected instead | Pixel-identical (`cv2.absdiff` mean 0.0) to the other capture at the same currency-cost-box region -- confirms this box is positionally fixed regardless of which slot/mission is currently selected |
| `region_quest_renew_confirm.png` | "지역 퀘스트를 갱신 하시겠습니까?" renewal-confirmation dialog (갱신 금액 4,400 / 보유 금액 .../ 취소 / 확인) | The REAL refresh-confirmation popup -- entirely different text/layout from the old, never-calibrated placeholder assumption (anchor label "새로고침", title label "확인") |

A 4th capture, `bounty_detail_popup.png` ("자유 토벌작전" mission-detail
popup with 임무 목표/보상/price/확인, sent by the customer as a "here's
what this looks like" reference), was also saved for cross-checking
false positives but is NOT the refresh-confirm popup -- it's a
separate, unrelated detail view.

**Root cause**: `refresh_button_point`/`refresh_popup_anchor_roi`/
`refresh_popup_title_roi`/`refresh_confirm_point` were all placeholder
values, never calibrated. Worse, `button_refresh_4400/6600/9900/
14900`/`button_refresh_confirm` (mapped in `template_map`) are
pre-GAME-CAL-001 mock assets (380x116/180x55 -- wrong proportions for
a 1280x720 capture) that never confidently match a real screen; because
`template_map` being non-empty overall makes `_tap_any_template()`/
`_tap_template()` return a hard `False` (not `None`) for an unconfident
match, this silently blocked the fixed-point fallback from ever
running -- the same `TAP-FALLBACK-CRASH-001`/`SLOT-SELECT-CALIBRATION-
001` gotcha, a third time.

**Fix**: `refresh_button_point` was measured as the center of the real
currency-cost action box -- which turned out to be the EXACT same real
UI element already calibrated in `GAME-CAL-001` as
`currency_action_4400.png` (cross-validated via direct template match:
0.993 confidence at pixel offset (830, 643), matching this packet's
independent hand-measurement to within 2px). Since that box's role is
positionally fixed regardless of its currently displayed price, and is
present at the identical pixel position across three independent real
captures (2 list views + 1 GAME-CAL-001 detail view), refresh-open now
always taps it directly -- no template search. Two real crops were
taken from `region_quest_renew_confirm.png` for structural popup
verification (see `templates/` table below), and `refresh_confirm_point`
was measured directly as the popup's real "확인" button center. The old
`button_refresh_*`/`button_refresh_confirm` template_map entries were
removed (see `configs/bounty.example.yaml`'s comment) and
`bounty_mission.py`'s refresh-open/refresh-confirm steps no longer
attempt template matching at all.

### `region_quest_renew_confirm.png`'s derived crops (REFRESH-CALIBRATION-001)

| File | Cropped from | Pixel region (of the 1280x720 source) | Used as |
|---|---|---|---|
| `refresh_popup_title.png` | `region_quest_renew_confirm.png` | x:332-947, y:174-206 | `refresh_popup_title_label` -- the full renewal-question sentence "지역 퀘스트를 갱신 하시겠습니까?"; confirmed (real `OpenCVTemplateRecognizer`, `tests/test_refresh_popup_real_assets.py`) to match only this real popup, never any of the other 9 real captures on file (next-highest confidence: 0.721, still under the 0.8 threshold) |
| `refresh_popup_renew_label.png` | `region_quest_renew_confirm.png` | x:375-465, y:307-330 | `refresh_popup_anchor_label` -- the "갱신 금액" (renewal amount) label alone (not the value); same real cross-check as above, confirmed absent from every other real capture |

`refresh_confirm_point` (x:660-842, y:498-550 real "확인" button bbox,
center measured directly) and `refresh_button_point` (x:830-1020,
y:643-698 real currency-action-box bbox, same as `currency_action_4400`)
were both measured by mean-brightness row/column scans of the real
captures, the same methodology used throughout this fixture set --
never eyeballed.

### What remains NEEDS_REAL_TEST (REFRESH-CALIBRATION-001)

- The exact game action that opens `region_quest_renew_confirm.png` is
  inferred from real evidence (the currency-action box is positionally
  fixed and present on every real capture checked), not directly
  observed as a single continuous tap-then-popup sequence -- the
  customer's captures were supplied as separate reference screenshots,
  not a recorded interaction sequence. If `refresh_button_point` turns
  out not to open this exact popup on some other screen state, the
  structural `refresh_popup_title`/`refresh_popup_renew_label` check
  immediately downstream will safely refuse to confirm (never taps
  blind), reporting `REFRESH_POPUP_NOT_VERIFIED` -- fails closed either
  way.
- No live ADB/LDPlayer/game session was used to verify this fix --
  verified against the real supplied captures, offline.

### `bounty_accept_popup_target.png` (ACCEPT-CONFIRM-001)

A real customer live run got stuck on this exact screen -- the "자유
토벌작전" mission-detail popup that opens after selecting a slot,
showing the real target phrase "모든 몬스터 처치 (0/200)" (matches
`mission_target_phrase` at 0.982 confidence). Confirmed near-identical
(mean pixel diff 1.08/255 -- compression-level noise only) to the
earlier `bounty_detail_popup.png` capture, but saved and documented
separately since it's the specific capture used to diagnose and fix
this bug (the earlier one was sent only as a "here's what this looks
like" reference, before the bug was understood).

**Root cause**: `run_one_cycle`'s per-slot acceptance check
(`_accept_or_refresh_slot`) has two paths to "target confirmed": (1)
the FAST path, when the target phrase/quantity already matches on the
very first check (no refresh needed), and (2) the path after a
refresh+confirm round-trip. Only path (2) ever tapped an accept/
confirm button (`button_accept_mission`, itself a stale, unreliable
pre-GAME-CAL-001 placeholder asset -- 180x55, scores only 0.726
against this real popup, below the 0.8 threshold). Path (1) returned
"accepted" without tapping anything at all, leaving this popup open on
screen -- every subsequent slot's select tap then landed harmlessly on
the still-open popup instead of the mission list underneath, and the
whole cycle stalled here indefinitely. This is exactly the screen the
customer reported being stuck on.

**Fix**: both paths now always tap a single real, measured
`accept_mission_point` directly (no template search) -- its real
"확인" button bounding box was measured as x:662-840, y:500-550
(center 751,525 -- rel 0.5867/0.7292), by the same mean-brightness
row/column scan methodology used throughout this fixture set.
Interestingly, this measures to within 1px of `refresh_confirm_point`
(x:660-842, y:498-550, from `region_quest_renew_confirm.png` in
`REFRESH-CALIBRATION-001`) -- both popups appear to share the same
modal footer button-bar convention -- but `accept_mission_point` was
kept as its own, separately-measured/documented config field rather
than silently reused, since the two popups are semantically distinct
and nothing guarantees they'll always coincide.

### High refresh-count real captures (verification, no fix needed)

The customer manually refreshed one bounty slot repeatedly (observed
counts up to 7, prices up to 75,500 -- confirming refresh counts and
prices go well past the 4 tiers seen in earlier captures) and supplied
the screens along the way, plus the non-target "야왕궁 토벌작전" (강시
처치) popup encountered mid-refresh, plus the final detail view
reached once a mission that's already complete gets accepted (shows
"완료" instead of a "0/200" counter).

| File | Real screen | Result |
|---|---|---|
| `bounty_popup_count7_75500.png` | Target popup, refresh count 7, price 75,500 | `mission_target_phrase` matches (0.982); `accept_mission_point`'s real button bbox (x:662-840, y:500-550) is UNCHANGED by the price's digit count -- confirmed via direct row/column scan, identical to the low-count capture |
| `region_popup_nontarget_gangsi.png` | "야왕궁 토벌작전" / 강시 처치 non-target popup | Correctly rejected: `mission_target_phrase` does not match (0.737 < 0.8); `refresh_popup_title_label` does not false-positive on it either (0.722 < 0.8) |
| `bounty_detail_complete_final.png` | Final detail view: "임무 목표: 모든 몬스터 처치 완료" + real 완료 button, no popup | Correctly detected as BOTH target (`mission_target_phrase`, phrase-only, matches at 0.999) AND complete (`complete_state_label` matches at 0.999, `button_complete` matches at 0.903) |

No bug found in this batch -- REFRESH-CALIBRATION-001/ACCEPT-CONFIRM-
001's real-measured positions and GAME-CAL-001's completion detection
all independently verified correct against these 3 new real captures.
Added as `tests/test_high_refresh_count_real_assets.py` (6 tests) for
permanent regression coverage. If a live run still stalls somewhere in
this sequence, the failure is likely at a step downstream of
`bounty_detail_complete_final.png` (the complete tap itself, or
whatever follows) -- not yet covered by any real capture.

### Correction to REFRESH-CALIBRATION-001's `refresh_button_point` (REFRESH-TRIGGER-CORRECTION-001)

The customer supplied a short screen recording demonstrating a manual,
successful refresh of a dungeon-type mission ("십변도
토벌작전[던전]"): they tapped the accept popup's OWN embedded price/
counter box (immediately left of the "확인" button, same row) -- NOT
the persistent currency-action box on the underlying list view that
`REFRESH-CALIBRATION-001` had calibrated `refresh_button_point`
against. That tap visibly opened the real "지역 퀘스트를 갱신
하시겠습니까?" dialog, confirming the correct trigger.

**Root cause of the original miscalibration**: these two boxes share
nearly identical visual styling (counter + price + icon, same gold
border) and were never directly compared side by side. `REFRESH-
CALIBRATION-001` measured and cross-validated its box against
`currency_action_4400.png` (GAME-CAL-001's crop, itself validated
against `in_progress_target.png`/`region_list_*.png` -- all captures
with NO popup open) -- a real, confidently-matching box, just the
WRONG one for this tap. Since `ACCEPT-CONFIRM-001` established that
selecting a slot immediately shows the accept popup (not a bare list
row), `refresh_button_point`'s tap always fires while that popup is
already open, and the underlying list's box is not interactive at
that moment (the popup blocks it).

**Fix**: `refresh_button_point` is now the real, measured center of
the popup's own price box (bbox x:438-622, y:498-552 in the 1280x720
real captures `bounty_accept_popup_target.png` and
`bounty_popup_count7_75500.png` -- confirmed identical position at
refresh counts 1 and 7 / prices 6600 and 75500, i.e. unaffected by the
price's digit count, the same way `accept_mission_point`'s "확인"
button position was already confirmed unaffected).

### `refresh_result_popup_1/2.png` (REFRESH-RESULT-DISMISS-001)

A real customer live run stalled repeatedly ("Slot 3: refresh popup
never verified") even after `REFRESH-TRIGGER-CORRECTION-001` and
`RETRY-BUDGET-001/002` shipped. The customer supplied 4 real
screenshots of the actual stuck screen (3 identical + 1 with a
different underlying list state) -- an arch-topped popup titled with
the newly-rolled mission's type ("자유 토벌작전"), showing "확률"
(odds), a single reward icon (100,000), and a "닫기" button. Two
distinct captures kept (`refresh_result_popup_1.png`,
`refresh_result_popup_2.png`).

**Root cause**: after confirming a mission renewal (`지역 퀘스트를
갱신 하시겠습니까?` -> `확인`), the game shows this ONE MORE brief
acknowledgment popup for the newly-rolled mission before returning to
the normal accept-popup state. The refresh loop never knew about this
screen, so every subsequent popup-verify/mission-acceptability check
saw this unexpected screen and correctly reported "not verified"/"not
acceptable" -- looping forever without ever dismissing it.

**Fix**: reuses two already-calibrated assets, no new template or
position measured:
- `reward_screen_label` ("확률", the same real anchor from
  `REWARD-SCREEN-CALIBRATION-001`) matches this popup at 1.0
  confidence on both real captures -- structurally identical to the
  real reward screen.
- The popup's real "닫기" button bbox (measured: x:552-732, y:486-537)
  coincides almost exactly with the already-calibrated
  `close_result_point`/`claim_point` value (0.5012/0.7104 rel ->
  641.5/511.5 px, comfortably inside the measured bbox) -- the same
  real button position reused a third time across three structurally
  related popups (reward screen, result screen, and now this
  acknowledgment popup).

`_accept_or_refresh_slot`'s refresh loop now does a single best-effort
check (not a bounded retry loop) right after the confirm tap: if
`reward_screen_label` matches, tap `close_result_point` to dismiss it
before re-checking mission acceptability. If the popup isn't showing,
this is a harmless no-op.
