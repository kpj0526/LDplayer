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
