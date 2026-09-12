import json
from datetime import datetime, timezone

from ldmanager.diagnostics import (
    DiagnosticsSettings,
    build_screenshot_request,
    write_metadata_sidecar,
)
from ldmanager.models import AccountId


def test_build_screenshot_request_does_not_touch_filesystem(tmp_path):
    settings = DiagnosticsSettings(screenshot_dir=tmp_path / "shots")
    request = build_screenshot_request(AccountId.LD1, settings, reason="login check")

    assert request.status == "pending_capture"
    assert request.image_path.suffix == ".png"
    assert request.image_path.parent == tmp_path / "shots" / "LD1"
    assert not request.image_path.exists()
    assert not settings.screenshot_dir.exists()


def test_requests_for_different_accounts_are_isolated(tmp_path):
    settings = DiagnosticsSettings(screenshot_dir=tmp_path / "shots")
    r1 = build_screenshot_request(AccountId.LD1, settings)
    r2 = build_screenshot_request(AccountId.LD2, settings)
    assert r1.image_path.parent != r2.image_path.parent


def test_repeated_requests_for_same_account_get_unique_paths(tmp_path):
    settings = DiagnosticsSettings(screenshot_dir=tmp_path / "shots")
    moment = datetime(2026, 1, 1, tzinfo=timezone.utc)
    r1 = build_screenshot_request(AccountId.LD1, settings, moment=moment)
    r2 = build_screenshot_request(AccountId.LD1, settings, moment=moment)
    assert r1.image_path != r2.image_path


def test_metadata_sidecar_written_without_image_bytes(tmp_path):
    settings = DiagnosticsSettings(screenshot_dir=tmp_path / "shots")
    moment = datetime(2026, 1, 1, tzinfo=timezone.utc)
    request = build_screenshot_request(AccountId.LD4, settings, reason="check", moment=moment)

    path = write_metadata_sidecar(request)

    assert path.exists()
    assert not request.image_path.exists()

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["account_id"] == "LD4"
    assert data["status"] == "pending_capture"
    assert data["reason"] == "check"
    assert data["requested_at"].startswith("2026-01-01")


def test_reason_is_sanitized_in_filename(tmp_path):
    settings = DiagnosticsSettings(screenshot_dir=tmp_path / "shots")
    request = build_screenshot_request(AccountId.LD1, settings, reason="../../etc/passwd")
    assert ".." not in str(request.image_path)
    assert request.image_path.parent == tmp_path / "shots" / "LD1"
