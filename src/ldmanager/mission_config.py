"""Mission-cycle configuration loading (MVP-001).

Kept separate from :mod:`ldmanager.config` (which owns
``adb_mapping``/``logging``/``diagnostics``) so this MVP's mission-cycle
knobs — ROIs, touch points, recognition threshold, retry/timeout
bounds, template directory — can evolve without touching the
already-stable core config loader. Same safety posture throughout the
project: nothing here is guessed, every value is explicitly validated,
and no credential ever belongs in this file.
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

MISSION_CONFIG_PATH_ENV_VAR = "LDMANAGER_MISSION_CONFIG"
DEFAULT_MISSION_CONFIG_RELPATH = Path("configs") / "mission.yaml"

DEFAULT_SLOT_COUNT = 5


class MissionConfigError(Exception):
    """Raised for missing or malformed mission configuration."""


@dataclass(frozen=True)
class MissionConfig:
    """Everything the mission-cycle state machine needs, fully
    explicit and validated — no path/ROI/coordinate/threshold/retry or
    timeout value is ever inferred or hardcoded by the state machine
    itself."""

    target_label: str
    slot_rois: tuple[RelativeRegion, ...]
    reroll_point: RelativeCoordinate
    kill_check_roi: RelativeRegion
    kill_check_label: str
    claim_point: RelativeCoordinate
    claimed_roi: RelativeRegion
    claimed_label: str
    reset_point: RelativeCoordinate
    ready_roi: RelativeRegion
    ready_label: str
    screen_size: ScreenSize
    templates_dir: Path
    threshold: float = 0.8
    max_capture_attempts: int = 3
    max_reroll_attempts: int = 5
    max_kill_check_attempts: int = 10
    max_claim_verify_attempts: int = 3
    max_reset_verify_attempts: int = 3
    retry_delay_seconds: float = 0.0
    capture_args: tuple[str, ...] = DEFAULT_CAPTURE_ARGS

    @property
    def slot_count(self) -> int:
        return len(self.slot_rois)


def default_mission_config_path() -> Path:
    return Path.cwd() / DEFAULT_MISSION_CONFIG_RELPATH


def resolve_mission_config_path(explicit_path: Optional[Path] = None) -> Path:
    if explicit_path is not None:
        return Path(explicit_path)
    env_value = os.environ.get(MISSION_CONFIG_PATH_ENV_VAR)
    if env_value:
        return Path(env_value)
    return default_mission_config_path()


def _require(raw: dict, key: str, path: Path) -> object:
    if key not in raw:
        raise MissionConfigError(f"Missing required key '{key}' in {path}.")
    return raw[key]


def _region_from_raw(raw: object, key: str, path: Path) -> RelativeRegion:
    if not isinstance(raw, dict):
        raise MissionConfigError(f"'{key}' in {path} must be a mapping with x/y/width/height.")
    try:
        return RelativeRegion(
            x=raw["x"], y=raw["y"], width=raw["width"], height=raw["height"]
        )
    except KeyError as exc:
        raise MissionConfigError(f"'{key}' in {path} is missing field {exc}.") from exc
    except InvalidCoordinateError as exc:
        raise MissionConfigError(f"'{key}' in {path} is invalid: {exc}") from exc


def _point_from_raw(raw: object, key: str, path: Path) -> RelativeCoordinate:
    if not isinstance(raw, dict):
        raise MissionConfigError(f"'{key}' in {path} must be a mapping with x/y.")
    try:
        return RelativeCoordinate(x=raw["x"], y=raw["y"])
    except KeyError as exc:
        raise MissionConfigError(f"'{key}' in {path} is missing field {exc}.") from exc
    except InvalidCoordinateError as exc:
        raise MissionConfigError(f"'{key}' in {path} is invalid: {exc}") from exc


def _positive_int(raw: dict, key: str, default: int, path: Path) -> int:
    value = raw.get(key, default)
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise MissionConfigError(f"'{key}' in {path} must be a positive integer, got {value!r}.")
    return value


def load_mission_config(explicit_path: Optional[Path] = None) -> MissionConfig:
    """Load and validate a :class:`MissionConfig` from YAML.

    Fails loudly (no silent fallback, no guessed ROI/coordinate) when
    the file is missing or malformed.
    """

    path = resolve_mission_config_path(explicit_path)
    if not path.is_file():
        raise MissionConfigError(
            f"Mission config file not found: {path}. Copy "
            "configs/mission.example.yaml to configs/mission.yaml (or set "
            f"{MISSION_CONFIG_PATH_ENV_VAR}) and fill in your own ROIs/"
            "coordinates before running again."
        )

    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    if not isinstance(raw, dict):
        raise MissionConfigError(f"{path} must contain a YAML mapping at the top level.")

    slot_rois_raw = _require(raw, "slot_rois", path)
    if not isinstance(slot_rois_raw, list) or not slot_rois_raw:
        raise MissionConfigError(f"'slot_rois' in {path} must be a non-empty list.")
    slot_rois = tuple(
        _region_from_raw(item, f"slot_rois[{i}]", path) for i, item in enumerate(slot_rois_raw)
    )

    screen_size_raw = _require(raw, "screen_size", path)
    if not isinstance(screen_size_raw, dict):
        raise MissionConfigError(f"'screen_size' in {path} must be a mapping with width/height.")
    try:
        screen_size = ScreenSize(
            width=screen_size_raw["width"], height=screen_size_raw["height"]
        )
    except KeyError as exc:
        raise MissionConfigError(f"'screen_size' in {path} is missing field {exc}.") from exc
    except InvalidScreenSizeError as exc:
        raise MissionConfigError(f"'screen_size' in {path} is invalid: {exc}") from exc

    templates_dir_raw = raw.get("templates_dir", "templates")
    if not isinstance(templates_dir_raw, str) or not templates_dir_raw.strip():
        raise MissionConfigError(f"'templates_dir' in {path} must be a non-empty string.")

    threshold = raw.get("threshold", 0.8)
    if not isinstance(threshold, (int, float)) or isinstance(threshold, bool) or not (0.0 <= threshold <= 1.0):
        raise MissionConfigError(f"'threshold' in {path} must be a number in [0.0, 1.0].")

    retry_delay_seconds = raw.get("retry_delay_seconds", 0.0)
    if not isinstance(retry_delay_seconds, (int, float)) or isinstance(retry_delay_seconds, bool) or retry_delay_seconds < 0:
        raise MissionConfigError(f"'retry_delay_seconds' in {path} must be a non-negative number.")

    target_label = _require(raw, "target_label", path)
    if not isinstance(target_label, str) or not target_label.strip():
        raise MissionConfigError(f"'target_label' in {path} must be a non-empty string.")

    kill_check_label = raw.get("kill_check_label", "200/200")
    claimed_label = raw.get("claimed_label", "claimed")
    ready_label = raw.get("ready_label", "ready")
    for label_name, label_value in (
        ("kill_check_label", kill_check_label),
        ("claimed_label", claimed_label),
        ("ready_label", ready_label),
    ):
        if not isinstance(label_value, str) or not label_value.strip():
            raise MissionConfigError(f"'{label_name}' in {path} must be a non-empty string.")

    return MissionConfig(
        target_label=target_label,
        slot_rois=slot_rois,
        reroll_point=_point_from_raw(_require(raw, "reroll_point", path), "reroll_point", path),
        kill_check_roi=_region_from_raw(_require(raw, "kill_check_roi", path), "kill_check_roi", path),
        kill_check_label=kill_check_label,
        claim_point=_point_from_raw(_require(raw, "claim_point", path), "claim_point", path),
        claimed_roi=_region_from_raw(_require(raw, "claimed_roi", path), "claimed_roi", path),
        claimed_label=claimed_label,
        reset_point=_point_from_raw(_require(raw, "reset_point", path), "reset_point", path),
        ready_roi=_region_from_raw(_require(raw, "ready_roi", path), "ready_roi", path),
        ready_label=ready_label,
        screen_size=screen_size,
        templates_dir=Path(templates_dir_raw),
        threshold=float(threshold),
        max_capture_attempts=_positive_int(raw, "max_capture_attempts", 3, path),
        max_reroll_attempts=_positive_int(raw, "max_reroll_attempts", 5, path),
        max_kill_check_attempts=_positive_int(raw, "max_kill_check_attempts", 10, path),
        max_claim_verify_attempts=_positive_int(raw, "max_claim_verify_attempts", 3, path),
        max_reset_verify_attempts=_positive_int(raw, "max_reset_verify_attempts", 3, path),
        retry_delay_seconds=float(retry_delay_seconds),
    )
