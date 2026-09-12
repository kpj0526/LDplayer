from pathlib import Path

import pytest

from ldmanager.config import (
    ConfigError,
    DEFAULT_CONFIG_RELPATH,
    load_config,
    resolve_config_path,
    validate_adb_mapping,
)
from ldmanager.models import AccountId

EXAMPLE_CONFIG = Path(__file__).resolve().parents[1] / "configs" / "config.example.yaml"


def test_resolve_config_path_explicit_wins(tmp_path):
    explicit = tmp_path / "explicit.yaml"
    assert resolve_config_path(explicit) == explicit


def test_resolve_config_path_env_var(monkeypatch, tmp_path):
    env_path = tmp_path / "from_env.yaml"
    monkeypatch.setenv("LDMANAGER_CONFIG", str(env_path))
    assert resolve_config_path() == env_path


def test_resolve_config_path_default(monkeypatch, tmp_path):
    monkeypatch.delenv("LDMANAGER_CONFIG", raising=False)
    monkeypatch.chdir(tmp_path)
    assert resolve_config_path() == tmp_path / DEFAULT_CONFIG_RELPATH


def test_missing_config_file_raises_clear_error(tmp_path):
    missing = tmp_path / "does_not_exist.yaml"
    with pytest.raises(ConfigError):
        load_config(missing)


def test_example_config_loads_with_all_placeholders_none():
    config = load_config(EXAMPLE_CONFIG)
    assert set(config.adb_mapping.keys()) == {a.value for a in AccountId}
    assert all(value is None for value in config.adb_mapping.values())
    for account_id in AccountId:
        assert config.adb_serial_for(account_id) is None


def test_validate_adb_mapping_rejects_unknown_key():
    with pytest.raises(ConfigError):
        validate_adb_mapping({"LD10": None})


def test_validate_adb_mapping_rejects_bad_value_type():
    with pytest.raises(ConfigError):
        validate_adb_mapping({"LD1": 5555})


def test_validate_adb_mapping_fills_missing_keys_as_none():
    mapping = validate_adb_mapping({"LD1": "127.0.0.1:5555"})
    assert mapping["LD1"] == "127.0.0.1:5555"
    assert mapping["LD2"] is None
