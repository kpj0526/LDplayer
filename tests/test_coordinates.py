import pytest

from ldmanager.coordinates import (
    InvalidCoordinateError,
    InvalidScreenSizeError,
    RelativeCoordinate,
    RelativeRegion,
    ScreenSize,
    build_tap_args,
    to_pixel_coordinates,
    to_pixel_rect,
)


# --- RelativeCoordinate: strict [0.0, 1.0] validation --------------------


def test_valid_coordinate_within_bounds_is_accepted():
    point = RelativeCoordinate(x=0.5, y=0.25)
    assert point.x == 0.5
    assert point.y == 0.25


@pytest.mark.parametrize("x,y", [(0.0, 0.0), (1.0, 1.0), (0.0, 1.0), (1.0, 0.0)])
def test_boundary_coordinates_are_accepted(x, y):
    RelativeCoordinate(x=x, y=y)  # must not raise


@pytest.mark.parametrize(
    "x,y",
    [
        (-0.01, 0.5),
        (0.5, -0.01),
        (1.01, 0.5),
        (0.5, 1.01),
        (-1.0, -1.0),
        (2.0, 2.0),
    ],
)
def test_out_of_range_coordinates_are_rejected(x, y):
    with pytest.raises(InvalidCoordinateError):
        RelativeCoordinate(x=x, y=y)


def test_nan_coordinate_is_rejected():
    with pytest.raises(InvalidCoordinateError):
        RelativeCoordinate(x=float("nan"), y=0.5)


def test_infinite_coordinate_is_rejected():
    with pytest.raises(InvalidCoordinateError):
        RelativeCoordinate(x=0.5, y=float("inf"))


def test_non_numeric_coordinate_is_rejected():
    with pytest.raises(InvalidCoordinateError):
        RelativeCoordinate(x="0.5", y=0.5)  # type: ignore[arg-type]


def test_bool_coordinate_is_rejected():
    # bool is a subclass of int in Python; explicitly excluded so a
    # stray True/False can never be silently treated as 1.0/0.0.
    with pytest.raises(InvalidCoordinateError):
        RelativeCoordinate(x=True, y=0.5)  # type: ignore[arg-type]


# --- ScreenSize: positive integers only ----------------------------------


def test_valid_screen_size_is_accepted():
    size = ScreenSize(width=1080, height=1920)
    assert (size.width, size.height) == (1080, 1920)


@pytest.mark.parametrize("width,height", [(0, 100), (100, 0), (-1, 100), (100, -1)])
def test_non_positive_screen_size_is_rejected(width, height):
    with pytest.raises(InvalidScreenSizeError):
        ScreenSize(width=width, height=height)


def test_non_integer_screen_size_is_rejected():
    with pytest.raises(InvalidScreenSizeError):
        ScreenSize(width=1080.5, height=1920)  # type: ignore[arg-type]


# --- to_pixel_coordinates / build_tap_args --------------------------------


def test_to_pixel_coordinates_center_point():
    size = ScreenSize(width=1000, height=2000)
    point = RelativeCoordinate(x=0.5, y=0.5)
    assert to_pixel_coordinates(size, point) == (500, 1000)


def test_to_pixel_coordinates_clamped_at_upper_boundary():
    size = ScreenSize(width=1000, height=2000)
    point = RelativeCoordinate(x=1.0, y=1.0)
    x_px, y_px = to_pixel_coordinates(size, point)
    assert x_px == size.width - 1
    assert y_px == size.height - 1


def test_to_pixel_coordinates_clamped_at_lower_boundary():
    size = ScreenSize(width=1000, height=2000)
    point = RelativeCoordinate(x=0.0, y=0.0)
    assert to_pixel_coordinates(size, point) == (0, 0)


def test_build_tap_args_shape():
    size = ScreenSize(width=1080, height=1920)
    point = RelativeCoordinate(x=0.5, y=0.5)
    args = build_tap_args(size, point)
    assert args[:3] == ["shell", "input", "tap"]
    assert args[3:] == ["540", "960"]


def test_build_tap_args_differ_for_different_points():
    size = ScreenSize(width=1080, height=1920)
    args1 = build_tap_args(size, RelativeCoordinate(x=0.1, y=0.1))
    args2 = build_tap_args(size, RelativeCoordinate(x=0.9, y=0.9))
    assert args1 != args2


# --- RelativeRegion: ROI validation ----------------------------------------


def test_valid_region_is_accepted():
    region = RelativeRegion(x=0.1, y=0.1, width=0.2, height=0.3)
    assert (region.x, region.y, region.width, region.height) == (0.1, 0.1, 0.2, 0.3)


def test_full_screen_region_is_accepted():
    RelativeRegion(x=0.0, y=0.0, width=1.0, height=1.0)  # must not raise


@pytest.mark.parametrize(
    "x,y,width,height",
    [
        (0.9, 0.0, 0.2, 0.1),  # extends past right edge
        (0.0, 0.9, 0.1, 0.2),  # extends past bottom edge
        (0.0, 0.0, 0.0, 0.1),  # zero width
        (0.0, 0.0, 0.1, 0.0),  # zero height
        (0.0, 0.0, -0.1, 0.1),  # negative width
        (0.0, 0.0, 1.5, 0.1),  # width > 1
        (-0.1, 0.0, 0.1, 0.1),  # negative x
    ],
)
def test_invalid_region_is_rejected(x, y, width, height):
    with pytest.raises(InvalidCoordinateError):
        RelativeRegion(x=x, y=y, width=width, height=height)


def test_region_non_numeric_dimension_is_rejected():
    with pytest.raises(InvalidCoordinateError):
        RelativeRegion(x=0.0, y=0.0, width="0.1", height=0.1)  # type: ignore[arg-type]


def test_to_pixel_rect_converts_and_clamps():
    size = ScreenSize(width=1000, height=2000)
    region = RelativeRegion(x=0.1, y=0.2, width=0.3, height=0.4)
    x_px, y_px, w_px, h_px = to_pixel_rect(size, region)
    assert (x_px, y_px) == (100, 400)
    assert (w_px, h_px) == (300, 800)


def test_to_pixel_rect_full_screen_stays_within_bounds():
    size = ScreenSize(width=1000, height=2000)
    region = RelativeRegion(x=0.0, y=0.0, width=1.0, height=1.0)
    x_px, y_px, w_px, h_px = to_pixel_rect(size, region)
    assert x_px >= 0 and y_px >= 0
    assert x_px + w_px <= size.width
    assert y_px + h_px <= size.height
