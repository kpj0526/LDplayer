"""PyInstaller entry point (MVP-001).

Deliberately NOT part of the ``ldmanager`` package: PyInstaller treats
whatever script it's pointed at as ``__main__`` with no package
context, so pointing it directly at ``src/ldmanager/app.py`` breaks
that module's internal relative imports (``from .config import ...``)
with "attempted relative import with no known parent package". This
tiny wrapper uses an absolute import instead, which works identically
frozen (built by PyInstaller) and unfrozen (``python
scripts/entrypoint.py``). Normal development/`python -m ldmanager.app`
usage is unaffected by this file either way.
"""

from __future__ import annotations

import sys
from pathlib import Path

if not getattr(sys, "frozen", False):
    # Unfrozen: make the sibling src/ directory importable, mirroring
    # what `--paths src` gives PyInstaller during a build.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ldmanager.app import main  # noqa: E402  (import after sys.path setup)

if __name__ == "__main__":
    raise SystemExit(main())
