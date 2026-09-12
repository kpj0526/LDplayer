"""Configurable template/OCR recognition abstraction (MVP-001).

This module defines *only* the interface and a safe placeholder
implementation. No OCR library and no template-matching library is
wired in — that is explicitly deferred to a later stage (see
``docs/REAL_CAPTURE_CHECKLIST.md``). The placeholder recognizer never
fabricates a match: every call returns ``UNKNOWN`` with zero
confidence, so any state machine built on top of it always takes the
safe "not recognized" branch until a real recognizer is substituted.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Protocol

from .coordinates import RelativeRegion


class RecognitionStatus(str, Enum):
    MATCH = "match"
    NO_MATCH = "no_match"
    LOW_CONFIDENCE = "low_confidence"
    UNKNOWN = "unknown"  # recognizer could not determine anything at all


@dataclass(frozen=True)
class RecognitionResult:
    """Outcome of one recognition attempt against one captured frame.

    ``detail`` is a short, secret-free diagnostic string. ``matched`` is
    the single boolean a caller should branch on — everything other
    than :attr:`RecognitionStatus.MATCH` is treated as "not found",
    never as an error to propagate.
    """

    status: RecognitionStatus
    label: Optional[str]
    confidence: float
    detail: str

    @property
    def matched(self) -> bool:
        return self.status is RecognitionStatus.MATCH


class Recognizer(Protocol):
    """Minimal interface a recognizer must satisfy.

    Implementations receive the *already-captured, already-validated*
    PNG bytes for the whole frame plus a ``roi`` hint describing where
    to look, and must never perform any capture or touch themselves.
    """

    def recognize(
        self,
        image_bytes: bytes,
        roi: RelativeRegion,
        expected_label: str,
        threshold: float,
    ) -> RecognitionResult:
        ...


class PlaceholderRecognizer:
    """Safe default recognizer: this MVP implements no real OCR/template
    matching. Every call returns :attr:`RecognitionStatus.UNKNOWN` with
    confidence ``0.0`` — it never claims a match, regardless of input.

    ``templates_dir`` is accepted and stored only as a forward-looking
    configuration placeholder for a future real implementation; nothing
    in this class reads from it.
    """

    def __init__(self, templates_dir: Optional[Path] = None) -> None:
        self.templates_dir = templates_dir

    def recognize(
        self,
        image_bytes: bytes,
        roi: RelativeRegion,
        expected_label: str,
        threshold: float,
    ) -> RecognitionResult:
        del image_bytes, roi, expected_label, threshold  # unused: placeholder only
        return RecognitionResult(
            status=RecognitionStatus.UNKNOWN,
            label=None,
            confidence=0.0,
            detail=(
                "PlaceholderRecognizer: no real OCR/template matching is "
                "implemented yet; always reports unknown/no match."
            ),
        )
