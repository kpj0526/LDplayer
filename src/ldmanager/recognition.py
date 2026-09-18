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
from typing import Mapping, Optional, Protocol

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
    # Center of the matched rectangle in full-frame relative coordinates.
    # ``None`` means this result cannot safely drive an image-based tap.
    match_center: Optional[tuple[float, float]] = None

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


class OpenCVTemplateRecognizer:
    """Real pixel recognizer using OpenCV template matching.

    ``template_map`` maps each configured expected label to a PNG file
    relative to ``templates_dir``.  The template is searched only inside
    the supplied device-relative ROI.  Missing assets, unreadable frames,
    an unavailable OpenCV installation, or an undersized ROI are all
    fail-closed: they return ``UNKNOWN``/``NO_MATCH`` and never authorize
    an input action.

    This class deliberately does not capture frames or send taps.  It can
    therefore be used identically for a GUI recognition preview and by the
    mission worker that performs guarded ADB input after a match.
    """

    def __init__(self, templates_dir: Path, template_map: Mapping[str, str]) -> None:
        self.templates_dir = Path(templates_dir)
        self.template_map = dict(template_map)
        self._templates: dict[str, object] = {}
        self._load_errors: dict[str, str] = {}
        try:
            import cv2  # type: ignore
            import numpy as np  # type: ignore
        except ImportError:
            self._cv2 = None
            self._np = None
            self._dependency_error = "OpenCV is not installed; run: pip install -e '.[recognition]'"
        else:
            self._cv2 = cv2
            self._np = np
            self._dependency_error = ""

    def _template_for(self, expected_label: str):
        if expected_label in self._templates:
            return self._templates[expected_label], None
        if expected_label in self._load_errors:
            return None, self._load_errors[expected_label]
        filename = self.template_map.get(expected_label)
        if not filename:
            error = f"No template configured for label {expected_label!r}."
            self._load_errors[expected_label] = error
            return None, error
        path = self.templates_dir / filename
        image = self._cv2.imread(str(path), self._cv2.IMREAD_GRAYSCALE) if self._cv2 else None
        if image is None or image.size == 0:
            error = f"Template unavailable or unreadable: {path}"
            self._load_errors[expected_label] = error
            return None, error
        self._templates[expected_label] = image
        return image, None

    def recognize(
        self,
        image_bytes: bytes,
        roi: RelativeRegion,
        expected_label: str,
        threshold: float,
    ) -> RecognitionResult:
        if self._cv2 is None or self._np is None:
            return RecognitionResult(RecognitionStatus.UNKNOWN, None, 0.0, self._dependency_error)
        if not 0.0 <= threshold <= 1.0:
            return RecognitionResult(RecognitionStatus.UNKNOWN, None, 0.0, "Invalid recognition threshold.")
        template, template_error = self._template_for(expected_label)
        if template is None:
            return RecognitionResult(RecognitionStatus.UNKNOWN, None, 0.0, template_error or "Template unavailable.")
        encoded = self._np.frombuffer(image_bytes, dtype=self._np.uint8)
        frame = self._cv2.imdecode(encoded, self._cv2.IMREAD_GRAYSCALE)
        if frame is None or frame.size == 0:
            return RecognitionResult(RecognitionStatus.UNKNOWN, None, 0.0, "Frame PNG could not be decoded.")
        height, width = frame.shape[:2]
        left = max(0, min(width - 1, round(roi.x * width)))
        top = max(0, min(height - 1, round(roi.y * height)))
        right = max(left + 1, min(width, round((roi.x + roi.width) * width)))
        bottom = max(top + 1, min(height, round((roi.y + roi.height) * height)))
        crop = frame[top:bottom, left:right]
        template_height, template_width = template.shape[:2]
        if crop.shape[0] < template_height or crop.shape[1] < template_width:
            return RecognitionResult(
                RecognitionStatus.UNKNOWN, None, 0.0,
                f"ROI {crop.shape[1]}x{crop.shape[0]} is smaller than template {template_width}x{template_height}.",
            )
        # Three candidate methods are evaluated, and the single highest-
        # confidence one wins (whichever it is -- never averaged).
        #
        # 1. Raw grayscale (GAME-CAL-001, real-capture calibration): most
        #    UI chrome in an ordinary (non-dimmed) frame is rendered
        #    pixel-identically run to run, so a plain, unnormalized
        #    TM_CCOEFF_NORMED match against a real, tightly-cropped
        #    template is the *most* reliable signal available -- verified
        #    against real customer 1280x720 captures at ~1.00 confidence
        #    for a true match vs. ~0.45-0.52 for a confidently different
        #    one, a far larger margin than histogram-equalized matching
        #    gives for the same crops (see docs/HANDOFF_CODE.md).
        # 2. Normalized (histogram-equalized) grayscale handles ordinary
        #    lighting/brightness variants that raw matching would miss.
        # 3. Edge matching is a further candidate for dimmed/modal-overlay
        #    frames (notably the customer 9,900 refresh-button reference)
        #    where text brightness changes but the button outline remains
        #    stable.
        #
        # Equalizing a small template against its own tiny histogram and
        # equalizing a large searched region against ITS OWN (very
        # different) histogram independently can distort an otherwise
        # perfect match -- candidate 1 exists specifically so that
        # distortion can never make a real, exact match score *lower*
        # than an equalized/edge-based one would.
        raw_scores = self._cv2.matchTemplate(crop, template, self._cv2.TM_CCOEFF_NORMED)
        _raw_min, confidence, _raw_min_location, location = self._cv2.minMaxLoc(raw_scores)

        normalized_crop = self._cv2.equalizeHist(crop)
        normalized_template = self._cv2.equalizeHist(template)
        scores = self._cv2.matchTemplate(normalized_crop, normalized_template, self._cv2.TM_CCOEFF_NORMED)
        _minimum, normalized_confidence, _min_location, normalized_location = self._cv2.minMaxLoc(scores)
        if normalized_confidence > confidence:
            confidence, location = normalized_confidence, normalized_location

        crop_edges = self._cv2.Canny(normalized_crop, 60, 160)
        template_edges = self._cv2.Canny(normalized_template, 60, 160)
        edge_scores = self._cv2.matchTemplate(crop_edges, template_edges, self._cv2.TM_CCOEFF_NORMED)
        _edge_min, edge_confidence, _edge_min_location, edge_location = self._cv2.minMaxLoc(edge_scores)
        if edge_confidence > confidence:
            confidence, location = edge_confidence, edge_location
        confidence = float(confidence)
        if confidence >= threshold:
            center_x = (left + location[0] + template_width / 2.0) / width
            center_y = (top + location[1] + template_height / 2.0) / height
            return RecognitionResult(
                RecognitionStatus.MATCH, expected_label, confidence, "OpenCV template matched in ROI.",
                (center_x, center_y),
            )
        return RecognitionResult(RecognitionStatus.NO_MATCH, None, confidence, "OpenCV template below threshold.")
