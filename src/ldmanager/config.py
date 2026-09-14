"""Configuration loading skeleton (TP-001 stage 1-2).

Responsibilities:
  * Resolve *where* a config file should be read from.
  * Load and validate its shape, including the stage 2 ``logging`` and
    ``diagnostics`` sections.
  * Refuse to load a config file that contains anything that looks like
    a credential/secret field — this project never stores or logs
    credentials, so such a file is rejected outright rather than
    partially accepted.
  * Expose an ``AppConfig`` with an ``adb_mapping`` placeholder for
    LD1~LD9.

Explicitly out of scope: guessing or hardcoding any ADB host/port,
connecting to ADB, or talking to LDPlayer in any way. Every mapping
value defaults to ``None`` until a human fills it in.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from .diagnostics import DEFAULT_SCREENSHOT_DIR, DiagnosticsSettings
from .logs import (
    DEFAULT_BACKUP_COUNT,
    DEFAULT_MAX_BYTES,
    DEFAULT_RETENTION_DAYS,
    DEFAULT_ROOT_DIR,
    LoggingSettings,
)
from .models import AccountId

#: Environment variable that, when set, overrides the config file path.
CONFIG_PATH_ENV_VAR = "LDMANAGER_CONFIG"

#: Default location, relative to the current working directory, used when
#: no explicit path and no environment override are given.
DEFAULT_CONFIG_RELPATH = Path("configs") / "config.yaml"

#: Key names (matched case-insensitively, anywhere in the config tree)
#: that make ldmanager refuse to load the file. This project never
#: stores credentials in config.yaml, so such a field is a hard error
#: rather than something that gets silently stripped or accepted.
_SENSITIVE_KEY_RE = re.compile(
    r"(password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|"
    r"private[_-]?key|credential|auth(?:orization)?|session[_-]?key|cookie)",
    re.IGNORECASE,
)

_KNOWN_TOP_LEVEL_KEYS = {"adb_mapping", "adb_path", "logging", "diagnostics"}
_KNOWN_LOGGING_KEYS = {"root_dir", "retention_days", "max_bytes", "backup_count"}
_KNOWN_DIAGNOSTICS_KEYS = {"screenshot_dir"}


class ConfigError(Exception):
    """Raised for missing, malformed, or unsafe configuration."""


@dataclass
class AppConfig:
    """Root application configuration.

    ``adb_mapping`` maps each :class:`~ldmanager.models.AccountId` value
    (as a string, e.g. ``"LD1"``) to an ADB serial such as
    ``"127.0.0.1:5555"``, or ``None`` while unset — never guessed.
    ``logging`` and ``diagnostics`` hold the stage 2 log rotation/
    retention policy and diagnostic-screenshot path settings.
    """

    adb_mapping: dict[str, Optional[str]] = field(default_factory=dict)
    adb_path: Optional[str] = None
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    diagnostics: DiagnosticsSettings = field(default_factory=DiagnosticsSettings)

    def adb_serial_for(self, account_id: AccountId) -> Optional[str]:
        """Return the configured ADB serial for an account, or ``None``."""

        return self.adb_mapping.get(account_id.value)


def default_config_path() -> Path:
    """Return the config path that would be used with no explicit override."""

    return Path.cwd() / DEFAULT_CONFIG_RELPATH


def resolve_config_path(explicit_path: Optional[Path] = None) -> Path:
    """Resolve the config file path with a clear, predictable precedence.

    Order: explicit argument > ``LDMANAGER_CONFIG`` env var > default
    ``configs/config.yaml`` under the current working directory.
    """

    if explicit_path is not None:
        return Path(explicit_path)

    env_value = os.environ.get(CONFIG_PATH_ENV_VAR)
    if env_value:
        return Path(env_value)

    return default_config_path()


def _empty_adb_mapping() -> dict[str, Optional[str]]:
    """A placeholder mapping with every LD1~LD9 slot set to ``None``."""

    return {account_id.value: None for account_id in AccountId}


def validate_adb_mapping(raw_mapping: dict) -> dict[str, Optional[str]]:
    """Validate a raw ``adb_mapping`` dict loaded from YAML.

    * Unknown keys (not one of LD1~LD9) raise :class:`ConfigError`.
    * Missing keys are filled in as ``None`` (safe default, never guessed).
    * Non-null values must be non-empty strings; anything else raises.
    """

    known_keys = {account_id.value for account_id in AccountId}
    unknown_keys = set(raw_mapping) - known_keys
    if unknown_keys:
        raise ConfigError(
            "Unknown adb_mapping key(s): "
            f"{sorted(unknown_keys)}. Expected only {sorted(known_keys)}."
        )

    mapping = _empty_adb_mapping()
    for key, value in raw_mapping.items():
        if value is None:
            mapping[key] = None
        elif isinstance(value, str) and value.strip():
            mapping[key] = value
        else:
            raise ConfigError(
                f"adb_mapping['{key}'] must be a non-empty string or null, "
                f"got {value!r}."
            )
    return mapping


def _find_sensitive_keys(obj: object, prefix: str = "") -> list[str]:
    """Recursively collect dotted paths of keys that look sensitive."""

    found: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(key, str) and _SENSITIVE_KEY_RE.search(key):
                found.append(path)
            found.extend(_find_sensitive_keys(value, path))
    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            found.extend(_find_sensitive_keys(item, f"{prefix}[{index}]"))
    return found


def _validate_logging_section(raw: Optional[dict]) -> LoggingSettings:
    if raw is None:
        return LoggingSettings()
    if not isinstance(raw, dict):
        raise ConfigError("'logging' section must be a mapping.")

    unknown = set(raw) - _KNOWN_LOGGING_KEYS
    if unknown:
        raise ConfigError(f"Unknown 'logging' option(s): {sorted(unknown)}")

    root_dir = raw.get("root_dir", str(DEFAULT_ROOT_DIR))
    if not isinstance(root_dir, str) or not root_dir.strip():
        raise ConfigError("'logging.root_dir' must be a non-empty string.")

    retention_days = raw.get("retention_days", DEFAULT_RETENTION_DAYS)
    if not isinstance(retention_days, int) or isinstance(retention_days, bool) or retention_days < 1:
        raise ConfigError("'logging.retention_days' must be a positive integer.")

    max_bytes = raw.get("max_bytes", DEFAULT_MAX_BYTES)
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes < 1024:
        raise ConfigError("'logging.max_bytes' must be an integer >= 1024.")

    backup_count = raw.get("backup_count", DEFAULT_BACKUP_COUNT)
    if not isinstance(backup_count, int) or isinstance(backup_count, bool) or backup_count < 0:
        raise ConfigError("'logging.backup_count' must be a non-negative integer.")

    return LoggingSettings(
        root_dir=Path(root_dir),
        retention_days=retention_days,
        max_bytes=max_bytes,
        backup_count=backup_count,
    )


def _validate_diagnostics_section(raw: Optional[dict]) -> DiagnosticsSettings:
    if raw is None:
        return DiagnosticsSettings()
    if not isinstance(raw, dict):
        raise ConfigError("'diagnostics' section must be a mapping.")

    unknown = set(raw) - _KNOWN_DIAGNOSTICS_KEYS
    if unknown:
        raise ConfigError(f"Unknown 'diagnostics' option(s): {sorted(unknown)}")

    screenshot_dir = raw.get("screenshot_dir", str(DEFAULT_SCREENSHOT_DIR))
    if not isinstance(screenshot_dir, str) or not screenshot_dir.strip():
        raise ConfigError("'diagnostics.screenshot_dir' must be a non-empty string.")

    return DiagnosticsSettings(screenshot_dir=Path(screenshot_dir))


def _validate_adb_path(raw: object) -> Optional[str]:
    if raw is None:
        return None
    if not isinstance(raw, str) or not raw.strip():
        raise ConfigError("'adb_path' must be a non-empty executable path or null.")
    return raw.strip()


def load_config(explicit_path: Optional[Path] = None) -> AppConfig:
    """Load :class:`AppConfig` from disk.

    Fails loudly (no silent fallback, no guessed values) when the file is
    missing, malformed, or contains a field that looks like a credential
    — a wrong ADB target, or a leaked secret, must never pass silently.
    """

    path = resolve_config_path(explicit_path)
    if not path.is_file():
        raise ConfigError(
            f"Config file not found: {path}. Copy configs/config.example.yaml "
            "to configs/config.yaml (or set LDMANAGER_CONFIG) and fill in "
            "your own adb_mapping values before running again."
        )

    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    if not isinstance(raw, dict):
        raise ConfigError(f"Config file {path} must contain a YAML mapping at the top level.")

    sensitive_keys = _find_sensitive_keys(raw)
    if sensitive_keys:
        raise ConfigError(
            f"Refusing to load {path}: sensitive-looking field(s) found "
            f"{sensitive_keys}. ldmanager never stores credentials in "
            "config.yaml — remove them (use a dedicated secret store instead)."
        )

    unknown_top = set(raw) - _KNOWN_TOP_LEVEL_KEYS
    if unknown_top:
        raise ConfigError(f"Unknown top-level config key(s): {sorted(unknown_top)}")

    raw_adb_mapping = raw.get("adb_mapping", {})
    if not isinstance(raw_adb_mapping, dict):
        raise ConfigError(f"'adb_mapping' in {path} must be a mapping of LD1..LD9 to values.")

    adb_mapping = validate_adb_mapping(raw_adb_mapping)
    logging_settings = _validate_logging_section(raw.get("logging"))
    diagnostics_settings = _validate_diagnostics_section(raw.get("diagnostics"))

    return AppConfig(
        adb_mapping=adb_mapping,
        adb_path=_validate_adb_path(raw.get("adb_path")),
        logging=logging_settings,
        diagnostics=diagnostics_settings,
    )
