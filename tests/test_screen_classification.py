"""Fixture/mock tests for configurable screen classification + gated
completion touch (GAME-CAL-001).

No real ADB, no real OpenCV/template matching, no real device -- every
recognizer here is an in-memory double. What's under test is the
*classification/gating logic itself*: stable-anchor screen confirmation,
explicit completed/in-progress/currency/unknown/mismatch classification,
and that a completion tap is sent if-and-only-if a freshly captured
precondition is COMPLETED, scoped to exactly one explicit serial, with a
verified postcondition. Real-device/real-template accuracy remains
NEEDS_REAL_TEST -- see docs/HANDOFF_CODE.md.
"""

from pathlib import Path

from ldmanager.adb import AdbBinaryResult
from ldmanager.bounty_config import AnchorSpec, BountyMissionConfig
from ldmanager.coordinates import RelativeCoordinate, RelativeRegion, ScreenSize
from ldmanager.recognition import RecognitionResult, RecognitionStatus
from ldmanager.screen_classification import (
    MissionAssessment,
    MissionScreenState,
    capture_and_classify,
    classify_screen,
    complete_mission_if_verified,
)
from ldmanager.screenshot import DEFAULT_CAPTURE_ARGS
from tests.fakes import FakeAdbRunner, LabelMappingRecognizer

_VALID_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
_SERIAL = "127.0.0.1:5555"
_SERIAL_B = "127.0.0.1:5557"

_KILL_PROGRESS = "200/200"  # legacy explicit-complete counter
_COMPLETE_BADGE = "완료-badge"
_MISSION_SCREEN = "mission_screen"
_REGION_TAB = "region_tab"
_CURRENCY = "button_refresh_6600"
_PROGRESS = "in_progress_indicator"
_TARGET_PHRASE = "phrase"  # matches _config()'s mission_phrase_label default
_TARGET_QTY = "qty"  # matches _config()'s mission_quantity_label default
_TARGET_MATCHED = {_TARGET_PHRASE, _TARGET_QTY}  # both required for TARGET_CONFIRMED


def _roi(x=0.0, y=0.0, w=0.1, h=0.1):
    return RelativeRegion(x=x, y=y, width=w, height=h)


def _config(**overrides) -> BountyMissionConfig:
    defaults = dict(
        slot_select_points=tuple(RelativeCoordinate(x=0.1, y=0.1 * i) for i in range(1, 6)),
        mission_phrase_roi=_roi(),
        mission_phrase_label="phrase",
        mission_quantity_roi=_roi(0.2),
        mission_quantity_label="qty",
        refresh_button_point=RelativeCoordinate(x=0.9, y=0.9),
        refresh_popup_anchor_roi=_roi(0.3),
        refresh_popup_anchor_label="popup-anchor",
        refresh_popup_title_roi=_roi(0.4),
        refresh_popup_title_label="popup-title",
        refresh_confirm_point=RelativeCoordinate(x=0.5, y=0.6),
        kill_progress_roi=_roi(0.5),
        kill_progress_complete_label=_KILL_PROGRESS,
        complete_state_roi=_roi(0.6),
        complete_state_label=_COMPLETE_BADGE,
        select_complete_point=RelativeCoordinate(x=0.1, y=0.2),
        complete_button_point=RelativeCoordinate(x=0.85, y=0.9),
        reward_screen_roi=_roi(0.7),
        reward_screen_label="reward",
        claim_point=RelativeCoordinate(x=0.5, y=0.7),
        result_screen_roi=_roi(0.8),
        result_screen_label="result",
        close_result_point=RelativeCoordinate(x=0.9, y=0.1),
        mission_list_roi=_roi(0.05, 0.05),
        mission_list_label="mission-list",
        screen_size=ScreenSize(width=1000, height=1000),
        templates_dir=Path("templates"),
        threshold=0.8,
        capture_args=DEFAULT_CAPTURE_ARGS,
        stable_screen_anchors=(
            AnchorSpec(roi=_roi(0.0, 0.0, 0.2, 0.05), label=_MISSION_SCREEN),
            AnchorSpec(roi=_roi(0.0, 0.9, 0.2, 0.1), label=_REGION_TAB),
        ),
        currency_action_labels=(_CURRENCY,),
        in_progress_roi=_roi(0.4, 0.4, 0.2, 0.05),
        in_progress_label=_PROGRESS,
        template_map={_CURRENCY: "button_refresh_6600.png"},
    )
    defaults.update(overrides)
    return BountyMissionConfig(**defaults)


def _runner_with_valid_captures(serial=_SERIAL) -> FakeAdbRunner:
    return FakeAdbRunner(
        capture_results={
            (serial, DEFAULT_CAPTURE_ARGS): AdbBinaryResult(
                serial=serial, args=DEFAULT_CAPTURE_ARGS, returncode=0,
                stdout_bytes=_VALID_PNG, stderr="",
            )
        }
    )


class _CenterMappingRecognizer:
    """Like LabelMappingRecognizer, but returns a ``match_center`` on a
    match -- needed to exercise the actual tap path (bare LabelMapping
    Recognizer deliberately never provides one)."""

    def __init__(self, matching_labels):
        self.matching_labels = frozenset(matching_labels)
        self.calls: list = []

    def recognize(self, image_bytes, roi, expected_label, threshold):
        self.calls.append(expected_label)
        if expected_label in self.matching_labels:
            return RecognitionResult(RecognitionStatus.MATCH, expected_label, 1.0, "test: matched", (0.5, 0.5))
        return RecognitionResult(RecognitionStatus.UNKNOWN, None, 0.0, "test: not in matching_labels")


class _StatefulRunner:
    """Delegates to a real FakeAdbRunner, but flips ``state['completed']``
    to False the moment any tap (``run()``) is sent -- modeling the real
    screen transitioning away from the completed state as a direct
    consequence of the tap, for a genuine fresh-postcondition check."""

    def __init__(self, inner: FakeAdbRunner, state: dict):
        self._inner = inner
        self._state = state

    def list_devices(self):
        return self._inner.list_devices()

    def capture_binary(self, serial, args):
        return self._inner.capture_binary(serial, args)

    def run(self, serial, args):
        result = self._inner.run(serial, args)
        self._state["completed"] = False
        return result

    @property
    def calls(self):
        return self._inner.calls

    @property
    def capture_calls(self):
        return self._inner.capture_calls


class _StatefulRecognizer:
    """Matches ``completed_label`` only while ``state['completed']`` is
    true; always matches every label in ``always_matching`` (the stable
    screen anchors, so the screen layout stays confirmed across pre/post
    capture)."""

    def __init__(self, state: dict, completed_label: str, always_matching=frozenset()):
        self._state = state
        self._completed_label = completed_label
        self._always_matching = frozenset(always_matching)
        self.calls: list = []

    def recognize(self, image_bytes, roi, expected_label, threshold):
        self.calls.append(expected_label)
        if expected_label == self._completed_label and self._state["completed"]:
            return RecognitionResult(RecognitionStatus.MATCH, expected_label, 1.0, "test", (0.5, 0.5))
        if expected_label in self._always_matching:
            return RecognitionResult(RecognitionStatus.MATCH, expected_label, 1.0, "test", (0.5, 0.5))
        return RecognitionResult(RecognitionStatus.UNKNOWN, None, 0.0, "test: no match")


# --- classify_screen: explicit five-way classification ---------------------


def test_classify_screen_completed_via_kill_progress_counter():
    recognizer = LabelMappingRecognizer(matching_labels={_MISSION_SCREEN, _REGION_TAB, _KILL_PROGRESS})
    result = classify_screen(_VALID_PNG, _config(), recognizer)
    assert result.state is MissionScreenState.COMPLETED
    assert _KILL_PROGRESS in result.matched_labels


def test_classify_screen_completed_via_complete_state_badge_when_no_button_complete_template():
    recognizer = LabelMappingRecognizer(matching_labels={_MISSION_SCREEN, _REGION_TAB, _COMPLETE_BADGE})
    result = classify_screen(_VALID_PNG, _config(), recognizer)  # template_map has no "button_complete"
    assert result.state is MissionScreenState.COMPLETED
    assert _COMPLETE_BADGE in result.matched_labels


def test_classify_screen_completed_via_button_complete_template_when_configured():
    cfg = _config(template_map={_CURRENCY: "x.png", "button_complete": "button_complete.png"})
    recognizer = LabelMappingRecognizer(matching_labels={_MISSION_SCREEN, _REGION_TAB, "button_complete"})
    result = classify_screen(_VALID_PNG, cfg, recognizer)
    assert result.state is MissionScreenState.COMPLETED
    assert "button_complete" in result.matched_labels


def test_classify_screen_currency_action_matches_configured_label():
    recognizer = LabelMappingRecognizer(matching_labels={_MISSION_SCREEN, _REGION_TAB, _CURRENCY})
    result = classify_screen(_VALID_PNG, _config(), recognizer)
    assert result.state is MissionScreenState.CURRENCY_ACTION
    assert _CURRENCY in result.matched_labels


def test_classify_screen_in_progress_matches_generic_indicator_not_digit_specific():
    """The customer's real "130/180" (a target quantity this project
    never hardcodes) is modeled here as one generic, non-digit-specific
    progress indicator -- never a fixed "x/y" digit template tied to one
    mission's target count."""
    recognizer = LabelMappingRecognizer(matching_labels={_MISSION_SCREEN, _REGION_TAB, _PROGRESS})
    result = classify_screen(_VALID_PNG, _config(), recognizer)
    assert result.state is MissionScreenState.IN_PROGRESS
    assert _PROGRESS in result.matched_labels


def test_classify_screen_unknown_when_screen_confirmed_but_nothing_else_matches():
    recognizer = LabelMappingRecognizer(matching_labels={_MISSION_SCREEN, _REGION_TAB})
    result = classify_screen(_VALID_PNG, _config(), recognizer)
    assert result.state is MissionScreenState.UNKNOWN


def test_classify_screen_mismatch_when_stable_anchors_insufficient():
    """Neither the reward amount nor a dynamic progress number is ever
    consulted for this gate -- only the two configured stable anchors."""
    recognizer = LabelMappingRecognizer(matching_labels={_MISSION_SCREEN, _KILL_PROGRESS, _COMPLETE_BADGE})
    result = classify_screen(_VALID_PNG, _config(), recognizer)  # region_tab never matches
    assert result.state is MissionScreenState.MISMATCH
    assert "1/2" in result.detail


def test_classify_screen_min_stable_anchor_matches_allows_partial_requirement():
    cfg = _config(min_stable_anchor_matches=1)
    recognizer = LabelMappingRecognizer(matching_labels={_MISSION_SCREEN, _KILL_PROGRESS})
    result = classify_screen(_VALID_PNG, cfg, recognizer)  # region_tab absent, but only 1 required
    assert result.state is MissionScreenState.COMPLETED


def test_classify_screen_skips_mismatch_gate_when_no_stable_anchors_configured():
    """Legacy/minimal config (no stable anchors calibrated yet) must
    never fabricate a MISMATCH it has no evidence for."""
    cfg = _config(stable_screen_anchors=())
    recognizer = LabelMappingRecognizer(matching_labels=set())
    result = classify_screen(_VALID_PNG, cfg, recognizer)
    assert result.state is MissionScreenState.UNKNOWN


def test_classify_screen_completed_takes_priority_over_currency_and_progress():
    recognizer = LabelMappingRecognizer(
        matching_labels={_MISSION_SCREEN, _REGION_TAB, _KILL_PROGRESS, _CURRENCY, _PROGRESS}
    )
    result = classify_screen(_VALID_PNG, _config(), recognizer)
    assert result.state is MissionScreenState.COMPLETED


def test_classify_screen_never_mismatches_for_a_different_mission_title():
    """Customer clarification: a mission-list panel title (e.g. "자유
    토벌작전") only appears for one specific objective type -- it is
    never a stable_screen_anchors entry in this project's config (see
    _config() above, which uses only generic "mission_screen"/
    "region_tab" chrome labels). A different mission's title is
    therefore simply never checked by classify_screen() at all, and
    cannot cause a MISMATCH -- only assess_mission_target() (a fully
    separate function) cares about the mission title."""
    # Neither "자유 토벌작전" nor any other mission-title label is ever
    # passed to classify_screen -- it only consults stable_screen_anchors
    # (mission_screen/region_tab) plus the completed/currency/progress
    # anchors, none of which are mission-title text.
    recognizer = LabelMappingRecognizer(matching_labels={_MISSION_SCREEN, _REGION_TAB})
    result = classify_screen(_VALID_PNG, _config(), recognizer)
    assert result.state is not MissionScreenState.MISMATCH
    assert result.state is MissionScreenState.UNKNOWN


# --- capture_and_classify: capture failure vs. classification --------------


def test_capture_and_classify_returns_none_on_capture_failure():
    runner = FakeAdbRunner(
        capture_results={
            (_SERIAL, DEFAULT_CAPTURE_ARGS): AdbBinaryResult(
                serial=_SERIAL, args=DEFAULT_CAPTURE_ARGS, returncode=1, stdout_bytes=b"", stderr="offline",
            )
        }
    )
    recognizer = LabelMappingRecognizer(matching_labels={_MISSION_SCREEN, _REGION_TAB, _KILL_PROGRESS})
    assert capture_and_classify(runner, _SERIAL, _config(), recognizer) is None


def test_capture_and_classify_returns_classification_on_success():
    runner = _runner_with_valid_captures()
    recognizer = LabelMappingRecognizer(matching_labels={_MISSION_SCREEN, _REGION_TAB, _KILL_PROGRESS})
    result = capture_and_classify(runner, _SERIAL, _config(), recognizer)
    assert result is not None
    assert result.state is MissionScreenState.COMPLETED


# --- complete_mission_if_verified: touch only after verified COMPLETED -----


def test_complete_mission_taps_only_when_precondition_completed_and_postcondition_verified():
    state = {"completed": True}
    runner = _StatefulRunner(_runner_with_valid_captures(), state)
    recognizer = _StatefulRecognizer(state, _COMPLETE_BADGE, always_matching={_MISSION_SCREEN, _REGION_TAB} | _TARGET_MATCHED)
    cfg = _config(template_map={_COMPLETE_BADGE: "complete.png"})

    result = complete_mission_if_verified(serial=_SERIAL, runner=runner, recognizer=recognizer, config=cfg)

    assert result.ok is True
    assert result.tap_sent is True
    assert result.precondition is MissionScreenState.COMPLETED
    assert result.postcondition is not MissionScreenState.COMPLETED
    assert len(runner.calls) == 1
    assert runner.calls[0][0] == _SERIAL


def test_complete_mission_no_touch_when_in_progress():
    runner = _runner_with_valid_captures()
    recognizer = LabelMappingRecognizer(matching_labels={_MISSION_SCREEN, _REGION_TAB, _PROGRESS})
    cfg = _config(template_map={_COMPLETE_BADGE: "complete.png"})

    result = complete_mission_if_verified(serial=_SERIAL, runner=runner, recognizer=recognizer, config=cfg)

    assert result.ok is False
    assert result.tap_sent is False
    assert result.precondition is MissionScreenState.IN_PROGRESS
    assert runner.calls == []


def test_complete_mission_no_touch_when_currency_action():
    runner = _runner_with_valid_captures()
    recognizer = LabelMappingRecognizer(matching_labels={_MISSION_SCREEN, _REGION_TAB, _CURRENCY})
    cfg = _config(template_map={_COMPLETE_BADGE: "complete.png", _CURRENCY: "x.png"})

    result = complete_mission_if_verified(serial=_SERIAL, runner=runner, recognizer=recognizer, config=cfg)

    assert result.ok is False
    assert result.tap_sent is False
    assert result.precondition is MissionScreenState.CURRENCY_ACTION
    assert runner.calls == []


def test_complete_mission_no_touch_when_unknown():
    runner = _runner_with_valid_captures()
    recognizer = LabelMappingRecognizer(matching_labels={_MISSION_SCREEN, _REGION_TAB})
    cfg = _config(template_map={_COMPLETE_BADGE: "complete.png"})

    result = complete_mission_if_verified(serial=_SERIAL, runner=runner, recognizer=recognizer, config=cfg)

    assert result.ok is False
    assert result.tap_sent is False
    assert result.precondition is MissionScreenState.UNKNOWN
    assert runner.calls == []


def test_complete_mission_no_touch_when_mismatch():
    runner = _runner_with_valid_captures()
    recognizer = LabelMappingRecognizer(matching_labels={_KILL_PROGRESS})  # stable anchors absent
    cfg = _config(template_map={_COMPLETE_BADGE: "complete.png"})

    result = complete_mission_if_verified(serial=_SERIAL, runner=runner, recognizer=recognizer, config=cfg)

    assert result.ok is False
    assert result.tap_sent is False
    assert result.precondition is MissionScreenState.MISMATCH
    assert runner.calls == []


def test_complete_mission_no_touch_when_mission_title_is_not_the_target():
    """A DIFFERENT mission (non-"모든 몬스터 처치" title) that happens to
    also show a completed-looking badge must never be tapped -- the
    screen state alone is not enough; the currently-selected mission
    must independently be confirmed as the required target objective.
    (The fake recognizer used here reports an uncalibrated/uncertain
    phrase+quantity rather than a confident non-match, so the exact
    assessment is RECOGNITION_FAILED rather than NON_TARGET_CONFIRMED --
    both are equally safe, fail-closed, zero-touch outcomes; see
    test_complete_mission_no_touch_for_a_confidently_different_title
    below for the confident-non-match case.)"""

    recognizer = LabelMappingRecognizer(
        matching_labels={_MISSION_SCREEN, _REGION_TAB, _KILL_PROGRESS}  # completed, but no _TARGET_MATCHED
    )
    runner = _runner_with_valid_captures()
    cfg = _config(template_map={_COMPLETE_BADGE: "complete.png"})

    result = complete_mission_if_verified(serial=_SERIAL, runner=runner, recognizer=recognizer, config=cfg)

    assert result.ok is False
    assert result.tap_sent is False
    assert result.precondition is MissionScreenState.COMPLETED  # the screen itself IS completed
    assert result.mission_target in (MissionAssessment.NON_TARGET_CONFIRMED, MissionAssessment.RECOGNITION_FAILED)
    assert runner.calls == []  # never tapped


def test_complete_mission_no_touch_for_a_confidently_different_title():
    """A recognizer that *confidently* reports a different mission title
    (NO_MATCH, not merely UNKNOWN) is classified precisely
    NON_TARGET_CONFIRMED -- still zero-touch."""

    class _ConfidentNonMatchRecognizer:
        def __init__(self, matching_labels):
            self.matching_labels = frozenset(matching_labels)

        def recognize(self, image_bytes, roi, expected_label, threshold):
            if expected_label in self.matching_labels:
                return RecognitionResult(RecognitionStatus.MATCH, expected_label, 1.0, "test", (0.5, 0.5))
            return RecognitionResult(RecognitionStatus.NO_MATCH, None, 0.1, "test: confidently absent")

    recognizer = _ConfidentNonMatchRecognizer(matching_labels={_MISSION_SCREEN, _REGION_TAB, _KILL_PROGRESS})
    runner = _runner_with_valid_captures()
    cfg = _config(template_map={_COMPLETE_BADGE: "complete.png"})

    result = complete_mission_if_verified(serial=_SERIAL, runner=runner, recognizer=recognizer, config=cfg)

    assert result.ok is False
    assert result.tap_sent is False
    assert result.precondition is MissionScreenState.COMPLETED
    assert result.mission_target is MissionAssessment.NON_TARGET_CONFIRMED
    assert runner.calls == []


def test_complete_mission_no_touch_when_precondition_capture_fails():
    runner = FakeAdbRunner(
        capture_results={
            (_SERIAL, DEFAULT_CAPTURE_ARGS): AdbBinaryResult(
                serial=_SERIAL, args=DEFAULT_CAPTURE_ARGS, returncode=1, stdout_bytes=b"", stderr="offline",
            )
        }
    )
    recognizer = LabelMappingRecognizer(matching_labels={_MISSION_SCREEN, _REGION_TAB, _KILL_PROGRESS})
    cfg = _config(template_map={_COMPLETE_BADGE: "complete.png"})

    result = complete_mission_if_verified(serial=_SERIAL, runner=runner, recognizer=recognizer, config=cfg)

    assert result.ok is False
    assert result.tap_sent is False
    assert result.precondition is None
    assert runner.calls == []


def test_complete_mission_refuses_blank_serial_with_zero_calls():
    runner = _runner_with_valid_captures()
    recognizer = LabelMappingRecognizer(matching_labels={_MISSION_SCREEN, _REGION_TAB, _KILL_PROGRESS})
    cfg = _config(template_map={_COMPLETE_BADGE: "complete.png"})

    result = complete_mission_if_verified(serial="   ", runner=runner, recognizer=recognizer, config=cfg)

    assert result.ok is False
    assert result.tap_sent is False
    assert runner.calls == []
    assert runner.capture_calls == []


def test_complete_mission_no_touch_when_should_stop_true_before_capture():
    runner = _runner_with_valid_captures()
    recognizer = LabelMappingRecognizer(matching_labels={_MISSION_SCREEN, _REGION_TAB, _KILL_PROGRESS})
    cfg = _config(template_map={_COMPLETE_BADGE: "complete.png"})

    result = complete_mission_if_verified(
        serial=_SERIAL, runner=runner, recognizer=recognizer, config=cfg, should_stop=lambda: True
    )

    assert result.ok is False
    assert result.tap_sent is False
    assert runner.capture_calls == []
    assert runner.calls == []


def test_complete_mission_no_touch_when_should_stop_true_after_precondition():
    runner = _runner_with_valid_captures()
    recognizer = LabelMappingRecognizer(matching_labels={_MISSION_SCREEN, _REGION_TAB, _KILL_PROGRESS})
    cfg = _config(template_map={_COMPLETE_BADGE: "complete.png"})
    calls = {"n": 0}

    def should_stop():
        calls["n"] += 1
        return calls["n"] > 1  # false on the first check, true on the second (after precondition)

    result = complete_mission_if_verified(
        serial=_SERIAL, runner=runner, recognizer=recognizer, config=cfg, should_stop=should_stop
    )

    assert result.ok is False
    assert result.tap_sent is False
    assert result.precondition is MissionScreenState.COMPLETED
    assert runner.calls == []  # precondition was COMPLETED, but stop was requested before the tap


def test_complete_mission_two_accounts_use_independent_serials():
    runner_a = _runner_with_valid_captures(_SERIAL)
    runner_b = _runner_with_valid_captures(_SERIAL_B)
    recognizer = _CenterMappingRecognizer(matching_labels={_MISSION_SCREEN, _REGION_TAB, _KILL_PROGRESS} | _TARGET_MATCHED)
    cfg = _config(template_map={_COMPLETE_BADGE: "complete.png"})

    result_a = complete_mission_if_verified(serial=_SERIAL, runner=runner_a, recognizer=recognizer, config=cfg)
    result_b = complete_mission_if_verified(serial=_SERIAL_B, runner=runner_b, recognizer=recognizer, config=cfg)

    assert result_a.tap_sent is True
    assert result_b.tap_sent is True
    assert runner_a.calls and all(call[0] == _SERIAL for call in runner_a.calls)
    assert runner_b.calls and all(call[0] == _SERIAL_B for call in runner_b.calls)
    assert not any(call[0] == _SERIAL for call in runner_b.calls)
    assert not any(call[0] == _SERIAL_B for call in runner_a.calls)


def test_complete_mission_bounded_when_postcondition_never_resolves():
    """The tap IS sent (irreversible, reported honestly as tap_sent=True)
    but the bounded postcondition loop gives up after exactly the
    configured number of attempts if the screen never appears to leave
    the completed state."""
    state = {"completed": True}
    # A plain (non-flipping) runner: the tap never actually changes what
    # the next capture returns, modeling a tap that landed but had no
    # observable effect.
    runner = _runner_with_valid_captures()
    recognizer = _StatefulRecognizer(state, _COMPLETE_BADGE, always_matching={_MISSION_SCREEN, _REGION_TAB} | _TARGET_MATCHED)
    cfg = _config(template_map={_COMPLETE_BADGE: "complete.png"})

    result = complete_mission_if_verified(
        serial=_SERIAL, runner=runner, recognizer=recognizer, config=cfg, max_postcondition_attempts=2
    )

    assert result.tap_sent is True
    assert result.ok is False
    assert result.postcondition is MissionScreenState.COMPLETED
    assert len(runner.calls) == 1  # exactly one tap, never repeated
