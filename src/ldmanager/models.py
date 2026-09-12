"""Domain model skeleton for LDPlayer accounts (TP-001 stage 1).

This module only defines data shapes and safe default state. It performs
no I/O, no ADB calls, and no automation of any kind.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class AccountId(str, Enum):
    """Fixed identifiers for the nine managed LDPlayer instances."""

    LD1 = "LD1"
    LD2 = "LD2"
    LD3 = "LD3"
    LD4 = "LD4"
    LD5 = "LD5"
    LD6 = "LD6"
    LD7 = "LD7"
    LD8 = "LD8"
    LD9 = "LD9"


class AccountState(str, Enum):
    """Lifecycle state of a managed account/instance.

    UNKNOWN is the safe default: the manager has not yet observed or
    connected to the instance, so no assumption is made about it.
    """

    UNKNOWN = "unknown"
    OFFLINE = "offline"
    STARTING = "starting"
    ONLINE = "online"
    BUSY = "busy"
    ERROR = "error"
    STOPPING = "stopping"


@dataclass
class Account:
    """A single LD1~LD9 account/instance record.

    ``adb_serial`` is intentionally left as ``None`` by default. Stage 1
    never guesses or hardcodes an ADB host:port — it must be supplied by
    configuration in a later stage.
    """

    id: AccountId
    state: AccountState = AccountState.UNKNOWN
    adb_serial: Optional[str] = None
    label: Optional[str] = None
    metadata: dict = field(default_factory=dict)


def create_default_accounts() -> dict[AccountId, Account]:
    """Build the default LD1~LD9 account registry.

    Every account starts in ``AccountState.UNKNOWN`` with no ADB serial
    assigned. Nothing here contacts an emulator, ADB server, or network.
    """

    return {account_id: Account(id=account_id) for account_id in AccountId}
