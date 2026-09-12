"""Tests for first-run config bootstrap (REL-0.1.0-PKG-01).

No GUI, no ADB, no PyInstaller involved -- pure filesystem behavior
against a throwaway tmp_path, never the real repo config.
"""

import shutil
from pathlib import Path

import yaml

from ldmanager.bootstrap import app_base_dir, bootstrap_default_configs
from ldmanager.config import load_config
from ldmanager.models import AccountId

_EXAMPLE_CONFIG = (
    Path(__file__).resolve().parents[1] / "configs" / "config.example.yaml"
)
_EXAMPLE_BOUNTY = (
    Path(__file__).resolve().parents[1] / "configs" / "bounty.example.yaml"
)


def _prepare_fake_app_dir(base: Path) -> None:
    """Mimic what scripts/build_windows.ps1 places next to the exe:
    configs/*.example.yaml, no real config yet."""

    configs_dir = base / "configs"
    configs_dir.mkdir(parents=True, exist_ok=True)
    # Binary copy -- no newline translation -- so byte-identity checks
    # against the real repo example files stay meaningful.
    shutil.copyfile(_EXAMPLE_CONFIG, configs_dir / "config.example.yaml")
    shutil.copyfile(_EXAMPLE_BOUNTY, configs_dir / "bounty.example.yaml")


# --- app_base_dir --------------------------------------------------------


def test_app_base_dir_is_cwd_when_unfrozen(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delattr("sys.frozen", raising=False)
    assert app_base_dir() == tmp_path


def test_app_base_dir_is_executable_dir_when_frozen(tmp_path, monkeypatch):
    fake_exe = tmp_path / "somewhere" / "ldmanager.exe"
    fake_exe.parent.mkdir(parents=True)
    fake_exe.write_bytes(b"")
    monkeypatch.setattr("sys.frozen", True, raising=False)
    monkeypatch.setattr("sys.executable", str(fake_exe))
    try:
        assert app_base_dir() == fake_exe.resolve().parent
    finally:
        monkeypatch.delattr("sys.frozen", raising=False)


# --- bootstrap_default_configs: creates when missing ----------------------


def test_bootstrap_creates_both_configs_from_examples(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LDMANAGER_CONFIG", raising=False)
    monkeypatch.delenv("LDMANAGER_BOUNTY_CONFIG", raising=False)
    _prepare_fake_app_dir(tmp_path)

    messages = bootstrap_default_configs()

    assert (tmp_path / "configs" / "config.yaml").is_file()
    assert (tmp_path / "configs" / "bounty.yaml").is_file()
    assert len(messages) == 2


def test_bootstrapped_config_has_all_null_adb_mapping(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LDMANAGER_CONFIG", raising=False)
    _prepare_fake_app_dir(tmp_path)

    bootstrap_default_configs()

    raw = yaml.safe_load((tmp_path / "configs" / "config.yaml").read_text(encoding="utf-8"))
    mapping = raw["adb_mapping"]
    assert set(mapping.keys()) == {a.value for a in AccountId}
    assert all(value is None for value in mapping.values())


def test_bootstrapped_config_contains_no_sensitive_looking_key(tmp_path, monkeypatch):
    # Uses the real config.py sensitive-key scanner (the authoritative
    # check, structural -- not a naive text/comment substring search)
    # by simply loading the bootstrapped file: load_config() raises
    # ConfigError if it finds anything credential-shaped.
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LDMANAGER_CONFIG", raising=False)
    _prepare_fake_app_dir(tmp_path)

    bootstrap_default_configs()

    config = load_config(tmp_path / "configs" / "config.yaml")
    assert all(value is None for value in config.adb_mapping.values())


def test_bootstrapped_configs_are_byte_identical_to_examples(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LDMANAGER_CONFIG", raising=False)
    monkeypatch.delenv("LDMANAGER_BOUNTY_CONFIG", raising=False)
    _prepare_fake_app_dir(tmp_path)

    bootstrap_default_configs()

    assert (tmp_path / "configs" / "config.yaml").read_bytes() == _EXAMPLE_CONFIG.read_bytes()
    assert (tmp_path / "configs" / "bounty.yaml").read_bytes() == _EXAMPLE_BOUNTY.read_bytes()


# --- never overwrites an existing config ----------------------------------


def test_bootstrap_never_overwrites_an_existing_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LDMANAGER_CONFIG", raising=False)
    _prepare_fake_app_dir(tmp_path)

    existing_path = tmp_path / "configs" / "config.yaml"
    existing_path.write_text("adb_mapping:\n  LD1: my-real-serial\n", encoding="utf-8")

    messages = bootstrap_default_configs()

    assert existing_path.read_text(encoding="utf-8") == "adb_mapping:\n  LD1: my-real-serial\n"
    assert not any("config.yaml" in m and "bounty" not in m for m in messages)


def test_bootstrap_never_overwrites_an_existing_bounty_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LDMANAGER_BOUNTY_CONFIG", raising=False)
    _prepare_fake_app_dir(tmp_path)

    existing_path = tmp_path / "configs" / "bounty.yaml"
    existing_path.write_text("# my custom bounty config\n", encoding="utf-8")

    bootstrap_default_configs()

    assert existing_path.read_text(encoding="utf-8") == "# my custom bounty config\n"


def test_bootstrap_leaves_config_untouched_when_only_bounty_is_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LDMANAGER_CONFIG", raising=False)
    monkeypatch.delenv("LDMANAGER_BOUNTY_CONFIG", raising=False)
    _prepare_fake_app_dir(tmp_path)

    config_path = tmp_path / "configs" / "config.yaml"
    config_path.write_text("adb_mapping:\n  LD1: kept-value\n", encoding="utf-8")

    bootstrap_default_configs()

    assert config_path.read_text(encoding="utf-8") == "adb_mapping:\n  LD1: kept-value\n"
    assert (tmp_path / "configs" / "bounty.yaml").is_file()


# --- graceful no-op when no example is bundled -----------------------------


def test_bootstrap_is_a_safe_noop_when_no_example_files_present(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LDMANAGER_CONFIG", raising=False)
    monkeypatch.delenv("LDMANAGER_BOUNTY_CONFIG", raising=False)
    # No configs/ directory at all -- nothing bundled, nothing to do.

    messages = bootstrap_default_configs()

    assert messages == []
    assert not (tmp_path / "configs" / "config.yaml").exists()
    assert not (tmp_path / "configs" / "bounty.yaml").exists()


def test_bootstrap_returns_empty_when_both_already_exist(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LDMANAGER_CONFIG", raising=False)
    monkeypatch.delenv("LDMANAGER_BOUNTY_CONFIG", raising=False)
    _prepare_fake_app_dir(tmp_path)
    bootstrap_default_configs()  # first run: creates both

    messages_second_run = bootstrap_default_configs()

    assert messages_second_run == []
