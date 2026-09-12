"""Diagnostic screenshot path/metadata scaffolding (TP-001 stage 2).

This stage only prepares *where* a future screenshot would live and
records the intent as a small JSON sidecar. It never calls ADB, never
captures pixels, and never writes image bytes — real capture is
explicitly deferred to a later stage per the TP-001 stage 2 directive.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .models import AccountId
from .paths import ensure_safe_subdir, sanitize_filename

DEFAULT_SCREENSHOT_DIR = Path("diagnostics") / "screenshots"

STATUS_PENDING_CAPTURE = "pending_capture"


@dataclass(frozen=True)
class DiagnosticsSettings:
    """Where diagnostic artifacts (screenshots, sidecars) are rooted."""

    screenshot_dir: Path = DEFAULT_SCREENSHOT_DIR


@dataclass
class ScreenshotRequest:
    """Describes an intended, not-yet-captured diagnostic screenshot."""

    account_id: AccountId
    requested_at: datetime
    reason: Optional[str]
    image_path: Path
    metadata_path: Path
    status: str = STATUS_PENDING_CAPTURE

    def to_json_dict(self) -> dict:
        return {
            "account_id": self.account_id.value,
            "requested_at": self.requested_at.isoformat(),
            "reason": self.reason,
            "image_path": str(self.image_path),
            "status": self.status,
        }


def _timestamp_slug(moment: datetime) -> str:
    return moment.strftime("%Y%m%dT%H%M%SZ")


def build_screenshot_request(
    account_id: AccountId,
    settings: Optional[DiagnosticsSettings] = None,
    *,
    reason: Optional[str] = None,
    moment: Optional[datetime] = None,
) -> ScreenshotRequest:
    """Compute a safe, unique, not-yet-existing path for a future screenshot.

    Pure path/metadata computation: no file or directory is created and
    no ADB call is made.
    """

    settings = settings or DiagnosticsSettings()
    moment = moment or datetime.now(timezone.utc)

    account_dir = ensure_safe_subdir(settings.screenshot_dir, account_id.value)
    slug = _timestamp_slug(moment)
    unique = uuid.uuid4().hex[:8]
    name_parts = [slug, unique]
    if reason:
        reason_part = sanitize_filename(reason, default="")
        if reason_part:
            name_parts.append(reason_part)
    base_name = "_".join(name_parts)

    return ScreenshotRequest(
        account_id=account_id,
        requested_at=moment,
        reason=reason,
        image_path=account_dir / f"{base_name}.png",
        metadata_path=account_dir / f"{base_name}.json",
    )


def write_metadata_sidecar(request: ScreenshotRequest) -> Path:
    """Persist ``request`` as a JSON sidecar next to the future image.

    Only the metadata is written — never image bytes, since capture is
    out of scope for this stage.
    """

    request.metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with request.metadata_path.open("w", encoding="utf-8") as handle:
        json.dump(request.to_json_dict(), handle, ensure_ascii=False, indent=2)
    return request.metadata_path
