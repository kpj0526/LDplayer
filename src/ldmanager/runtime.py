"""Per-account persistent mission state and verified ADB click primitive."""
from __future__ import annotations
import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

from .adb import AdbRunner
from .coordinates import RelativeCoordinate, RelativeRegion, ScreenSize, build_tap_args
from .recognition import Recognizer
from .screenshot import capture_screenshot


class SlotState(str, Enum):
    UNKNOWN = "unknown"
    TARGET_LOCKED = "target_locked"
    NON_TARGET = "non_target"
    ERROR = "error"


class VerificationError(str, Enum):
    STOPPED = "stopped"
    STALE_SCREEN = "stale_screen"
    UNKNOWN_SCREEN = "unknown_screen"
    ADB_ERROR = "adb_error"


@dataclass
class AccountMissionRuntime:
    slots: list[SlotState] = field(default_factory=lambda: [SlotState.UNKNOWN] * 5)
    # The next configuration pass revisits the row whose completed
    # reward/result popup was just closed, then continues downward.
    next_slot_index: int = 1
    # One completed-target slot is checked per waiting cycle.  Keeping this
    # cursor per account prevents five LD rows from being selected/captured
    # on every poll pass, while still rotating through all five fairly.
    next_progress_slot_index: int = 1
    phase: str = "IDLE"
    last_template: str = ""
    last_score: float = 0.0
    last_action: str = ""
    last_error: str = ""
    error_capture: Optional[Path] = None

    @property
    def locked_count(self) -> int:
        return sum(slot is SlotState.TARGET_LOCKED for slot in self.slots)

    @property
    def configured(self) -> bool:
        return self.locked_count == 5

    def reset_after_verified_return(self, *, completed_slot_index: int) -> None:
        """Forget only the claimed row; other accepted targets are unchanged.

        Claiming one reward replaces that row's mission, not the other four.
        Clearing every lock would re-evaluate their N/200 progress as if it
        were a new 0/200 mission and could refresh a valid target.
        """
        if not 1 <= completed_slot_index <= len(self.slots):
            raise ValueError("Completed slot index is outside the mission list")
        self.slots[completed_slot_index - 1] = SlotState.UNKNOWN
        self.next_slot_index = completed_slot_index
        self.next_progress_slot_index = completed_slot_index
        self.phase = "CONFIGURING"


def click_and_verify(*, runner: AdbRunner, serial: str, screen: ScreenSize,
                     point: RelativeCoordinate, recognizer: Recognizer,
                     expected_label: str, expected_roi: RelativeRegion,
                     threshold: float, should_stop: Callable[[], bool],
                     attempts: int = 3, diagnostics_dir: Path = Path("diagnostics/errors")) -> Optional[VerificationError]:
    """Capture, tap, then require the expected next template or a changed ROI.
    Returns ``None`` only on verified success; never issues input after Stop."""
    before = capture_screenshot(runner, serial)
    if not before.ok:
        return VerificationError.ADB_ERROR
    if should_stop():
        return VerificationError.STOPPED
    tap = runner.run(serial, build_tap_args(screen, point))
    if not tap.ok:
        return VerificationError.ADB_ERROR
    before_hash = hashlib.sha256(before.image_bytes).digest()
    for _ in range(attempts):
        if should_stop():
            return VerificationError.STOPPED
        after = capture_screenshot(runner, serial)
        if not after.ok:
            return VerificationError.ADB_ERROR
        match = recognizer.recognize(after.image_bytes, expected_roi, expected_label, threshold)
        if match.matched:
            return None
        if hashlib.sha256(after.image_bytes).digest() == before_hash:
            continue
        diagnostics_dir.mkdir(parents=True, exist_ok=True)
        path = diagnostics_dir / f"{serial.replace(':', '_')}-{int(time.time())}.png"
        path.write_bytes(after.image_bytes)
        return VerificationError.UNKNOWN_SCREEN
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    path = diagnostics_dir / f"{serial.replace(':', '_')}-{int(time.time())}.png"
    path.write_bytes(before.image_bytes)
    return VerificationError.STALE_SCREEN
