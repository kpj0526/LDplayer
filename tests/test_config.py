from pathlib import Path

import pytest

from ldmanager.config import (
    ConfigError,
    DEFAULT_CONFIG_RELPATH,
    load_config,
    resolve_config_path,
    validate_adb_mapping,
)
from ldmanager.diagnostics import DEFAULT_SCREENSHOT_DIR
from ldmanager.logs import (
    DEFAULT_BACKUP_COUNT,
    DEFAULT_MAX_BYTES,
    DEFAULT_RETENTION_DAYS,
    DEFAULT_ROOT_DIR,
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


def test_example_config_logging_and_diagnostics_match_documented_defaults():
    config = load_config(EXAMPLE_CONFIG)
    assert config.logging.root_dir == Path(DEFAULT_ROOT_DIR)
    assert config.logging.retention_days == DEFAULT_RETENTION_DAYS
    assert config.logging.max_bytes == DEFAULT_MAX_BYTES
    assert config.logging.backup_count == DEFAULT_BACKUP_COUNT
    assert config.diagnostics.screenshot_dir == Path(DEFAULT_SCREENSHOT_DIR)


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


def test_load_config_defaults_logging_and_diagnostics_when_sections_omitted(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("adb_mapping: {}\n", encoding="utf-8")

    config = load_config(path)

    assert config.logging.root_dir == Path(DEFAULT_ROOT_DIR)
    assert config.logging.retention_days == DEFAULT_RETENTION_DAYS
    assert config.diagnostics.screenshot_dir == Path(DEFAULT_SCREENSHOT_DIR)


def test_load_config_rejects_top_level_sensitive_key(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("adb_mapping: {}\npassword: hunter2\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(path)


def test_load_config_rejects_nested_sensitive_key(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text(
        "adb_mapping: {}\nlogging:\n  root_dir: logs\n  api_token: abc\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError):
        load_config(path)


def test_load_config_rejects_unknown_top_level_key(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("adb_mapping: {}\nfoo: bar\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(path)


def test_load_config_rejects_unknown_logging_key(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("adb_mapping: {}\nlogging:\n  bogus: 1\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(path)


@pytest.mark.parametrize(
    "logging_yaml",
    [
        "retention_days: 0\n",
        "retention_days: -1\n",
        "max_bytes: 100\n",
        "backup_count: -1\n",
        "root_dir: ''\n",
    ],
)
def test_load_config_rejects_bad_logging_values(tmp_path, logging_yaml):
    path = tmp_path / "config.yaml"
    indented = "".join(f"  {line}\n" for line in logging_yaml.strip().splitlines())
    path.write_text(f"adb_mapping: {{}}\nlogging:\n{indented}", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(path)


def test_load_config_rejects_unknown_diagnostics_key(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("adb_mapping: {}\ndiagnostics:\n  bogus: 1\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(path)


def test_load_config_accepts_custom_diagnostics_dir(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text(
        "adb_mapping: {}\ndiagnostics:\n  screenshot_dir: my_shots\n",
        encoding="utf-8",
    )
    config = load_config(path)
    assert config.diagnostics.screenshot_dir == Path("my_shots")
