import pytest

from ldmanager.discovery import (
    ConnectionStatus,
    InvalidAdbMappingError,
    MappingIssue,
    build_account_connection_statuses,
    ensure_complete_adb_mapping,
    validate_complete_adb_mapping,
)
from ldmanager.models import AccountId
from tests.fakes import BrokenAdbRunner, FakeAdbRunner


def _nine_mapping():
    return {f"LD{i}": f"127.0.0.1:{5555 + i}" for i in range(1, 10)}


def _devices_output(*rows):
    lines = ["List of devices attached"]
    lines.extend(f"{serial}\t{state}" for serial, state in rows)
    return "\n".join(lines) + "\n"


# --- validate_complete_adb_mapping / ensure_complete_adb_mapping --------


def test_valid_nine_mapping_has_no_issues():
    assert validate_complete_adb_mapping(_nine_mapping()) == []


def test_missing_account_is_rejected():
    mapping = _nine_mapping()
    mapping["LD1"] = None
    issues = validate_complete_adb_mapping(mapping)
    assert any(i.issue is MappingIssue.MISSING_ACCOUNT for i in issues)


def test_duplicate_serial_is_rejected():
    mapping = _nine_mapping()
    mapping["LD2"] = mapping["LD1"]
    issues = validate_complete_adb_mapping(mapping)
    assert any(i.issue is MappingIssue.DUPLICATE_SERIAL for i in issues)


def test_too_few_accounts_is_rejected():
    mapping = _nine_mapping()
    del mapping["LD9"]
    issues = validate_complete_adb_mapping(mapping)
    assert any(i.issue is MappingIssue.WRONG_ACCOUNT_COUNT for i in issues)


def test_too_many_accounts_is_rejected():
    mapping = _nine_mapping()
    mapping["LD10"] = "127.0.0.1:9999"
    issues = validate_complete_adb_mapping(mapping)
    assert any(i.issue is MappingIssue.WRONG_ACCOUNT_COUNT for i in issues)


def test_ensure_complete_adb_mapping_raises_on_invalid():
    mapping = _nine_mapping()
    mapping["LD1"] = None
    with pytest.raises(InvalidAdbMappingError):
        ensure_complete_adb_mapping(mapping)


def test_ensure_complete_adb_mapping_passes_silently_when_valid():
    ensure_complete_adb_mapping(_nine_mapping())  # must not raise


def test_invalid_mapping_error_message_has_no_secrets_just_structure():
    mapping = _nine_mapping()
    mapping["LD1"] = None
    try:
        ensure_complete_adb_mapping(mapping)
    except InvalidAdbMappingError as exc:
        assert exc.errors and exc.errors[0].issue is MappingIssue.MISSING_ACCOUNT
        assert "LD1" in str(exc)
    else:
        pytest.fail("expected InvalidAdbMappingError")


# --- build_account_connection_statuses -----------------------------------


def test_all_nine_mapped_and_online_are_ok():
    mapping = _nine_mapping()
    rows = [(serial, "device") for serial in mapping.values()]
    runner = FakeAdbRunner(devices_output=_devices_output(*rows))

    statuses = build_account_connection_statuses(mapping, runner)

    assert len(statuses) == 9
    assert all(s.status is ConnectionStatus.OK for s in statuses)
    assert {s.account_id for s in statuses} == set(AccountId)


def test_unmapped_account_reports_unmapped_without_touching_adb():
    mapping = _nine_mapping()
    mapping["LD3"] = None
    runner = FakeAdbRunner(devices_output=_devices_output())

    statuses = {s.account_id: s for s in build_account_connection_statuses(mapping, runner)}

    assert statuses[AccountId.LD3].status is ConnectionStatus.UNMAPPED
    assert statuses[AccountId.LD3].serial is None


def test_offline_unauthorized_and_missing_device_are_distinguished():
    mapping = _nine_mapping()
    rows = [
        (mapping["LD1"], "device"),
        (mapping["LD2"], "offline"),
        (mapping["LD3"], "unauthorized"),
        # LD4's configured serial is deliberately absent from discovery.
    ]
    rows.extend((mapping[f"LD{i}"], "device") for i in range(5, 10))
    runner = FakeAdbRunner(devices_output=_devices_output(*rows))

    statuses = {s.account_id: s for s in build_account_connection_statuses(mapping, runner)}

    assert statuses[AccountId.LD1].status is ConnectionStatus.OK
    assert statuses[AccountId.LD2].status is ConnectionStatus.DEVICE_OFFLINE
    assert statuses[AccountId.LD3].status is ConnectionStatus.DEVICE_UNAUTHORIZED
    assert statuses[AccountId.LD4].status is ConnectionStatus.DEVICE_NOT_FOUND
    assert statuses[AccountId.LD4].serial == mapping["LD4"]


def test_unknown_or_malformed_device_state_is_reported_distinctly():
    mapping = _nine_mapping()
    rows = [(mapping["LD1"], "qwerty")]  # unrecognized/malformed state token
    rows.extend((mapping[f"LD{i}"], "device") for i in range(2, 10))
    runner = FakeAdbRunner(devices_output=_devices_output(*rows))

    statuses = {s.account_id: s for s in build_account_connection_statuses(mapping, runner)}
    assert statuses[AccountId.LD1].status is ConnectionStatus.DEVICE_STATE_UNKNOWN


def test_discovery_never_auto_assigns_unmapped_account_even_if_a_device_is_present():
    mapping = _nine_mapping()
    mapping["LD5"] = None
    # A device is visible over ADB, but nothing maps LD5 to it.
    runner = FakeAdbRunner(devices_output=_devices_output(("127.0.0.1:9999", "device")))

    statuses = {s.account_id: s for s in build_account_connection_statuses(mapping, runner)}

    assert statuses[AccountId.LD5].status is ConnectionStatus.UNMAPPED
    assert statuses[AccountId.LD5].serial is None
    # And the visible-but-unmapped device is not attributed to any account.
    assert all(s.serial != "127.0.0.1:9999" for s in statuses.values())


def test_discovery_unavailable_is_reported_per_account_without_crashing():
    mapping = _nine_mapping()
    statuses = build_account_connection_statuses(mapping, BrokenAdbRunner("adb not found"))

    assert len(statuses) == 9
    assert all(s.status is ConnectionStatus.DISCOVERY_UNAVAILABLE for s in statuses)
    assert all(isinstance(s.detail, str) and s.detail for s in statuses)


def test_malformed_non_string_discovery_result_is_handled_safely():
    class WeirdRunner:
        def list_devices(self):
            return None  # not a string; must not crash parsing

        def run(self, serial, args):  # pragma: no cover - unused
            raise NotImplementedError

    mapping = _nine_mapping()
    statuses = build_account_connection_statuses(mapping, WeirdRunner())
    assert all(s.status is ConnectionStatus.DISCOVERY_UNAVAILABLE for s in statuses)


def test_incomplete_mapping_still_produces_per_account_statuses_not_a_crash():
    # A non-nine / partially-null mapping (invalid per
    # validate_complete_adb_mapping) must still be safely reportable
    # per account rather than raising.
    mapping = _nine_mapping()
    mapping["LD1"] = None
    mapping["LD2"] = mapping["LD3"]  # duplicate
    runner = FakeAdbRunner(devices_output=_devices_output((mapping["LD3"], "device")))

    statuses = build_account_connection_statuses(mapping, runner)
    assert len(statuses) == 9
    by_id = {s.account_id: s for s in statuses}
    assert by_id[AccountId.LD1].status is ConnectionStatus.UNMAPPED
