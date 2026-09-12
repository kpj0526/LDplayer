import os
import time
from pathlib import Path

import pytest

from ldmanager.logs import (
    LoggingSettings,
    account_log_dir,
    close_account_logger,
    error_log_path,
    get_account_logger,
    purge_expired_logs,
    task_log_path,
)
from ldmanager.models import AccountId


@pytest.fixture(autouse=True)
def _cleanup_account_loggers():
    yield
    for account_id in AccountId:
        close_account_logger(account_id)


def test_account_log_dir_is_per_account(tmp_path):
    settings = LoggingSettings(root_dir=tmp_path / "logs")
    dir1 = account_log_dir(settings, AccountId.LD1)
    dir2 = account_log_dir(settings, AccountId.LD2)
    assert dir1 == tmp_path / "logs" / "LD1"
    assert dir2 == tmp_path / "logs" / "LD2"
    assert dir1 != dir2


def test_task_and_error_logs_are_separated(tmp_path):
    settings = LoggingSettings(root_dir=tmp_path / "logs")
    logger = get_account_logger(AccountId.LD1, settings, force=True)
    logger.info("hello task")
    logger.error("boom")
    for handler in logger.handlers:
        handler.flush()

    task_text = task_log_path(settings, AccountId.LD1).read_text(encoding="utf-8")
    error_text = error_log_path(settings, AccountId.LD1).read_text(encoding="utf-8")

    assert "hello task" in task_text
    assert "boom" not in task_text
    assert "boom" in error_text
    assert "hello task" not in error_text


def test_get_account_logger_is_idempotent_without_force(tmp_path):
    settings = LoggingSettings(root_dir=tmp_path / "logs")
    logger1 = get_account_logger(AccountId.LD2, settings, force=True)
    handler_count = len(logger1.handlers)
    logger2 = get_account_logger(AccountId.LD2, settings)
    assert logger1 is logger2
    assert len(logger2.handlers) == handler_count


def test_purge_expired_logs_removes_only_old_rotated_files(tmp_path):
    settings = LoggingSettings(root_dir=tmp_path / "logs", retention_days=1)
    logger = get_account_logger(AccountId.LD3, settings, force=True)
    logger.info("current")
    for handler in logger.handlers:
        handler.flush()

    current_file = task_log_path(settings, AccountId.LD3)
    rotated = current_file.with_name(current_file.name + ".1")
    rotated.write_text("old", encoding="utf-8")
    old_time = time.time() - (2 * 86400)
    os.utime(rotated, (old_time, old_time))

    deleted = purge_expired_logs(settings)

    assert rotated in deleted
    assert not rotated.exists()
    assert current_file.exists()  # fresh file untouched


def test_purge_expired_logs_on_missing_root_is_noop(tmp_path):
    settings = LoggingSettings(root_dir=tmp_path / "does_not_exist")
    assert purge_expired_logs(settings) == []


# --- TP-001-RW-02: sensitive-value redaction regression coverage ---------

_CONTROLLED_PASSWORD_MARKER = "S3cr3t-ControlMarker-9f8e7d"


def test_password_marker_absent_from_task_log(tmp_path):
    settings = LoggingSettings(root_dir=tmp_path / "logs")
    logger = get_account_logger(AccountId.LD5, settings, force=True)
    logger.info("login attempt password=%s", _CONTROLLED_PASSWORD_MARKER)
    for handler in logger.handlers:
        handler.flush()

    text = task_log_path(settings, AccountId.LD5).read_text(encoding="utf-8")
    assert _CONTROLLED_PASSWORD_MARKER not in text
    assert "password=***REDACTED***" in text


def test_password_marker_absent_from_error_log(tmp_path):
    settings = LoggingSettings(root_dir=tmp_path / "logs")
    logger = get_account_logger(AccountId.LD6, settings, force=True)
    logger.error("auth failed password=%s", _CONTROLLED_PASSWORD_MARKER)
    for handler in logger.handlers:
        handler.flush()

    text = error_log_path(settings, AccountId.LD6).read_text(encoding="utf-8")
    assert _CONTROLLED_PASSWORD_MARKER not in text
    assert "password=***REDACTED***" in text


def test_token_api_key_authorization_cookie_markers_absent_from_task_log(tmp_path):
    settings = LoggingSettings(root_dir=tmp_path / "logs")
    logger = get_account_logger(AccountId.LD7, settings, force=True)
    logger.info("token=%s", "tok-controlmarker-111")
    logger.info("api_key=%s", "key-controlmarker-222")
    logger.info("Authorization: Bearer jwt-controlmarker-333")
    logger.info("Cookie: session=cookie-controlmarker-444; other=1")
    for handler in logger.handlers:
        handler.flush()

    text = task_log_path(settings, AccountId.LD7).read_text(encoding="utf-8")
    for marker in (
        "tok-controlmarker-111",
        "key-controlmarker-222",
        "jwt-controlmarker-333",
        "cookie-controlmarker-444",
    ):
        assert marker not in text
    assert text.count("***REDACTED***") == 4


def test_redaction_survives_percent_style_argument_not_just_format_string(tmp_path):
    # Guards against a fix that only regex-scans the literal format
    # string and misses a secret supplied as a logging %-arg.
    settings = LoggingSettings(root_dir=tmp_path / "logs")
    logger = get_account_logger(AccountId.LD8, settings, force=True)
    logger.info("password=%s", "arg-only-controlmarker-555")
    for handler in logger.handlers:
        handler.flush()

    text = task_log_path(settings, AccountId.LD8).read_text(encoding="utf-8")
    assert "arg-only-controlmarker-555" not in text


def test_non_sensitive_messages_are_unaffected_by_redaction(tmp_path):
    settings = LoggingSettings(root_dir=tmp_path / "logs")
    logger = get_account_logger(AccountId.LD9, settings, force=True)
    logger.info("account LD9 transitioned to state=online")
    for handler in logger.handlers:
        handler.flush()

    text = task_log_path(settings, AccountId.LD9).read_text(encoding="utf-8")
    assert "account LD9 transitioned to state=online" in text
    assert "REDACTED" not in text


# --- TP-001-RW-03: exc_info/traceback redaction regression coverage -----


def test_logger_exception_traceback_marker_absent_from_error_log(tmp_path):
    """Reproduces the QA-reported failure: logger.exception() must not
    leak a credential-shaped value via the formatted traceback."""

    settings = LoggingSettings(root_dir=tmp_path / "logs")
    logger = get_account_logger(AccountId.LD1, settings, force=True)
    marker = "Tb-ControlMarker-abc123"

    try:
        raise ValueError(f"login failed password={marker}")
    except ValueError:
        logger.exception("unexpected failure")
    for handler in logger.handlers:
        handler.flush()

    text = error_log_path(settings, AccountId.LD1).read_text(encoding="utf-8")
    assert marker not in text
    assert "password=***REDACTED***" in text
    # Normal error diagnostics (exception type, traceback framing,
    # non-sensitive message) must still be present.
    assert "ValueError" in text
    assert "unexpected failure" in text
    assert "Traceback (most recent call last)" in text


def test_exc_info_marker_absent_from_task_log_when_logged_below_error(tmp_path):
    """exc_info=True can be passed at INFO level too (handled, non-fatal
    case) -- the task.log path through the same filter must redact it."""

    settings = LoggingSettings(root_dir=tmp_path / "logs")
    logger = get_account_logger(AccountId.LD2, settings, force=True)
    marker = "Tb-ControlMarker-def456"

    try:
        raise RuntimeError(f"token={marker}")
    except RuntimeError:
        logger.info("handled non-fatal issue", exc_info=True)
    for handler in logger.handlers:
        handler.flush()

    text = task_log_path(settings, AccountId.LD2).read_text(encoding="utf-8")
    assert marker not in text
    assert "token=***REDACTED***" in text
    assert "RuntimeError" in text
    assert "handled non-fatal issue" in text
