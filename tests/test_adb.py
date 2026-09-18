import pytest

from ldmanager.adb import (
    AdbDeviceState,
    InputGateAdbRunner,
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


def test_subprocess_adb_runner_never_flashes_a_console_window_on_windows(monkeypatch):
    """NO-CONSOLE-FLICKER-001: real customer report -- every ADB
    subprocess call flashed a black console window on screen (visible
    constantly given one call per tap/capture). On Windows, every
    subprocess.run() invocation here must pass creationflags=
    CREATE_NO_WINDOW to suppress it."""

    import os
    import subprocess as subprocess_module

    if os.name != "nt":
        pytest.skip("CREATE_NO_WINDOW is a Windows-only subprocess flag")

    captured_kwargs = []

    class _FakeCompleted:
        stdout = "ok\n"
        stderr = ""
        returncode = 0

    def fake_run(args, **kwargs):
        captured_kwargs.append(kwargs)
        return _FakeCompleted()

    monkeypatch.setattr("ldmanager.adb.subprocess.run", fake_run)

    runner = SubprocessAdbRunner(adb_path="adb")
    runner.list_devices()
    runner.run("127.0.0.1:5555", ["shell", "echo", "hi"])
    runner.capture_binary("127.0.0.1:5555", ["exec-out", "screencap", "-p"])

    assert len(captured_kwargs) == 3
    for kwargs in captured_kwargs:
        assert kwargs.get("creationflags") == subprocess_module.CREATE_NO_WINDOW


def test_subprocess_adb_runner_capture_binary_invokes_scoped_argv(monkeypatch):
    captured = {}

    class _FakeCompleted:
        stdout = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8
        stderr = b""
        returncode = 0

    def fake_run(args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return _FakeCompleted()

    monkeypatch.setattr("ldmanager.adb.subprocess.run", fake_run)

    runner = SubprocessAdbRunner(adb_path="adb")
    result = runner.capture_binary("127.0.0.1:5555", ["exec-out", "screencap", "-p"])

    assert captured["args"] == ["adb", "-s", "127.0.0.1:5555", "exec-out", "screencap", "-p"]
    assert captured["kwargs"]["text"] is False  # binary mode: bytes, no decoding
    assert result.ok
    assert result.stdout_bytes.startswith(b"\x89PNG")


def test_subprocess_adb_runner_capture_binary_requires_serial_before_spawning(monkeypatch):
    def fail_if_called(*args, **kwargs):  # pragma: no cover
        raise AssertionError("subprocess.run must not be called for an empty serial")

    monkeypatch.setattr("ldmanager.adb.subprocess.run", fail_if_called)

    runner = SubprocessAdbRunner(adb_path="adb")
    with pytest.raises(ValueError):
        runner.capture_binary("", ["exec-out", "screencap", "-p"])


def test_capture_binary_argv_for_two_serials_does_not_overlap():
    cmd1 = build_adb_command("adb", "SERIAL-A", ["exec-out", "screencap", "-p"])
    cmd2 = build_adb_command("adb", "SERIAL-B", ["exec-out", "screencap", "-p"])
    assert cmd1 != cmd2
    assert "SERIAL-A" in cmd1 and "SERIAL-A" not in cmd2
    assert "SERIAL-B" in cmd2 and "SERIAL-B" not in cmd1


def test_fake_runner_capture_calls_are_scoped_per_serial_and_separate_from_run_calls():
    runner = FakeAdbRunner()
    runner.run("SERIAL-A", ["shell", "input", "tap", "1", "2"])
    runner.capture_binary("SERIAL-A", ["exec-out", "screencap", "-p"])
    runner.capture_binary("SERIAL-B", ["exec-out", "screencap", "-p"])

    assert runner.calls == [("SERIAL-A", ("shell", "input", "tap", "1", "2"))]
    assert runner.capture_calls == [
        ("SERIAL-A", ("exec-out", "screencap", "-p")),
        ("SERIAL-B", ("exec-out", "screencap", "-p")),
    ]


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


# --- InputGateAdbRunner: real taps refused outside live mode (REL-UPDATE-003) --
#
# Found unused/unwired during v1.0.1 candidate diff inspection (defined in
# adb.py but never instantiated anywhere -- app.py wired the raw
# SubprocessAdbRunner directly, so a verified Start could already send real
# taps with no separate live-mode opt-in). Wired into app.py's
# build_controller() as part of REL-UPDATE-003; these are the missing unit
# tests for the gate class itself.


def test_input_gate_blocks_run_by_default():
    inner = FakeAdbRunner()
    gate = InputGateAdbRunner(inner)

    assert gate.live_enabled is False
    result = gate.run("SERIAL-A", ["shell", "input", "tap", "1", "2"])

    assert result.ok is False
    assert inner.calls == []  # the tap never reached the inner runner


def test_input_gate_allows_list_devices_and_capture_regardless_of_live_mode():
    inner = FakeAdbRunner(devices_output="List of devices attached\n")
    gate = InputGateAdbRunner(inner)  # live_enabled=False (default)

    assert gate.list_devices() == "List of devices attached\n"
    gate.capture_binary("SERIAL-A", ["exec-out", "screencap", "-p"])

    assert inner.list_devices_calls == 1
    assert inner.capture_calls == [("SERIAL-A", ("exec-out", "screencap", "-p"))]


def test_input_gate_allows_run_once_constructed_live():
    inner = FakeAdbRunner()
    gate = InputGateAdbRunner(inner, live_enabled=True)

    result = gate.run("SERIAL-A", ["shell", "input", "tap", "1", "2"])

    assert result.ok is True
    assert inner.calls == [("SERIAL-A", ("shell", "input", "tap", "1", "2"))]


def test_input_gate_set_live_enabled_toggles_at_runtime():
    inner = FakeAdbRunner()
    gate = InputGateAdbRunner(inner)

    gate.run("SERIAL-A", ["shell", "true"])
    assert inner.calls == []  # still blocked

    gate.set_live_enabled(True)
    gate.run("SERIAL-A", ["shell", "true"])
    assert inner.calls == [("SERIAL-A", ("shell", "true"))]

    gate.set_live_enabled(False)
    gate.run("SERIAL-A", ["shell", "true"])
    assert inner.calls == [("SERIAL-A", ("shell", "true"))]  # no new call while blocked


def test_input_gate_still_validates_serial_even_when_blocked():
    gate = InputGateAdbRunner(FakeAdbRunner())
    with pytest.raises(ValueError):
        gate.run("", ["shell", "true"])


# --- set_adb_path() / resolve_adb_path() live update (ADB-PATH-001) --------


def test_subprocess_runner_set_adb_path_re_resolves(tmp_path):
    real_exe = tmp_path / "adb.exe"
    real_exe.write_bytes(b"")
    runner = SubprocessAdbRunner(adb_path=None)  # starts on auto-detect ("adb")

    runner.set_adb_path(str(real_exe))

    assert runner.adb_path == str(real_exe)


def test_subprocess_runner_set_adb_path_keeps_explicit_value_when_missing():
    runner = SubprocessAdbRunner(adb_path=None)
    runner.set_adb_path("C:/does/not/exist/adb.exe")
    # resolve_adb_path() never silently invents a *different* path for a
    # missing explicit candidate -- it returns that candidate verbatim
    # (so a later subprocess call fails honestly against the path the
    # user actually configured, not a swapped-in "adb").
    assert runner.adb_path == "C:/does/not/exist/adb.exe"


def test_input_gate_set_adb_path_passes_through_to_inner(tmp_path):
    real_exe = tmp_path / "adb.exe"
    real_exe.write_bytes(b"")
    inner = SubprocessAdbRunner(adb_path=None)
    gate = InputGateAdbRunner(inner)

    gate.set_adb_path(str(real_exe))

    assert inner.adb_path == str(real_exe)
    assert gate.adb_path == str(real_exe)


def test_input_gate_set_adb_path_is_a_safe_noop_for_a_runner_without_it():
    class _BareRunner:
        """A minimal AdbRunner double with neither ``set_adb_path`` nor
        ``adb_path`` -- unlike FakeAdbRunner (which now mirrors both, for
        the GUI's ADB-PATH-001 tests), this stands in for a hypothetical
        runner implementation that never added them."""

        def list_devices(self):
            return ""

        def run(self, serial, args):
            raise NotImplementedError

        def capture_binary(self, serial, args):
            raise NotImplementedError

    gate = InputGateAdbRunner(_BareRunner())
    gate.set_adb_path("C:/whatever/adb.exe")  # must not raise
    assert gate.adb_path is None  # the inner runner has no .adb_path attribute
