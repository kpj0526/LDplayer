import pytest

from ldmanager.adb import (
    AdbDeviceState,
    SubprocessAdbRunner,
    build_adb_command,
    parse_adb_devices_output,
)
from tests.fakes import FakeAdbRunner


# --- parse_adb_devices_output --------------------------------------------


def test_parse_valid_devices_output():
    raw = (
        "List of devices attached\n"
        "127.0.0.1:5555\tdevice\n"
        "127.0.0.1:5557\toffline\n"
        "127.0.0.1:5559\tunauthorized\n"
        "\n"
    )
    devices = parse_adb_devices_output(raw)
    assert [d.serial for d in devices] == [
        "127.0.0.1:5555",
        "127.0.0.1:5557",
        "127.0.0.1:5559",
    ]
    assert devices[0].state is AdbDeviceState.DEVICE
    assert devices[1].state is AdbDeviceState.OFFLINE
    assert devices[2].state is AdbDeviceState.UNAUTHORIZED


def test_parse_unknown_state_is_classified_unknown_not_crash():
    devices = parse_adb_devices_output("127.0.0.1:5561\tqwerty\n")
    assert devices[0].state is AdbDeviceState.UNKNOWN
    assert devices[0].raw_state == "qwerty"


def test_parse_skips_lines_with_no_state_column():
    # A line with only one whitespace-separated token (no state column
    # at all) can't be turned into a device and must be skipped, not
    # mis-parsed.
    raw = "onlyoneword\n127.0.0.1:5555\tdevice\n"
    devices = parse_adb_devices_output(raw)
    assert len(devices) == 1
    assert devices[0].serial == "127.0.0.1:5555"


def test_parse_treats_unrecognized_multi_token_line_as_unknown_state():
    # A line that does have >=2 tokens but isn't a real adb line is
    # still safely classified (UNKNOWN state) rather than crashing or
    # silently vanishing.
    raw = "not a valid line at all\n127.0.0.1:5555\tdevice\n"
    devices = parse_adb_devices_output(raw)
    assert len(devices) == 2
    assert devices[0].state is AdbDeviceState.UNKNOWN
    assert devices[1].serial == "127.0.0.1:5555"
    assert devices[1].state is AdbDeviceState.DEVICE


def test_parse_ignores_banner_and_daemon_lines():
    raw = "* daemon not running; starting now *\nList of devices attached\n\n"
    assert parse_adb_devices_output(raw) == []


def test_parse_empty_output_returns_empty_list():
    assert parse_adb_devices_output("") == []


def test_parse_completely_garbled_output_does_not_raise():
    # Must never raise, regardless of content; whatever comes out is
    # safely classified rather than crashing discovery.
    devices = parse_adb_devices_output("\x00\x01 garbage \xff\n")
    assert isinstance(devices, list)


# --- build_adb_command: single-serial scoping ----------------------------


def test_build_adb_command_scopes_to_single_serial():
    cmd = build_adb_command("adb", "127.0.0.1:5555", ["shell", "echo", "hi"])
    assert cmd == ["adb", "-s", "127.0.0.1:5555", "shell", "echo", "hi"]


def test_build_adb_command_rejects_empty_serial():
    with pytest.raises(ValueError):
        build_adb_command("adb", "", ["devices"])


def test_build_adb_command_rejects_whitespace_in_serial():
    with pytest.raises(ValueError):
        build_adb_command("adb", "127.0.0.1 5555", ["devices"])


def test_different_serials_produce_non_overlapping_commands():
    cmd1 = build_adb_command("adb", "SERIAL-A", ["shell", "true"])
    cmd2 = build_adb_command("adb", "SERIAL-B", ["shell", "true"])
    assert cmd1 != cmd2
    assert "SERIAL-A" in cmd1 and "SERIAL-A" not in cmd2
    assert "SERIAL-B" in cmd2 and "SERIAL-B" not in cmd1


# --- SubprocessAdbRunner: argv construction, no real process spawned ----


def test_subprocess_adb_runner_list_devices_invokes_expected_argv(monkeypatch):
    captured = {}

    class _FakeCompleted:
        stdout = "List of devices attached\n\n"
        stderr = ""
        returncode = 0

    def fake_run(args, **kwargs):
        captured["args"] = args
        return _FakeCompleted()

    monkeypatch.setattr("ldmanager.adb.subprocess.run", fake_run)

    runner = SubprocessAdbRunner(adb_path="adb", timeout=5)
    output = runner.list_devices()

    assert captured["args"] == ["adb", "devices"]
    assert output == "List of devices attached\n\n"


def test_subprocess_adb_runner_run_invokes_scoped_argv(monkeypatch):
    captured = {}

    class _FakeCompleted:
        stdout = "ok\n"
        stderr = ""
        returncode = 0

    def fake_run(args, **kwargs):
        captured["args"] = args
        return _FakeCompleted()

    monkeypatch.setattr("ldmanager.adb.subprocess.run", fake_run)

    runner = SubprocessAdbRunner(adb_path="adb")
    result = runner.run("127.0.0.1:5555", ["shell", "echo", "hi"])

    assert captured["args"] == ["adb", "-s", "127.0.0.1:5555", "shell", "echo", "hi"]
    assert result.ok
    assert result.stdout == "ok\n"


def test_subprocess_adb_runner_run_requires_serial_before_spawning(monkeypatch):
    def fail_if_called(*args, **kwargs):  # pragma: no cover
        raise AssertionError("subprocess.run must not be called for an empty serial")

    monkeypatch.setattr("ldmanager.adb.subprocess.run", fail_if_called)

    runner = SubprocessAdbRunner(adb_path="adb")
    with pytest.raises(ValueError):
        runner.run("", ["devices"])


# --- FakeAdbRunner: command separation across accounts -------------------


def test_fake_runner_records_calls_scoped_per_serial():
    runner = FakeAdbRunner()
    runner.run("SERIAL-A", ["shell", "echo", "a"])
    runner.run("SERIAL-B", ["shell", "echo", "b"])

    assert runner.calls == [
        ("SERIAL-A", ("shell", "echo", "a")),
        ("SERIAL-B", ("shell", "echo", "b")),
    ]


def test_fake_runner_rejects_empty_serial():
    runner = FakeAdbRunner()
    with pytest.raises(ValueError):
        runner.run("", ["devices"])
