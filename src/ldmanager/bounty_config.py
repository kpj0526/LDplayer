"""Free regional-bounty five-slot mission configuration (MVP-001-CV).

Same safety posture as ``mission_config.py``: every ROI/coordinate/
label/threshold/retry/timeout value is explicit and validated, nothing
is guessed. Kept as its own module (rather than folded into
``mission_config.py``) since the customer-video flow this models is
structurally richer than the earlier generic 5-slot mock — separate
slot selection, a refresh confirmation popup that must be verified
*structurally* (never by its displayed, variable cost), a two-condition
mission-acceptance check, and a distinct reward/claim/result/close
flow.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from .coordinates import (
    InvalidCoordinateError,
    InvalidScreenSizeError,
    RelativeCoordinate,
    RelativeRegion,
    ScreenSize,
)
from .screenshot import DEFAULT_CAPTURE_ARGS

BOUNTY_CONFIG_PATH_ENV_VAR = "LDMANAGER_BOUNTY_CONFIG"
DEFAULT_BOUNTY_CONFIG_RELPATH = Path("configs") / "bounty.yaml"

DEFAULT_SLOT_COUNT = 5


class BountyConfigError(Exception):
    """Raised for missing or malformed bounty-mission configuration."""


@dataclass(frozen=True)
class BountyMissionConfig:
    """Everything the free-regional-bounty state machine needs.

    Every field is explicit/validated; nothing here is a fixed cost
    value used for detection — the refresh popup is confirmed via
    ``refresh_popup_anchor_*``/``refresh_popup_title_*`` structural
    checks, never by reading the (variable) refresh cost.
    """

    # Slot selection (tap to select/check slot i, 1-indexed by position).
    slot_select_points: tuple[RelativeCoordinate, ...]

    # Mission acceptance: BOTH must be recognized, never just one.
    mission_phrase_roi: RelativeRegion
    mission_phrase_label: str
    mission_quantity_roi: RelativeRegion
    mission_quantity_label: str

    # Refresh (reroll) flow.
    refresh_button_point: RelativeCoordinate
    refresh_popup_anchor_roi: RelativeRegion
    refresh_popup_anchor_label: str
    refresh_popup_title_roi: RelativeRegion
    refresh_popup_title_label: str
    refresh_confirm_point: RelativeCoordinate

    # Kill-progress / completion eligibility (two independent signals).
    kill_progress_roi: RelativeRegion
    kill_progress_complete_label: str
    complete_state_roi: RelativeRegion
    complete_state_label: str

    # Complete -> reward -> claim -> result -> close -> mission list.
    select_complete_point: RelativeCoordinate
    complete_button_point: RelativeCoordinate
    reward_screen_roi: RelativeRegion
    reward_screen_label: str
    claim_point: RelativeCoordinate
    result_screen_roi: RelativeRegion
    result_screen_label: str
    close_result_point: RelativeCoordinate
    mission_list_roi: RelativeRegion
    mission_list_label: str

    screen_size: ScreenSize
    templates_dir: Path
    threshold: float = 0.8

    max_capture_attempts: int = 3
    max_refresh_attempts: int = 5
    max_popup_verify_attempts: int = 3
    max_kill_progress_poll_attempts: int = 10
    max_reward_verify_attempts: int = 3
    max_result_verify_attempts: int = 3
    max_mission_list_verify_attempts: int = 3
    retry_delay_seconds: float = 0.0
    capture_args: tuple[str, ...] = DEFAULT_CAPTURE_ARGS

    @property
    def slot_count(self) -> int:
        return len(self.slot_select_points)


def default_bounty_config_path() -> Path:
    return Path.cwd() / DEFAULT_BOUNTY_CONFIG_RELPATH


def resolve_bounty_config_path(explicit_path: Optional[Path] = None) -> Path:
    if explicit_path is not None:
        return Path(explicit_path)
    env_value = os.environ.get(BOUNTY_CONFIG_PATH_ENV_VAR)
    if env_value:
        return Path(env_value)
    return default_bounty_config_path()


def _require(raw: dict, key: str, path: Path) -> object:
    if key not in raw:
        raise BountyConfigError(f"Missing required key '{key}' in {path}.")
    return raw[key]


def _region(raw: dict, key: str, path: Path) -> RelativeRegion:
    value = _require(raw, key, path)
    if not isinstance(value, dict):
        raise BountyConfigError(f"'{key}' in {path} must be a mapping with x/y/width/height.")
    try:
        return RelativeRegion(x=value["x"], y=value["y"], width=value["width"], height=value["height"])
    except KeyError as exc:
        raise BountyConfigError(f"'{key}' in {path} is missing field {exc}.") from exc
    except InvalidCoordinateError as exc:
        raise BountyConfigError(f"'{key}' in {path} is invalid: {exc}") from exc


def _point(raw: dict, key: str, path: Path) -> RelativeCoordinate:
    value = _require(raw, key, path)
    if not isinstance(value, dict):
        raise BountyConfigError(f"'{key}' in {path} must be a mapping with x/y.")
    try:
        return RelativeCoordinate(x=value["x"], y=value["y"])
    except KeyError as exc:
        raise BountyConfigError(f"'{key}' in {path} is missing field {exc}.") from exc
    except InvalidCoordinateError as exc:
        raise BountyConfigError(f"'{key}' in {path} is invalid: {exc}") from exc


def _label(raw: dict, key: str, path: Path) -> str:
    value = _require(raw, key, path)
    if not isinstance(value, str) or not value.strip():
        raise BountyConfigError(f"'{key}' in {path} must be a non-empty string.")
    return value


def _positive_int(raw: dict, key: str, default: int, path: Path) -> int:
    value = raw.get(key, default)
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise BountyConfigError(f"'{key}' in {path} must be a positive integer, got {value!r}.")
    return value


def load_bounty_config(explicit_path: Optional[Path] = None) -> BountyMissionConfig:
    """Load and validate a :class:`BountyMissionConfig` from YAML.

    Fails loudly (no silent fallback, no guessed ROI/coordinate/label)
    when the file is missing or malformed.
    """

    path = resolve_bounty_config_path(explicit_path)
    if not path.is_file():
        raise BountyConfigError(
            f"Bounty config file not found: {path}. Copy "
            "configs/bounty.example.yaml to configs/bounty.yaml (or set "
            f"{BOUNTY_CONFIG_PATH_ENV_VAR}) and fill in your own ROIs/"
            "coordinates before running again."
        )

    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    if not isinstance(raw, dict):
        raise BountyConfigError(f"{path} must contain a YAML mapping at the top level.")

    slot_points_raw = _require(raw, "slot_select_points", path)
    if not isinstance(slot_points_raw, list) or not slot_points_raw:
        raise BountyConfigError(f"'slot_select_points' in {path} must be a non-empty list.")
    slot_select_points = tuple(
        _point_from_item(item, f"slot_select_points[{i}]", path) for i, item in enumerate(slot_points_raw)
    )

    screen_size_raw = _require(raw, "screen_size", path)
    if not isinstance(screen_size_raw, dict):
        raise BountyConfigError(f"'screen_size' in {path} must be a mapping with width/height.")
    try:
        screen_size = ScreenSize(width=screen_size_raw["width"], height=screen_size_raw["height"])
    except KeyError as exc:
        raise BountyConfigError(f"'screen_size' in {path} is missing field {exc}.") from exc
    except InvalidScreenSizeError as exc:
        raise BountyConfigError(f"'screen_size' in {path} is invalid: {exc}") from exc

    templates_dir_raw = raw.get("templates_dir", "templates")
    if not isinstance(templates_dir_raw, str) or not templates_dir_raw.strip():
        raise BountyConfigError(f"'templates_dir' in {path} must be a non-empty string.")

    threshold = raw.get("threshold", 0.8)
    if not isinstance(threshold, (int, float)) or isinstance(threshold, bool) or not (0.0 <= threshold <= 1.0):
        raise BountyConfigError(f"'threshold' in {path} must be a number in [0.0, 1.0].")

    retry_delay_seconds = raw.get("retry_delay_seconds", 0.0)
    if not isinstance(retry_delay_seconds, (int, float)) or isinstance(retry_delay_seconds, bool) or retry_delay_seconds < 0:
        raise BountyConfigError(f"'retry_delay_seconds' in {path} must be a non-negative number.")

    return BountyMissionConfig(
        slot_select_points=slot_select_points,
        mission_phrase_roi=_region(raw, "mission_phrase_roi", path),
        mission_phrase_label=_label(raw, "mission_phrase_label", path),
        mission_quantity_roi=_region(raw, "mission_quantity_roi", path),
        mission_quantity_label=_label(raw, "mission_quantity_label", path),
        refresh_button_point=_point(raw, "refresh_button_point", path),
        refresh_popup_anchor_roi=_region(raw, "refresh_popup_anchor_roi", path),
        refresh_popup_anchor_label=_label(raw, "refresh_popup_anchor_label", path),
        refresh_popup_title_roi=_region(raw, "refresh_popup_title_roi", path),
        refresh_popup_title_label=_label(raw, "refresh_popup_title_label", path),
        refresh_confirm_point=_point(raw, "refresh_confirm_point", path),
        kill_progress_roi=_region(raw, "kill_progress_roi", path),
        kill_progress_complete_label=_label(raw, "kill_progress_complete_label", path),
        complete_state_roi=_region(raw, "complete_state_roi", path),
        complete_state_label=_label(raw, "complete_state_label", path),
        select_complete_point=_point(raw, "select_complete_point", path),
        complete_button_point=_point(raw, "complete_button_point", path),
        reward_screen_roi=_region(raw, "reward_screen_roi", path),
        reward_screen_label=_label(raw, "reward_screen_label", path),
        claim_point=_point(raw, "claim_point", path),
        result_screen_roi=_region(raw, "result_screen_roi", path),
        result_screen_label=_label(raw, "result_screen_label", path),
        close_result_point=_point(raw, "close_result_point", path),
        mission_list_roi=_region(raw, "mission_list_roi", path),
        mission_list_label=_label(raw, "mission_list_label", path),
        screen_size=screen_size,
        templates_dir=Path(templates_dir_raw),
        threshold=float(threshold),
        max_capture_attempts=_positive_int(raw, "max_capture_attempts", 3, path),
        max_refresh_attempts=_positive_int(raw, "max_refresh_attempts", 5, path),
        max_popup_verify_attempts=_positive_int(raw, "max_popup_verify_attempts", 3, path),
        max_kill_progress_poll_attempts=_positive_int(raw, "max_kill_progress_poll_attempts", 10, path),
        max_reward_verify_attempts=_positive_int(raw, "max_reward_verify_attempts", 3, path),
        max_result_verify_attempts=_positive_int(raw, "max_result_verify_attempts", 3, path),
        max_mission_list_verify_attempts=_positive_int(raw, "max_mission_list_verify_attempts", 3, path),
        retry_delay_seconds=float(retry_delay_seconds),
    )


def _point_from_item(item: object, key: str, path: Path) -> RelativeCoordinate:
    if not isinstance(item, dict):
        raise BountyConfigError(f"'{key}' in {path} must be a mapping with x/y.")
    try:
        return RelativeCoordinate(x=item["x"], y=item["y"])
    except KeyError as exc:
        raise BountyConfigError(f"'{key}' in {path} is missing field {exc}.") from exc
    except InvalidCoordinateError as exc:
        raise BountyConfigError(f"'{key}' in {path} is invalid: {exc}") from exc
