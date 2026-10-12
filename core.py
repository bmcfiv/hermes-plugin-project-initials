"""project-initials rule: sessions of a project start with that project's initials.

Pure logic with no Hermes imports, so it can be tested offline.

A project's initials are the trailing ``(xx)`` of its name, e.g. ``Billing Service (bs)``. A session
title that Hermes generates automatically then reads ``BS: Fix invoices``. Nothing stores the initials
anywhere else, so renaming a project in the sidebar changes the prefix of the titles written after it.

When ``derive_missing`` is on, a project whose name carries no ``(xx)`` gets initials derived from the
name (never written back to the project): the first letters of its first two words, the first two
letters of a one-word name, and a third letter only when two are already taken by another project.
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional, Tuple

INITIALS_RE = re.compile(r"\s\(([a-z0-9]{1,8})\)\s*$", re.I)
# One case per prefix, so an ordinary capitalised word ("Fix: ...") never reads as initials.
PREFIX_RE = re.compile(r"^([a-z0-9]{1,8}|[A-Z0-9]{1,8}):\s+")
COLLISION_RE = re.compile(r"\s+#\d+$")  # the session store's own "#N" duplicate-title suffix

_FILLER = {"a", "an", "and", "as", "at", "by", "for", "from", "in", "into", "of", "on", "or",
           "the", "to", "via", "vs", "with"}
_ARTICLES = {"a", "an", "the"}


def initials_of(name: str) -> Optional[str]:
    m = INITIALS_RE.search(name or "")
    return m.group(1).lower() if m else None


def _alnum_words(name: str) -> List[str]:
    base = re.sub(r"\([^)]*\)", " ", name or "")
    tokens = re.split(r"\s+|\s*[—–]\s*|\s+-\s+", base)
    out = []
    for tok in tokens:
        if re.search(r"[A-Za-z]", tok):
            cleaned = re.sub(r"[^a-z0-9]", "", tok.lower())
            if cleaned:
                out.append(cleaned)
    return out


def stem2(name: str) -> Optional[str]:
    words = _alnum_words(name)
    if not words:
        return None
    if len(words) == 1:
        return (words[0] + words[0][:1])[:2]
    return words[0][0] + words[1][0]


def derive_initials(name: str, taken: Iterable[str] = ()) -> Optional[str]:
    """Two letters, or three when the two-letter code is already taken. Never longer."""
    taken = set(taken)
    stem = stem2(name)
    if not stem:
        return None
    if stem not in taken:
        return stem
    words = _alnum_words(name)
    rest = (words[0][2:] if len(words) == 1 else "".join(w[0] for w in words[2:]) + words[1][1:] + words[0][1:])
    for ch in rest + "abcdefghijklmnopqrstuvwxyz":
        if ch.isalnum() and stem + ch not in taken:
            return stem + ch
    return None


def initials_map(project_names: Iterable[str], derive_missing: bool = False) -> Dict[str, str]:
    """``name -> initials`` for every project name (explicit ``(xx)`` first, then derived ones)."""
    names = list(project_names)
    out = {n: i for n in names if (i := initials_of(n))}
    if derive_missing:
        taken = set(out.values())
        for n in names:
            if n not in out and (ini := derive_initials(n, taken)):
                out[n] = ini
                taken.add(ini)
    return out


def _norm_word(w: str) -> str:
    w = re.sub(r"[^a-z0-9]", "", (w or "").lower())
    return w[:-1] if len(w) > 3 and w.endswith("s") else w  # "deals" == "deal"


def project_words(project_name: str, ini: str) -> set:
    """Words a title may drop because the prefix already says them: the project's name words and its initials."""
    words = _alnum_words(project_name)
    out = {_norm_word(w) for w in words} | {_norm_word("".join(words)), _norm_word(ini)}
    return {w for w in out if w}


def shorten(topic: str, max_words: int, drop: Iterable[str] = ()) -> str:
    """Cut a topic to its first clause and at most ``max_words`` words; ``max_words <= 0`` keeps it as is.

    Words in ``drop`` (normalised project words) are removed when that still leaves a meaningful clause;
    leading articles and filler words are dropped. Never returns an empty string for non-empty input."""
    text = " ".join((topic or "").split())
    if not text or max_words <= 0:
        return text
    clauses: List[List[str]] = [[]]
    for tok in text.split():
        word = tok.strip("\"'`()[]{}…,;:.!?")
        if not re.search(r"[A-Za-z0-9]", word):
            continue
        clauses[-1].append(word)
        if tok.rstrip("\"')]…").endswith((".", ":", ";", "?", "!")):
            clauses.append([])
    clauses = [c for c in clauses if c]
    if not clauses:
        return text
    words = clauses[0]
    drop = set(drop)
    if drop:
        for clause in clauses:
            kept = [w for w in clause if _norm_word(w) not in drop]
            if any(w.lower() not in _FILLER for w in kept):
                words = kept
                break
    while len(words) > 1 and (words[0].lower() in _ARTICLES):
        words = words[1:]
    words = [w for i, w in enumerate(words) if i == 0 or w.lower() not in _FILLER]
    words = words[:max_words]
    while len(words) > 1 and words[-1].lower() in _FILLER:
        words.pop()
    out = " ".join(words)
    return out[:1].upper() + out[1:] if out else text


def strip_prefix(title: str, known: Iterable[str]) -> str:
    """Drop one leading ``xx: `` when ``xx`` is the initials of a known project."""
    known = {k.lower() for k in known}
    m = PREFIX_RE.match(title or "")
    return title[m.end():] if m and m.group(1).lower() in known else title


def prefixed_title(
    title: str,
    project_name: Optional[str],
    initials: Dict[str, str],
    *,
    uppercase: bool = True,
    max_words: int = 0,
    drop_project_words: bool = False,
    max_len: int = 100,
) -> str:
    """The title a session of ``project_name`` should carry: ``XX: <topic>``.

    ``initials`` maps every project name to its initials. A session outside any project, or in a project
    without initials, keeps its title untouched. A prefix of another known project is replaced."""
    ini = initials.get(project_name or "")
    if not ini:
        return title
    topic = strip_prefix(COLLISION_RE.sub("", (title or "").strip()), initials.values())
    drop = project_words(project_name, ini) if drop_project_words else ()
    topic = shorten(topic, max_words, drop)
    if not topic:
        return title
    out = f"{ini.upper() if uppercase else ini}: {topic}"
    if len(out) > max_len - 4:  # leave room for the store's "#N" collision suffix
        out = out[: max_len - 5].rstrip() + "…"
    return out
