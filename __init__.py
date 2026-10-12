"""project-initials plugin: prefix automatic session titles with the owning project's initials.

Uses the ``transform_session_title`` hook only (fired just before an automatic title is stored); it
patches nothing in Hermes. Names a user types (``/title``, sidebar rename) never pass through the hook.
Any failure is logged at debug level and the title is stored unchanged.
"""

from __future__ import annotations

import logging

from . import core, projects

logger = logging.getLogger(__name__)


def _setting(ctx, key, default):
    try:
        value = ctx.get_config(key, default=default)
    except Exception:
        return default
    return default if value is None else value


def make_hook(ctx):
    def transform_session_title(title=None, cwd=None, **_kwargs):
        if not title or not cwd:
            return None
        try:
            project, names = projects.lookup(cwd)
            if not project:
                return None
            initials = core.initials_map(names, bool(_setting(ctx, "derive_missing", False)))
            out = core.prefixed_title(
                title,
                project,
                initials,
                uppercase=bool(_setting(ctx, "uppercase", True)),
                max_words=int(_setting(ctx, "max_words", 0) or 0),
                drop_project_words=bool(_setting(ctx, "drop_project_words", False)),
            )
            return out if out != title else None
        except Exception:
            logger.debug("project-initials: left %r unchanged", title, exc_info=True)
            return None

    return transform_session_title


def register(ctx) -> None:
    ctx.register_hook("transform_session_title", make_hook(ctx))
