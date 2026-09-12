"""Minimal CLI entry point skeleton (TP-001 stage 1).

This only loads configuration and prints the default account registry.
It does not start, stop, or otherwise control any LDPlayer instance,
handle credentials, touch a web page's DOM, or move the mouse.
"""

from __future__ import annotations

import sys

from .config import ConfigError, load_config
from .models import create_default_accounts


def main(argv: list[str] | None = None) -> int:
    """Print resolved config + default account states, then exit.

    Later stages will replace/extend this with real subcommands.
    """

    del argv  # unused in this stage; kept for a future argparse wire-up

    accounts = create_default_accounts()
    print("ldmanager stage-1 skeleton")
    print("Default accounts (state is always UNKNOWN until later stages wire in real checks):")
    for account_id, account in accounts.items():
        print(f"  {account_id.value}: state={account.state.value} adb_serial={account.adb_serial!r}")

    try:
        config = load_config()
    except ConfigError as exc:
        print(f"\nConfig not loaded: {exc}", file=sys.stderr)
        return 0

    print("\nLoaded adb_mapping:")
    for key, value in config.adb_mapping.items():
        print(f"  {key}: {value!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
