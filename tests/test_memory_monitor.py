from concurrent.futures import ThreadPoolExecutor
import csv

from ldmanager.memory_monitor import CallMetrics, MemoryMonitor
from ldmanager.adb import SubprocessAdbRunner
from ldmanager.capture_backends import HybridCaptureAdbRunner


def test_preflight_and_runtime_counts_are_atomic_and_thread_local():
    metrics = CallMetrics()
    def record(probe):
        if probe:
            with metrics.preflight():
                for _ in range(100):
                    metrics.record_capture()
        else:
            for _ in range(100):
                metrics.record_capture()
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(record, [True, False, True, False]))
    result = metrics.snapshot()
    assert result["adb_capture_calls"] == 400
    assert result["adb_preflight_captures"] == result["adb_runtime_captures"] == 200


def test_counter_measures_actual_adb_boundary_even_on_launch_failure(monkeypatch):
    metrics = CallMetrics()
    runner = SubprocessAdbRunner(metrics=metrics)
    router = HybridCaptureAdbRunner(runner, metrics)
    def fail(*args, **kwargs):
        raise FileNotFoundError("missing adb")
    monkeypatch.setattr("ldmanager.adb.subprocess.run", fail)
    import pytest
    with pytest.raises(FileNotFoundError):
        router.preflight_capture_binary("a", ("exec-out", "screencap", "-p"))
    assert metrics.snapshot()["adb_preflight_captures"] == 1
    assert metrics.snapshot()["adb_runtime_captures"] == 0
    assert metrics.snapshot()["adb_process_starts"] == 1


def test_csv_records_commit_and_calls_without_dividing_by_zero(tmp_path):
    metrics = CallMetrics()
    current = {"commit_bytes": 1000, "commit_limit_bytes": 10000,
               "kernel_paged_bytes": 5, "kernel_nonpaged_bytes": 6}
    process = {"pid": 123, "name": "dnplayer.exe", "group": "ldplayer", "created_at": 1,
               "private_bytes": 333, "working_set_bytes": 222, "error": ""}
    monitor = MemoryMonitor(metrics, root=tmp_path, system_reader=lambda: dict(current),
                            process_reader=lambda: [process])
    first = monitor.sample()
    assert first["commit_delta_per_1000_adb_captures"] is None
    with metrics.preflight():
        metrics.record_capture()
    current["commit_bytes"] = 1100
    second = monitor.sample()
    assert second["commit_delta_per_1000_adb_captures"] == 100000
    assert second["ldplayer_private_bytes"] == 333
    assert second["adb_runtime_captures"] == 0
    third = monitor.sample()
    assert third["commit_delta_per_1000_adb_captures"] is None
    with (monitor.directory / "summary.csv").open(encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 3 and rows[-1]["commit_bytes"] == "1100"
    with (monitor.directory / "processes.csv").open(encoding="utf-8-sig") as stream:
        assert len(list(csv.DictReader(stream))) == 3


def test_missing_system_counter_is_reported_not_a_fake_zero(tmp_path):
    def failed():
        raise OSError("unavailable")
    monitor = MemoryMonitor(CallMetrics(), root=tmp_path, system_reader=failed, process_reader=lambda: [])
    row = monitor.sample()
    assert row["commit_bytes"] is None
    assert "unavailable" in row["error"]


def test_monitor_thread_stops_and_writes_final_snapshot(tmp_path):
    monitor = MemoryMonitor(CallMetrics(), root=tmp_path, interval=0.01,
                            system_reader=lambda: {}, process_reader=lambda: [])
    monitor.start()
    monitor.close()
    assert not monitor._thread.is_alive()
    assert (monitor.directory / "summary.csv").is_file()
