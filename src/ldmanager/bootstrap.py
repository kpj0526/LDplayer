"""First-run config bootstrap (REL-0.1.0-PKG-01).

A packaged distribution (built by ``scripts/build_windows.ps1``) ships
``configs/*.example.yaml`` next to the executable, but never a real
``configs/config.yaml``/``configs/bounty.yaml`` — those stay the
user's own, git-ignored, never-committed files, exactly as in the
source checkout. Without this module, a customer double-clicking
``ldmanager.exe`` for the first time on a freshly extracted ZIP would
just get a "config not found" console error and no GUI at all.

:func:`bootstrap_default_configs` copies each ``*.example.yaml`` to its
real counterpart — but **only if the real file does not already
exist**; it never overwrites an existing (possibly user-edited)
config. The copied files are byte-identical to the shipped examples:
every ``adb_mapping`` entry is ``null`` (nothing guessed) and neither
example file contains any credential (both already pass
``config.py``'s/``bounty_config.py``'s own validation, unmodified,
before and after the copy — see ``tests/test_config.py``/
``tests/test_bounty_config.py``).

No ADB call, no worker, and no GUI code lives here — this module only
ever copies two small YAML files, and only when they're missing.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import List

from .bounty_config import resolve_bounty_config_path
from .config import resolve_config_path


def app_base_dir() -> Path:
    """Where bundled ``*.example.yaml`` files live relative to the
    running app.

    - Frozen (PyInstaller, ``sys.frozen`` set): the directory containing
      the executable — matching how ``scripts/build_windows.ps1`` places
      ``configs/*.example.yaml`` and ``templates/`` as siblings of
      ``ldmanager.exe``, and how Windows sets a double-clicked exe's
      working directory to its own folder.
    - Unfrozen (running from source): the current working directory —
      matching how :func:`ldmanager.config.resolve_config_path` and
      :func:`ldmanager.bounty_config.resolve_bounty_config_path` already
      resolve their own CWD-relative defaults, so a normal
      ``python -m ldmanager.app`` run from the repo root stays
      consistent with this module.
    """

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path.cwd()


def bootstrap_default_configs() -> List[str]:
    """Create ``configs/config.yaml``/``configs/bounty.yaml`` from their
    ``.example.yaml`` counterparts, one at a time, only where the real
    file is missing.

    Returns a list of human-readable messages describing what (if
    anything) was created, for the caller to print/log — an empty list
    means nothing needed to be done (both files already existed, or no
    bundled example was found to bootstrap from). Never raises: a
    missing example file is silently skipped, leaving
    :func:`ldmanager.config.load_config`/
    :func:`ldmanager.bounty_config.load_bounty_config` to raise their
    own normal, clear "file not found" error afterward, unchanged.
    """

    messages: List[str] = []
    example_base = app_base_dir()

    for resolver, example_name in (
        (resolve_config_path, "config.example.yaml"),
        (resolve_bounty_config_path, "bounty.example.yaml"),
    ):
        target = resolver()
        if target.exists():
            continue  # never overwrite an existing (possibly user-edited) file

        example = example_base / "configs" / example_name
        if not example.is_file():
            continue  # nothing bundled to bootstrap from

        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(example, target)
        messages.append(
            f"First run: created {target} from {example_name} "
            "(safe defaults -- no ADB mapping, no credentials). "
            "Use the GUI's 'Refresh ADB devices' + per-account Save to register your instances."
        )

    return messages
