"""LD1~LD9 discovery + explicit mapping validation (TP-002 stage 3).

Two independent checks, both required before any real connection would
ever be attempted (actual connection is out of scope for this stage):

1. :func:`validate_complete_adb_mapping` / :func:`ensure_complete_adb_mapping`
   check the *shape* of a config-supplied ``adb_mapping``: exactly
   LD1..LD9, each with a distinct, non-null serial. Pure — never touches
   ADB.

2. :func:`build_account_connection_statuses` cross-checks that mapping
   against what an injected :class:`~ldmanager.adb.AdbRunner` actually
   reports from `adb devices`, producing one secret-free, structured
   status per account.

Discovery only *reports* what ADB sees; it never assigns a discovered
serial to an account on its own — mapping is always explicit, from
config. No touch/tap/screenshot/login/reconnect/game action happens
here or anywhere in this stage.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .adb import AdbDeviceState, AdbRunner, parse_adb_devices_output
from .models import AccountId


class MappingIssue(str, Enum):
    """Why a config-level ``adb_mapping`` isn't a valid *complete* mapping.

    These are shape problems, checked before any ADB call is made —
    distinct from the per-account :class:`ConnectionStatus` values below,
    which come from cross-checking a (shape-valid) mapping against live
    discovery output.
    """

    WRONG_ACCOUNT_COUNT = "wrong_account_count"  # not exactly LD1..LD9
    MISSING_ACCOUNT = "missing_account"  # an LDx has no serial at all
    DUPLICATE_SERIAL = "duplicate_serial"  # same serial used for 2+ accounts


class ConnectionStatus(str, Enum):
    """Per-account status after cross-checking mapping against discovery."""

    OK = "ok"  # mapped, and the device is present with state DEVICE
    UNMAPPED = "unmapped"  # no serial configured for this account
    DEVICE_NOT_FOUND = "device_not_found"  # serial absent from `adb devices`
    DEVICE_OFFLINE = "device_offline"
    DEVICE_UNAUTHORIZED = "device_unauthorized"
    DEVICE_STATE_UNKNOWN = "device_state_unknown"  # malformed/unrecognized state
    DISCOVERY_UNAVAILABLE = "discovery_unavailable"  # runner/parse failure


@dataclass(frozen=True)
class MappingValidationError:
    """A structured, secret-free diagnostic for a mapping shape problem."""

    issue: MappingIssue
    detail: str


class InvalidAdbMappingError(ValueError):
    """Raised by :func:`ensure_complete_adb_mapping` for an invalid mapping."""

    def __init__(self, errors: list[MappingValidationError]) -> None:
        self.errors = errors
        summary = "; ".join(f"{e.issue.value}: {e.detail}" for e in errors)
        super().__init__(f"Invalid ADB mapping ({len(errors)} issue(s)): {summary}")


@dataclass(frozen=True)
class AccountConnectionStatus:
    """Per-account connection/mapping status + structured diagnostic.

    ``serial`` is an ADB target string (e.g. ``127.0.0.1:5555``), never a
    credential, so it is safe to include verbatim for diagnostics.
    """

    account_id: AccountId
    status: ConnectionStatus
    serial: Optional[str]
    detail: str


def validate_complete_adb_mapping(
    adb_mapping: dict[str, Optional[str]],
) -> list[MappingValidationError]:
    """Check that ``adb_mapping`` is a valid *complete* LD1..LD9 mapping.

    Requires exactly the nine ``AccountId`` keys, each with a distinct,
    non-null serial. Returns the list of issues found (empty == valid).
    Never touches ADB and never guesses a value.
    """

    errors: list[MappingValidationError] = []
    expected_keys = {account_id.value for account_id in AccountId}
    actual_keys = set(adb_mapping.keys())

    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        extra = sorted(actual_keys - expected_keys)
        errors.append(
            MappingValidationError(
                MappingIssue.WRONG_ACCOUNT_COUNT,
                f"Expected exactly {sorted(expected_keys)}; "
                f"missing={missing}, unexpected={extra}.",
            )
        )

    serial_owners: dict[str, list[str]] = {}
    for account_key in sorted(expected_keys & actual_keys):
        serial = adb_mapping.get(account_key)
        if serial is None:
            errors.append(
                MappingValidationError(
                    MappingIssue.MISSING_ACCOUNT,
                    f"{account_key} has no adb serial configured.",
                )
            )
            continue
        serial_owners.setdefault(serial, []).append(account_key)

    for serial, owners in sorted(serial_owners.items()):
        if len(owners) > 1:
            errors.append(
                MappingValidationError(
                    MappingIssue.DUPLICATE_SERIAL,
                    f"Serial is assigned to multiple accounts: {sorted(owners)}.",
                )
            )

    return errors


def ensure_complete_adb_mapping(adb_mapping: dict[str, Optional[str]]) -> None:
    """Raise :class:`InvalidAdbMappingError` unless the mapping is complete.

    Callers that are about to rely on a full LD1..LD9 -> serial mapping
    (e.g. a future connection flow) should call this first instead of
    assuming an incomplete or malformed mapping is usable.
    """

    errors = validate_complete_adb_mapping(adb_mapping)
    if errors:
        raise InvalidAdbMappingError(errors)


def discover_devices(runner: AdbRunner) -> tuple[list, Optional[str]]:
    """Run + parse `adb devices` via the injected ``runner``.

    Returns ``(devices, error)``: on any failure (runner exception, or a
    non-string result), returns ``([], "<short description>")`` instead
    of raising, so callers can surface ``DISCOVERY_UNAVAILABLE`` per
    account rather than crashing.
    """

    try:
        raw_output = runner.list_devices()
    except Exception as exc:
        return [], f"ADB device listing failed: {type(exc).__name__}"

    if not isinstance(raw_output, str):
        return [], "ADB device listing returned a non-text result."

    return parse_adb_devices_output(raw_output), None


def _status_for_device_state(state: AdbDeviceState) -> ConnectionStatus:
    if state is AdbDeviceState.DEVICE:
        return ConnectionStatus.OK
    if state is AdbDeviceState.OFFLINE:
        return ConnectionStatus.DEVICE_OFFLINE
    if state is AdbDeviceState.UNAUTHORIZED:
        return ConnectionStatus.DEVICE_UNAUTHORIZED
    return ConnectionStatus.DEVICE_STATE_UNKNOWN


def build_account_connection_statuses(
    adb_mapping: dict[str, Optional[str]],
    runner: AdbRunner,
) -> list[AccountConnectionStatus]:
    """Cross-check ``adb_mapping`` against live `adb devices` output.

    Produces exactly one status per ``AccountId`` (LD1..LD9), regardless
    of whether the mapping is "complete" — an unmapped account simply
    gets :attr:`ConnectionStatus.UNMAPPED` instead of raising. A device
    that is visible over ADB but not referenced by any account's
    configured serial is never auto-assigned to an unmapped account;
    discovery only reports, it never assigns.
    """

    devices, discovery_error = discover_devices(runner)
    devices_by_serial = {device.serial: device for device in devices}

    statuses: list[AccountConnectionStatus] = []
    for account_id in AccountId:
        serial = adb_mapping.get(account_id.value)

        if serial is None:
            statuses.append(
                AccountConnectionStatus(
                    account_id=account_id,
                    status=ConnectionStatus.UNMAPPED,
                    serial=None,
                    detail="No adb serial configured for this account.",
                )
            )
            continue

        if discovery_error is not None:
            statuses.append(
                AccountConnectionStatus(
                    account_id=account_id,
                    status=ConnectionStatus.DISCOVERY_UNAVAILABLE,
                    serial=serial,
                    detail=discovery_error,
                )
            )
            continue

        device = devices_by_serial.get(serial)
        if device is None:
            statuses.append(
                AccountConnectionStatus(
                    account_id=account_id,
                    status=ConnectionStatus.DEVICE_NOT_FOUND,
                    serial=serial,
                    detail="Configured serial not present in `adb devices` output.",
                )
            )
            continue

        status = _status_for_device_state(device.state)
        detail = (
            "Device present and authorized."
            if status is ConnectionStatus.OK
            else f"Device reported state {device.raw_state!r}."
        )
        statuses.append(
            AccountConnectionStatus(
                account_id=account_id,
                status=status,
                serial=serial,
                detail=detail,
            )
        )

    return statuses
