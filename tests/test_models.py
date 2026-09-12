from ldmanager.models import Account, AccountId, AccountState, create_default_accounts


def test_account_ids_cover_ld1_to_ld9():
    ids = [member.value for member in AccountId]
    assert ids == [f"LD{i}" for i in range(1, 10)]


def test_account_default_state_is_unknown():
    account = Account(id=AccountId.LD1)
    assert account.state is AccountState.UNKNOWN
    assert account.adb_serial is None


def test_create_default_accounts_has_nine_entries_all_unknown():
    accounts = create_default_accounts()
    assert set(accounts.keys()) == set(AccountId)
    assert len(accounts) == 9
    for account_id, account in accounts.items():
        assert account.id is account_id
        assert account.state is AccountState.UNKNOWN
        assert account.adb_serial is None
