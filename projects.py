"""Read-only lookup of the project that owns a working directory.

The only module that touches Hermes' project store, so the rule in ``core`` stays testable offline.
Nothing here writes: no project is created, renamed or archived.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


def lookup(cwd: str) -> Tuple[Optional[str], List[str]]:
    """``(name of the project owning cwd or None, names of all projects, archived included)``."""
    from hermes_cli import projects_db as pdb

    with pdb.connect_closing() as conn:
        owner = pdb.project_for_path(conn, cwd, include_archived=True) if cwd else None
        names = [p.name for p in pdb.list_projects(conn, include_archived=True)]
    return (owner.name if owner else None), names
