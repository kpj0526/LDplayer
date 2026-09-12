"""Per-account rotating log setup + retention policy (TP-001 stage 2).

Scope: file layout, rotation, and a retention (purge) policy for LD1~LD9
task/error logs. No credential material is ever accepted or written by
this module — callers must not pass secrets as log message arguments.
No ADB/LDPlayer/game interaction happens here.
"""

from __future__ import annotations

import logging
import logging.handlers
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .models import AccountId
from .paths import ensure_safe_subdir

DEFAULT_ROOT_DIR = Path("logs")
DEFAULT_RETENTION_DAYS = 14
DEFAULT_MAX_BYTES = 5_000_000
DEFAULT_BACKUP_COUNT = 5

_LOGGER_NAME_PREFIX = "ldmanager.account"


@dataclass(frozen=True)
class LoggingSettings:
    """Logging policy: where files go, and how they rotate/expire."""

    root_dir: Path = DEFAULT_ROOT_DIR
    retention_days: int = DEFAULT_RETENTION_DAYS
    max_bytes: int = DEFAULT_MAX_BYTES
    backup_count: int = DEFAULT_BACKUP_COUNT


class _MaxLevelFilter(logging.Filter):
    """Lets records through only *below* ``max_level``.

    Used so task.log never receives ERROR+ records (those go to
    error.log instead), keeping the two files cleanly separated.
    """

    def __init__(self, max_level: int) -> None:
        super().__init__()
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        return record.levelno < self.max_level


def account_log_dir(settings: LoggingSettings, account_id: AccountId) -> Path:
    """Per-account log directory, e.g. ``<root_dir>/LD1``."""

    return ensure_safe_subdir(settings.root_dir, account_id.value)


def task_log_path(settings: LoggingSettings, account_id: AccountId) -> Path:
    return account_log_dir(settings, account_id) / "task.log"


def error_log_path(settings: LoggingSettings, account_id: AccountId) -> Path:
    return account_log_dir(settings, account_id) / "error.log"


def _logger_name(account_id: AccountId) -> str:
    return f"{_LOGGER_NAME_PREFIX}.{account_id.value}"


def get_account_logger(
    account_id: AccountId,
    settings: Optional[LoggingSettings] = None,
    *,
    force: bool = False,
) -> logging.Logger:
    """Return a configured logger for ``account_id``.

    Attaches two rotating file handlers: ``task.log`` (INFO/WARNING) and
    ``error.log`` (ERROR and above). Safe to call repeatedly — handlers
    are only (re)installed once unless ``force=True`` (tests use this to
    repoint a logger at a fresh ``tmp_path`` between cases).
    """

    settings = settings or LoggingSettings()
    logger = logging.getLogger(_logger_name(account_id))

    if logger.handlers and not force:
        return logger

    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)

    log_dir = account_log_dir(settings, account_id)
    log_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")

    task_handler = logging.handlers.RotatingFileHandler(
        task_log_path(settings, account_id),
        maxBytes=settings.max_bytes,
        backupCount=settings.backup_count,
        encoding="utf-8",
    )
    task_handler.setLevel(logging.INFO)
    task_handler.addFilter(_MaxLevelFilter(logging.ERROR))
    task_handler.setFormatter(formatter)

    error_handler = logging.handlers.RotatingFileHandler(
        error_log_path(settings, account_id),
        maxBytes=settings.max_bytes,
        backupCount=settings.backup_count,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    logger.addHandler(task_handler)
    logger.addHandler(error_handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


def close_account_logger(account_id: AccountId) -> None:
    """Close and detach all handlers for an account logger.

    Mainly for tests/shutdown paths so log files aren't left open.
    """

    logger = logging.getLogger(_logger_name(account_id))
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)


def purge_expired_logs(
    settings: LoggingSettings, *, now: Optional[float] = None
) -> list[Path]:
    """Delete rotated log files older than ``settings.retention_days``.

    Only touches files matching the known log naming scheme
    (``task.log*`` / ``error.log*``) directly under each account's log
    directory, so it never wanders into unrelated files. Returns the
    list of deleted paths.
    """

    now = time.time() if now is None else now
    cutoff = now - settings.retention_days * 86400
    root = Path(settings.root_dir)
    deleted: list[Path] = []

    if not root.exists():
        return deleted

    for pattern in ("task.log*", "error.log*"):
        for path in root.glob(f"*/{pattern}"):
            try:
                if path.is_file() and path.stat().st_mtime < cutoff:
                    path.unlink()
                    deleted.append(path)
            except OSError:
                # Best-effort purge: skip files we can't stat/remove
                # (e.g. concurrently held open) rather than aborting.
                continue

    return deleted
