import pytest

from ldmanager.coordinates import (
    InvalidCoordinateError,
    InvalidScreenSizeError,
    RelativeCoordinate,
    ScreenSize,
    build_tap_args,
    to_pixel_coordinates,
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
