"""Safe filename/path helpers (TP-001 stage 2).

Shared by the logging and diagnostics subsystems so that any
user/account-derived string used to build a filesystem path is defused
before it touches disk. Pure functions only — no logging, no ADB, no
credential handling.
"""

from __future__ import annotations

import re
from pathlib import Path

#: Conservative allow-list for a single path segment or filename.
_SAFE_CHARS_RE = re.compile(r"[^A-Za-z0-9._-]")
_SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9._-]+$")


class UnsafePathError(ValueError):
    """Raised when a filename or path segment fails safety validation."""


def sanitize_filename(name: str, *, default: str = "file") -> str:
    """Return a filesystem-safe filename derived from ``name``.

    * Any directory component is dropped (``Path(name).name`` only).
    * Characters outside ``[A-Za-z0-9._-]`` become ``_``.
    * Leading/trailing dots and underscores are trimmed (blocks ``..``,
      hidden-file surprises, and trailing-dot Windows quirks).
    * Falls back to ``default`` if nothing safe remains.
    """

    if not name:
        return default

    base = Path(name).name  # strips any directory components / traversal
    if not base:
        return default

    cleaned = _SAFE_CHARS_RE.sub("_", base).strip("._")
    if not cleaned:
        return default
    return cleaned


def ensure_safe_subdir(root: Path | str, *segments: str) -> Path:
    """Join ``segments`` under ``root`` and guarantee containment.

    Each segment must match the conservative allow-list and must not be
    ``.`` or ``..``; the resolved result must stay inside the resolved
    ``root``. Raises :class:`UnsafePathError` otherwise. Does not touch
    the filesystem (no directory is created).
    """

    root_path = Path(root)
    result = root_path
    for segment in segments:
        if (
            not segment
            or not _SAFE_SEGMENT_RE.match(segment)
            or segment in {".", ".."}
        ):
            raise UnsafePathError(f"Unsafe path segment: {segment!r}")
        result = result / segment

    resolved_root = root_path.resolve()
    resolved_result = result.resolve()
    if resolved_root != resolved_result and resolved_root not in resolved_result.parents:
        raise UnsafePathError(
            f"Resolved path {resolved_result} escapes root {resolved_root}"
        )
    return result
