import pytest

from ldmanager.adb import AdbBinaryResult
from ldmanager.screenshot import (
    DEFAULT_CAPTURE_ARGS,
    CaptureError,
    capture_screenshot,
)
from tests.fakes import ExceptionRaisingCaptureRunner, FakeAdbRunner

_VALID_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32  # magic header + filler bytes
_SERIAL = "127.0.0.1:5555"


def test_capture_success_returns_validated_bytes():
    runner = FakeAdbRunner(
        capture_results={(_SERIAL, DEFAULT_CAPTURE_ARGS): AdbBinaryResult(
            serial=_SERIAL, args=DEFAULT_CAPTURE_ARGS, returncode=0,
            stdout_bytes=_VALID_PNG, stderr="",
        )}
    )

    result = capture_screenshot(runner, _SERIAL)

    assert result.ok is True
    assert result.error is CaptureError.NONE
    assert result.image_bytes == _VALID_PNG
    assert runner.capture_calls == [(_SERIAL, DEFAULT_CAPTURE_ARGS)]


def test_capture_runner_nonzero_returncode_is_reported_not_raised():
    runner = FakeAdbRunner(
        capture_results={(_SERIAL, DEFAULT_CAPTURE_ARGS): AdbBinaryResult(
            serial=_SERIAL, args=DEFAULT_CAPTURE_ARGS, returncode=1,
            stdout_bytes=b"", stderr="device offline",
        )}
    )

    result = capture_screenshot(runner, _SERIAL)

    assert result.ok is False
    assert result.error is CaptureError.RUNNER_FAILED
    assert result.image_bytes == b""


def test_capture_empty_bytes_is_reported():
    runner = FakeAdbRunner(
        capture_results={(_SERIAL, DEFAULT_CAPTURE_ARGS): AdbBinaryResult(
            serial=_SERIAL, args=DEFAULT_CAPTURE_ARGS, returncode=0,
            stdout_bytes=b"", stderr="",
        )}
    )

    result = capture_screenshot(runner, _SERIAL)

    assert result.ok is False
    assert result.error is CaptureError.EMPTY_OUTPUT


def test_capture_invalid_image_bytes_is_reported():
    runner = FakeAdbRunner(
        capture_results={(_SERIAL, DEFAULT_CAPTURE_ARGS): AdbBinaryResult(
            serial=_SERIAL, args=DEFAULT_CAPTURE_ARGS, returncode=0,
            stdout_bytes=b"not a png at all", stderr="",
        )}
    )

    result = capture_screenshot(runner, _SERIAL)

    assert result.ok is False
    assert result.error is CaptureError.INVALID_IMAGE_BYTES


def test_capture_truncated_magic_header_is_rejected():
    runner = FakeAdbRunner(
        capture_results={(_SERIAL, DEFAULT_CAPTURE_ARGS): AdbBinaryResult(
            serial=_SERIAL, args=DEFAULT_CAPTURE_ARGS, returncode=0,
            stdout_bytes=b"\x89PN",  # too short, not a real PNG magic
            stderr="",
        )}
    )

    result = capture_screenshot(runner, _SERIAL)

    assert result.ok is False
    assert result.error is CaptureError.INVALID_IMAGE_BYTES


def test_capture_runner_exception_is_reported_not_propagated():
    runner = ExceptionRaisingCaptureRunner("boom")

    result = capture_screenshot(runner, _SERIAL)

    assert result.ok is False
    assert result.error is CaptureError.EXCEPTION
    assert "boom" in result.detail


def test_capture_rejects_blank_serial_before_touching_runner():
    runner = FakeAdbRunner()
    with pytest.raises(ValueError):
        capture_screenshot(runner, "")
    assert runner.capture_calls == []


def test_capture_rejects_whitespace_only_serial():
    runner = FakeAdbRunner()
    with pytest.raises(ValueError):
        capture_screenshot(runner, "   ")
    assert runner.capture_calls == []


def test_capture_is_scoped_to_exactly_the_given_serial_and_args():
    other_serial = "127.0.0.1:5557"
    runner = FakeAdbRunner(
        capture_results={
            (_SERIAL, DEFAULT_CAPTURE_ARGS): AdbBinaryResult(
                serial=_SERIAL, args=DEFAULT_CAPTURE_ARGS, returncode=0,
                stdout_bytes=_VALID_PNG, stderr="",
            ),
            (other_serial, DEFAULT_CAPTURE_ARGS): AdbBinaryResult(
                serial=other_serial, args=DEFAULT_CAPTURE_ARGS, returncode=1,
                stdout_bytes=b"", stderr="offline",
            ),
        }
    )

    result_a = capture_screenshot(runner, _SERIAL)
    result_b = capture_screenshot(runner, other_serial)

    assert result_a.ok is True
    assert result_b.ok is False
    assert runner.capture_calls == [
        (_SERIAL, DEFAULT_CAPTURE_ARGS),
        (other_serial, DEFAULT_CAPTURE_ARGS),
    ]
