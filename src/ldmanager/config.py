"""Configuration loading skeleton (TP-001 stage 1).

Responsibilities in this stage:
  * Resolve *where* a config file should be read from.
  * Load and lightly validate its shape.
  * Expose an ``AppConfig`` with an ``adb_mapping`` placeholder for
    LD1~LD9.

Explicitly out of scope for this stage: guessing or hardcoding any ADB
host/port, connecting to ADB, or talking to LDPlayer in any way. Every
mapping value defaults to ``None`` until a human fills it in.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from .models import AccountId

#: Environment variable that, when set, overrides the config file path.
CONFIG_PATH_ENV_VAR = "LDMANAGER_CONFIG"

#: Default location, relative to the current working directory, used when
#: no explicit path and no environment override are given.
DEFAULT_CONFIG_RELPATH = Path("configs") / "config.yaml"


class ConfigError(Exception):
    """Raised for missing or malformed configuration."""


@dataclass
class AppConfig:
    """Root application configuration.

    ``adb_mapping`` maps each :class:`~ldmanager.models.AccountId` value
    (as a string, e.g. ``"LD1"``) to an ADB serial such as
    ``"127.0.0.1:5555"``, or ``None`` while unset. Stage 1 never invents
    a value for a missing entry.
    """

    adb_mapping: dict[str, Optional[str]] = field(default_factory=dict)

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


def load_config(explicit_path: Optional[Path] = None) -> AppConfig:
    """Load :class:`AppConfig` from disk.

    Fails loudly (no silent fallback, no guessed values) when the file is
    missing or malformed, since a wrong ADB target could hit the wrong
    account.
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

    raw_adb_mapping = raw.get("adb_mapping", {})
    if not isinstance(raw_adb_mapping, dict):
        raise ConfigError(f"'adb_mapping' in {path} must be a mapping of LD1..LD9 to values.")

    adb_mapping = validate_adb_mapping(raw_adb_mapping)
    return AppConfig(adb_mapping=adb_mapping)
