"""Device-internal relative coordinates (TP-003 / MVP-001).

Deliberately the *only* kind of coordinate this project accepts for a
touch or a recognition region: a fraction of the target device's own
screen (``[0.0, 1.0]`` on each axis), validated strictly at
construction. There is no concept of a fixed external/desktop pixel
coordinate anywhere here, and no global mouse control exists in this
project — every resulting tap command is still scoped to exactly one
explicit ADB serial by the caller.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


class InvalidCoordinateError(ValueError):
    """Raised for an out-of-range or non-finite relative coordinate."""


class InvalidScreenSizeError(ValueError):
    """Raised for a non-positive/non-integer screen dimension."""


def _validate_fraction(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidCoordinateError(f"{name} must be a real number, got {value!r}.")
    numeric = float(value)
    if math.isnan(numeric) or math.isinf(numeric):
        raise InvalidCoordinateError(f"{name} must be finite, got {value!r}.")
    if not (0.0 <= numeric <= 1.0):
        raise InvalidCoordinateError(
            f"{name} must be within [0.0, 1.0] (device-relative), got {value!r}."
        )
    return numeric


@dataclass(frozen=True)
class RelativeCoordinate:
    """A point expressed as a fraction of the device's own screen.

    Both ``x`` and ``y`` must be finite real numbers in the closed
    interval ``[0.0, 1.0]`` — validated immediately in ``__post_init__``,
    so an invalid coordinate can never be constructed, let alone threaded
    through into a touch command.
    """

    x: float
    y: float

    def __post_init__(self) -> None:
        _validate_fraction("x", self.x)
        _validate_fraction("y", self.y)


@dataclass(frozen=True)
class ScreenSize:
    """A device's screen size in pixels.

    Used only to convert a :class:`RelativeCoordinate` into the absolute
    pixel arguments for a single `input tap` command scoped to one
    serial — never to address a fixed external/desktop coordinate.
    """

    width: int
    height: int

    def __post_init__(self) -> None:
        for name, value in (("width", self.width), ("height", self.height)):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise InvalidScreenSizeError(
                    f"{name} must be a positive integer, got {value!r}."
                )


_REGION_EPSILON = 1e-9


@dataclass(frozen=True)
class RelativeRegion:
    """A rectangular region of interest (ROI) as a fraction of the
    device's own screen — used to tell a recognizer *where* to look,
    never to move a mouse or address a fixed external coordinate.

    ``x``/``y`` are the top-left corner (each in ``[0.0, 1.0]``);
    ``width``/``height`` must be positive and the region must not
    extend past the far edge of the screen (``x + width <= 1.0``,
    ``y + height <= 1.0``, within a small floating-point tolerance).
    """

    x: float
    y: float
    width: float
    height: float

    def __post_init__(self) -> None:
        _validate_fraction("x", self.x)
        _validate_fraction("y", self.y)
        for name, value in (("width", self.width), ("height", self.height)):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise InvalidCoordinateError(f"{name} must be a real number, got {value!r}.")
            numeric = float(value)
            if math.isnan(numeric) or math.isinf(numeric) or not (0.0 < numeric <= 1.0):
                raise InvalidCoordinateError(
                    f"{name} must be within (0.0, 1.0], got {value!r}."
                )
        if self.x + self.width > 1.0 + _REGION_EPSILON:
            raise InvalidCoordinateError(
                f"Region extends past the right edge: x={self.x!r} + width={self.width!r} > 1.0."
            )
        if self.y + self.height > 1.0 + _REGION_EPSILON:
            raise InvalidCoordinateError(
                f"Region extends past the bottom edge: y={self.y!r} + height={self.height!r} > 1.0."
            )


def to_pixel_rect(screen_size: ScreenSize, region: RelativeRegion) -> tuple[int, int, int, int]:
    """Convert a validated relative region to an absolute pixel rectangle.

    Returns ``(x, y, width, height)`` in pixels, clamped so the region
    never extends outside ``[0, dimension)``. Purely a geometry
    calculation for a future real cropping/recognition step — no image
    is read or written here.
    """

    x_px = min(max(round(region.x * screen_size.width), 0), screen_size.width - 1)
    y_px = min(max(round(region.y * screen_size.height), 0), screen_size.height - 1)
    width_px = max(min(round(region.width * screen_size.width), screen_size.width - x_px), 1)
    height_px = max(min(round(region.height * screen_size.height), screen_size.height - y_px), 1)
    return x_px, y_px, width_px, height_px


def to_pixel_coordinates(screen_size: ScreenSize, point: RelativeCoordinate) -> tuple[int, int]:
    """Convert a validated relative coordinate to absolute device pixels.

    Clamped defensively to ``[0, dimension - 1]`` so the boundary
    fractions (0.0/1.0) never round to a pixel just outside the visible
    screen.
    """

    x_px = min(max(round(point.x * screen_size.width), 0), screen_size.width - 1)
    y_px = min(max(round(point.y * screen_size.height), 0), screen_size.height - 1)
    return x_px, y_px


def build_tap_args(screen_size: ScreenSize, point: RelativeCoordinate) -> list[str]:
    """Build the `shell input tap <x> <y>` argv tail for exactly one point.

    Still requires the caller to scope this through
    :meth:`~ldmanager.adb.AdbRunner.run` with an explicit serial — this
    function only ever produces the tap arguments, never a full command,
    and the coordinates it emits are always device-internal pixels
    derived from a validated relative fraction, never a global desktop
    coordinate.
    """

    x_px, y_px = to_pixel_coordinates(screen_size, point)
    return ["shell", "input", "tap", str(x_px), str(y_px)]
