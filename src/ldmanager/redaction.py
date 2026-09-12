"""Credential-shaped text redaction (TP-001-RW-02 / stage 2 repair).

Independent of, but conceptually paired with, the config-file field
rejection in :mod:`ldmanager.config`:

* ``config.py`` refuses to *load* a config file that contains a
  credential-looking **key** at all.
* This module redacts a credential-looking **value** out of free-form
  text (log messages) *before* it is written anywhere, so a caller who
  accidentally logs ``"password=hunter2"`` never gets the literal value
  persisted to disk.

The original value is never retained: it is discarded by the regex
substitution, not stored, hashed, or queued anywhere for later use.
"""

from __future__ import annotations

import re

#: Placeholder that replaces every redacted value. Deliberately generic
#: (no length/shape hints about the original secret).
REDACTED_PLACEHOLDER = "***REDACTED***"

#: Field-name fragments treated as a single-token secret, e.g.
#: ``password=hunter2`` or ``token: abc123`` — only the token immediately
#: after the separator is replaced.
_SENSITIVE_WORD = (
    r"(?:password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|"
    r"private[_-]?key|credential|session[_-]?key)"
)

#: Header-style keys whose entire remaining value (which may contain
#: spaces, e.g. ``Bearer <jwt>`` or a multi-cookie string) must be
#: treated as sensitive, not just the first token.
_HEADER_WORD = r"(?:authorization|cookie)"

_KV_PATTERN = re.compile(
    rf"(?i)\b({_SENSITIVE_WORD})\b(\s*[:=]\s*)(\"[^\"]*\"|'[^']*'|\S+)"
)

_HEADER_PATTERN = re.compile(rf"(?im)\b({_HEADER_WORD})\b(\s*[:=]\s*)(.+)$")


def redact_sensitive_text(text: str) -> str:
    """Return ``text`` with credential-shaped values replaced.

    Order matters: the header pattern (which consumes the rest of the
    line for ``authorization``/``cookie``) runs first so it doesn't get
    partially pre-empted by the single-token pattern; the single-token
    pattern then mops up ``password=``/``token=``/etc. anywhere else in
    the (possibly already partially redacted) text.
    """

    if not text:
        return text

    def _header_sub(match: re.Match) -> str:
        return f"{match.group(1)}{match.group(2)}{REDACTED_PLACEHOLDER}"

    def _kv_sub(match: re.Match) -> str:
        return f"{match.group(1)}{match.group(2)}{REDACTED_PLACEHOLDER}"

    redacted = _HEADER_PATTERN.sub(_header_sub, text)
    redacted = _KV_PATTERN.sub(_kv_sub, redacted)
    return redacted
