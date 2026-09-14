"""GUI-driven ADB mapping registration (UI-ADB-001) + ADB executable
path registration (ADB-PATH-001).

Lets a user register or clear exactly one account's ADB serial at a
time — from the GUI, never by hand-editing YAML/terminal — while
reusing the existing explicit-mapping validation
(:func:`ldmanager.config.validate_adb_mapping`) and never auto-
assigning a discovered device: every value saved here was either typed
by the user or picked by the user from a list the GUI showed them.

As of ADB-PATH-001, this module also lets the user register (via
Browse, or typing a path) or clear the local ``adb.exe`` the app should
use — the exact same ``adb_path`` field :func:`ldmanager.config.load_config`
already reads, just now writable from the GUI instead of only by hand.
A path is only ever persisted after confirming it actually exists as a
file (fail-closed for a typo/missing executable); clearing it always
succeeds and falls back to :func:`ldmanager.adb.resolve_adb_path`'s
normal PATH/common-install-location auto-detection.

This module only reads/writes the local, git-ignored config file. It
never constructs an :class:`~ldmanager.adb.AdbRunner`, never captures a
screenshot, never deletes any file, and never sends an ADB command of
any kind — saving/clearing either the mapping or the ADB path is pure
config file I/O + validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

import yaml

from .adb import validate_serial
from .config import ConfigError, resolve_config_path, validate_adb_mapping
from .models import AccountId


class MappingSaveError(str, Enum):
    BLANK = "blank"
    MALFORMED = "malformed"
    DUPLICATE = "duplicate"
    EXISTING_CONFIG_INVALID = "existing_config_invalid"
    WRITE_FAILED = "write_failed"


class AdbPathSaveError(str, Enum):
    BLANK = "blank"
    NOT_FOUND = "not_found"
    EXISTING_CONFIG_INVALID = "existing_config_invalid"
    WRITE_FAILED = "write_failed"


@dataclass(frozen=True)
class AdbPathSaveResult:
    """Outcome of one save/clear attempt for the configured ADB path.

    ``adb_path`` is the resulting configured value on success (``None``
    after a clear), or ``None`` on failure — a failed save never
    partially applies.
    """

    ok: bool
    error: Optional[AdbPathSaveError]
    detail: str
    adb_path: Optional[str]


@dataclass(frozen=True)
class MappingSaveResult:
    """Outcome of one save/clear attempt for one account.

    ``adb_mapping`` is the resulting full LD1..LD9 mapping on success,
    or the unchanged current mapping (best-effort; empty if it couldn't
    even be read) on failure — never a partially-applied mapping.
    """

    ok: bool
    error: Optional[MappingSaveError]
    detail: str
    adb_mapping: dict


def _load_raw_config(path: Path) -> dict:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    if not isinstance(raw, dict):
        raise ConfigError(f"{path} must contain a YAML mapping at the top level.")
    return raw


def _write_raw_config(path: Path, raw: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(raw, handle, allow_unicode=True, sort_keys=False)


def load_current_adb_mapping(explicit_path: Optional[Path] = None) -> dict:
    """Read the current LD1..LD9 -> serial mapping from disk.

    Returns all nine keys (missing entries as ``None``) even if the
    config file doesn't exist yet or has no ``adb_mapping`` section —
    matching :func:`ldmanager.config.load_config`'s safe-default
    behavior. Raises :class:`~ldmanager.config.ConfigError` if the file
    exists but is malformed (not silently treated as "all unmapped",
    since that could hide a real problem from the user).
    """

    path = resolve_config_path(explicit_path)
    raw = _load_raw_config(path)
    raw_mapping = raw.get("adb_mapping", {})
    if not isinstance(raw_mapping, dict):
        raw_mapping = {}
    return validate_adb_mapping(raw_mapping)


def save_account_serial(
    account_id: AccountId,
    serial: Optional[str],
    explicit_path: Optional[Path] = None,
) -> MappingSaveResult:
    """Save (``serial`` is a non-blank string) or clear (``serial`` is
    ``None``) exactly one account's ADB serial.

    Rejects — without writing anything — a blank/whitespace-only
    string, a malformed serial (whitespace inside it), or a serial
    already assigned to a *different* account. Never touches any other
    account's entry, and preserves every other top-level section of the
    config file (``logging``, ``diagnostics``, ...) byte-for-byte
    structurally (re-serialized, so comments are not preserved — see
    docs/RUN_GUIDE.md).
    """

    path = resolve_config_path(explicit_path)

    try:
        raw = _load_raw_config(path)
    except ConfigError as exc:
        return MappingSaveResult(False, MappingSaveError.WRITE_FAILED, str(exc), {})

    raw_mapping = raw.get("adb_mapping", {})
    if not isinstance(raw_mapping, dict):
        raw_mapping = {}
    try:
        current_mapping = validate_adb_mapping(raw_mapping)
    except ConfigError as exc:
        return MappingSaveResult(
            False, MappingSaveError.EXISTING_CONFIG_INVALID,
            f"Existing config's adb_mapping is invalid, fix it before saving: {exc}",
            {},
        )

    if serial is not None:
        stripped = serial.strip()
        if not stripped:
            return MappingSaveResult(
                False, MappingSaveError.BLANK, "Serial cannot be blank.", current_mapping
            )
        try:
            validate_serial(stripped)
        except ValueError as exc:
            return MappingSaveResult(False, MappingSaveError.MALFORMED, str(exc), current_mapping)

        for other_key, other_serial in current_mapping.items():
            if other_key != account_id.value and other_serial == stripped:
                return MappingSaveResult(
                    False, MappingSaveError.DUPLICATE,
                    f"Serial {stripped!r} is already assigned to {other_key}.",
                    current_mapping,
                )
        new_value: Optional[str] = stripped
    else:
        new_value = None

    updated_mapping = dict(current_mapping)
    updated_mapping[account_id.value] = new_value

    raw["adb_mapping"] = updated_mapping
    try:
        _write_raw_config(path, raw)
    except OSError as exc:
        return MappingSaveResult(False, MappingSaveError.WRITE_FAILED, str(exc), current_mapping)

    return MappingSaveResult(True, None, "Saved." if new_value else "Cleared.", updated_mapping)


def load_current_adb_path(explicit_path: Optional[Path] = None) -> Optional[str]:
    """Read the currently configured ``adb_path`` (may be ``None``,
    meaning "auto-detect" — see :func:`ldmanager.adb.resolve_adb_path`).

    Returns ``None`` (never raises) if the config file doesn't exist yet
    or has no ``adb_path`` key, matching this project's usual
    safe-default behavior. Does **not** validate the value here (that
    happens at ``load_config()``/``save_adb_path()`` time) — this is a
    lightweight read for the GUI to display the currently configured
    value.
    """

    path = resolve_config_path(explicit_path)
    try:
        raw = _load_raw_config(path)
    except ConfigError:
        return None
    value = raw.get("adb_path")
    return value if isinstance(value, str) and value.strip() else None


def save_adb_path(
    path: Optional[str],
    explicit_path: Optional[Path] = None,
) -> AdbPathSaveResult:
    """Save (``path`` is a non-blank string) or clear (``path`` is
    ``None``) the configured ``adb.exe`` path (ADB-PATH-001).

    Fail-closed: a save is rejected — nothing is written — unless
    ``path`` actually exists as a file on disk right now. Clearing
    always succeeds (falls back to auto-detection); this function never
    deletes any file, it only ever writes the ``adb_path`` YAML value.
    Preserves every other top-level section (``adb_mapping``,
    ``logging``, ``diagnostics``, ...) exactly as read.
    """

    config_path = resolve_config_path(explicit_path)

    try:
        raw = _load_raw_config(config_path)
    except ConfigError as exc:
        return AdbPathSaveResult(False, AdbPathSaveError.EXISTING_CONFIG_INVALID, str(exc), None)

    if path is not None:
        stripped = path.strip()
        if not stripped:
            return AdbPathSaveResult(False, AdbPathSaveError.BLANK, "Path cannot be blank.", None)
        if not Path(stripped).is_file():
            return AdbPathSaveResult(
                False, AdbPathSaveError.NOT_FOUND, f"File not found: {stripped}", None
            )
        new_value: Optional[str] = stripped
    else:
        new_value = None

    raw["adb_path"] = new_value
    try:
        _write_raw_config(config_path, raw)
    except OSError as exc:
        return AdbPathSaveResult(False, AdbPathSaveError.WRITE_FAILED, str(exc), None)

    return AdbPathSaveResult(True, None, "Saved." if new_value else "Cleared.", new_value)
