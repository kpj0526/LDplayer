"""Tests for GUI-driven ADB mapping registration (UI-ADB-001).

No GUI, no ADB runner involved -- pure config file I/O + validation.
"""

from pathlib import Path

import yaml

from ldmanager.config_mapping import (
    AdbPathSaveError,
    MappingSaveError,
    load_current_adb_mapping,
    load_current_adb_path,
    save_account_serial,
    save_adb_path,
)
from ldmanager.models import AccountId


def _config_path(tmp_path: Path) -> Path:
    return tmp_path / "config.yaml"


# --- load_current_adb_mapping -----------------------------------------


def test_load_current_mapping_defaults_all_none_when_file_missing(tmp_path):
    mapping = load_current_adb_mapping(_config_path(tmp_path))
    assert mapping == {f"LD{i}": None for i in range(1, 10)}


def test_load_current_mapping_reads_existing_values(tmp_path):
    path = _config_path(tmp_path)
    path.write_text("adb_mapping:\n  LD1: 127.0.0.1:5555\n", encoding="utf-8")
    mapping = load_current_adb_mapping(path)
    assert mapping["LD1"] == "127.0.0.1:5555"
    assert mapping["LD2"] is None


# --- save: creates a new file when none exists -------------------------


def test_save_creates_config_file_when_missing(tmp_path):
    path = _config_path(tmp_path)
    assert not path.exists()

    result = save_account_serial(AccountId.LD1, "127.0.0.1:5555", path)

    assert result.ok is True
    assert path.is_file()
    assert result.adb_mapping["LD1"] == "127.0.0.1:5555"
    assert result.adb_mapping["LD2"] is None


def test_save_persists_and_reload_reflects_it(tmp_path):
    path = _config_path(tmp_path)
    result = save_account_serial(AccountId.LD3, "emulator-5556", path)
    assert result.ok is True

    reloaded = load_current_adb_mapping(path)
    assert reloaded["LD3"] == "emulator-5556"


# --- save: rejects blank / malformed / duplicate ------------------------


def test_save_rejects_blank_serial(tmp_path):
    path = _config_path(tmp_path)
    result = save_account_serial(AccountId.LD1, "", path)
    assert result.ok is False
    assert result.error is MappingSaveError.BLANK
    assert not path.exists()  # nothing written


def test_save_rejects_whitespace_only_serial(tmp_path):
    path = _config_path(tmp_path)
    result = save_account_serial(AccountId.LD1, "   ", path)
    assert result.ok is False
    assert result.error is MappingSaveError.BLANK


def test_save_rejects_malformed_serial_with_internal_whitespace(tmp_path):
    path = _config_path(tmp_path)
    result = save_account_serial(AccountId.LD1, "127.0.0.1 5555", path)
    assert result.ok is False
    assert result.error is MappingSaveError.MALFORMED
    assert not path.exists()


def test_save_rejects_duplicate_serial_across_accounts(tmp_path):
    path = _config_path(tmp_path)
    first = save_account_serial(AccountId.LD1, "127.0.0.1:5555", path)
    assert first.ok is True

    second = save_account_serial(AccountId.LD2, "127.0.0.1:5555", path)
    assert second.ok is False
    assert second.error is MappingSaveError.DUPLICATE
    # LD2 must not have been written.
    reloaded = load_current_adb_mapping(path)
    assert reloaded["LD2"] is None
    assert reloaded["LD1"] == "127.0.0.1:5555"


def test_save_same_serial_to_same_account_again_is_not_a_duplicate(tmp_path):
    path = _config_path(tmp_path)
    save_account_serial(AccountId.LD1, "127.0.0.1:5555", path)
    result = save_account_serial(AccountId.LD1, "127.0.0.1:5555", path)
    assert result.ok is True


# --- save: preserves other accounts' mappings and other config sections -


def test_save_preserves_other_accounts_mappings(tmp_path):
    path = _config_path(tmp_path)
    save_account_serial(AccountId.LD1, "serial-1", path)
    save_account_serial(AccountId.LD2, "serial-2", path)
    save_account_serial(AccountId.LD3, "serial-3", path)

    # Updating LD2 must not disturb LD1/LD3.
    result = save_account_serial(AccountId.LD2, "serial-2-updated", path)
    assert result.ok is True
    assert result.adb_mapping["LD1"] == "serial-1"
    assert result.adb_mapping["LD2"] == "serial-2-updated"
    assert result.adb_mapping["LD3"] == "serial-3"


def test_save_preserves_unrelated_top_level_sections(tmp_path):
    path = _config_path(tmp_path)
    path.write_text(
        "adb_mapping:\n  LD1: null\n"
        "logging:\n  retention_days: 30\n",
        encoding="utf-8",
    )

    result = save_account_serial(AccountId.LD1, "127.0.0.1:5555", path)
    assert result.ok is True

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert raw["logging"]["retention_days"] == 30
    assert raw["adb_mapping"]["LD1"] == "127.0.0.1:5555"


# --- clear (serial=None) -------------------------------------------------


def test_clear_removes_a_previously_saved_serial(tmp_path):
    path = _config_path(tmp_path)
    save_account_serial(AccountId.LD1, "127.0.0.1:5555", path)

    result = save_account_serial(AccountId.LD1, None, path)

    assert result.ok is True
    assert result.adb_mapping["LD1"] is None
    assert load_current_adb_mapping(path)["LD1"] is None


def test_clear_on_never_set_account_is_a_harmless_noop_success(tmp_path):
    path = _config_path(tmp_path)
    result = save_account_serial(AccountId.LD5, None, path)
    assert result.ok is True
    assert result.adb_mapping["LD5"] is None


def test_clear_never_triggers_duplicate_or_blank_rejection(tmp_path):
    path = _config_path(tmp_path)
    save_account_serial(AccountId.LD1, "shared-serial", path)
    # Clearing LD2 (which has no value) must succeed even though LD1
    # already holds a serial -- clear is not subject to the duplicate
    # check (None is never "equal" to a real serial).
    result = save_account_serial(AccountId.LD2, None, path)
    assert result.ok is True


# --- existing malformed config is surfaced, not silently papered over ---


def test_existing_invalid_adb_mapping_blocks_save_with_clear_error(tmp_path):
    path = _config_path(tmp_path)
    path.write_text("adb_mapping:\n  LD1: 12345\n", encoding="utf-8")  # wrong type

    result = save_account_serial(AccountId.LD2, "127.0.0.1:5555", path)

    assert result.ok is False
    assert result.error is MappingSaveError.EXISTING_CONFIG_INVALID


# --- ADB executable path registration (ADB-PATH-001) -----------------------


def test_load_current_adb_path_defaults_none_when_file_missing(tmp_path):
    assert load_current_adb_path(_config_path(tmp_path)) is None


def test_load_current_adb_path_reads_existing_value(tmp_path):
    path = _config_path(tmp_path)
    path.write_text("adb_path: C:/LDPlayer/LDPlayer14/adb.exe\n", encoding="utf-8")
    assert load_current_adb_path(path) == "C:/LDPlayer/LDPlayer14/adb.exe"


def test_save_adb_path_rejects_missing_file_fail_closed(tmp_path):
    path = _config_path(tmp_path)
    result = save_adb_path("C:/does/not/exist/adb.exe", path)

    assert result.ok is False
    assert result.error is AdbPathSaveError.NOT_FOUND
    assert not path.exists()  # nothing written
    assert load_current_adb_path(path) is None


def test_save_adb_path_rejects_blank(tmp_path):
    path = _config_path(tmp_path)
    result = save_adb_path("   ", path)

    assert result.ok is False
    assert result.error is AdbPathSaveError.BLANK
    assert not path.exists()


def test_save_adb_path_persists_a_real_existing_file(tmp_path):
    real_exe = tmp_path / "adb.exe"
    real_exe.write_bytes(b"")
    path = _config_path(tmp_path)

    result = save_adb_path(str(real_exe), path)

    assert result.ok is True
    assert result.adb_path == str(real_exe)
    assert load_current_adb_path(path) == str(real_exe)


def test_save_adb_path_rejects_a_directory_not_a_file(tmp_path):
    directory = tmp_path / "not_a_file"
    directory.mkdir()
    path = _config_path(tmp_path)

    result = save_adb_path(str(directory), path)

    assert result.ok is False
    assert result.error is AdbPathSaveError.NOT_FOUND


def test_clear_adb_path_always_succeeds_and_never_deletes_the_file(tmp_path):
    real_exe = tmp_path / "adb.exe"
    real_exe.write_bytes(b"")
    path = _config_path(tmp_path)
    save_adb_path(str(real_exe), path)

    result = save_adb_path(None, path)

    assert result.ok is True
    assert result.adb_path is None
    assert load_current_adb_path(path) is None
    assert real_exe.is_file()  # the actual adb.exe file itself is untouched


def test_save_adb_path_preserves_adb_mapping_and_other_sections(tmp_path):
    real_exe = tmp_path / "adb.exe"
    real_exe.write_bytes(b"")
    path = _config_path(tmp_path)
    save_account_serial(AccountId.LD1, "127.0.0.1:5555", path)

    save_adb_path(str(real_exe), path)

    assert load_current_adb_mapping(path)["LD1"] == "127.0.0.1:5555"
    assert load_current_adb_path(path) == str(real_exe)


def test_save_account_serial_preserves_adb_path(tmp_path):
    real_exe = tmp_path / "adb.exe"
    real_exe.write_bytes(b"")
    path = _config_path(tmp_path)
    save_adb_path(str(real_exe), path)

    save_account_serial(AccountId.LD2, "127.0.0.1:6000", path)

    assert load_current_adb_path(path) == str(real_exe)
