"""Generates `index.md` files for progressive disclosure (OKF spec §6).

Deterministic port of Google's reference generator
(`GoogleCloudPlatform/knowledge-catalog`, `okf/src/reference_agent/bundle/index.py`,
Copyright Google LLC, Apache License 2.0 -- see ../../THIRD_PARTY_NOTICES.md):
same per-directory, per-type grouping and relative-link format, but built on
top of this project's own concept discovery (`graph.discover_concepts`)
instead of Google's `OKFDocument`, and with the LLM-synthesized subdirectory
blurb dropped -- a subdirectory description is reused verbatim only when that
subdirectory has exactly one entry with a description, otherwise it's left
blank rather than calling out to a model. A directory whose concept files all
fail discovery (bad frontmatter, unresolvable type) is simply left unindexed,
same as an empty directory; those problems are already reported by
`okf-validator validate`.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .graph import discover_concepts

_INDEX_FILE = "index.md"

# (group, title, relative_link, description)
Entry = tuple[str, str, str, str]


def _flatten(text: str) -> str:
    """Collapse a frontmatter description to one line.

    A `description` sourced from a multi-line/folded YAML scalar can parse to
    a string containing embedded newlines -- dropped straight into a `* [..]
    - <desc>` bullet, that breaks the single-line list-item Markdown expects.
    """
    return " ".join(text.split())


def _format_index(entries: list[Entry]) -> str:
    grouped: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for group, title, link, desc in entries:
        grouped[group or "Other"].append((title, link, _flatten(desc)))

    sections: list[str] = []
    for group in sorted(grouped):
        lines = [f"# {group}", ""]
        for title, link, desc in sorted(grouped[group], key=lambda e: e[0].lower()):
            suffix = f" - {desc}" if desc else ""
            lines.append(f"* [{title}]({link}){suffix}")
        sections.append("\n".join(lines))
    return "\n\n".join(sections) + "\n"


def build_indexes(bundle_root: Path) -> dict[Path, str]:
    """Compute the desired `index.md` content for every directory in
    `bundle_root` that (transitively) contains at least one valid concept file.

    Returns `{absolute index.md path: content}`. Does not touch disk -- see
    `write_indexes` / `check_indexes`.
    """
    bundle_root = Path(bundle_root)
    concepts, _issues = discover_concepts(bundle_root)
    if not concepts:
        return {}

    by_dir: dict[Path, list[Entry]] = defaultdict(list)
    for concept, _parsed, path in concepts.values():
        title = concept.title or path.stem
        desc = concept.description or ""
        by_dir[path.parent].append((concept.type, title, path.name, desc))

    directories = {path.parent for _c, _p, path in concepts.values()}
    for directory in list(directories):
        cur = directory
        while cur != bundle_root:
            cur = cur.parent
            directories.add(cur)

    ordered = sorted(directories, key=lambda p: (-len(p.relative_to(bundle_root).parts), str(p)))

    dir_descriptions: dict[Path, str] = {}
    computed: dict[Path, str] = {}

    for directory in ordered:
        entries: list[Entry] = list(by_dir.get(directory, []))
        for child in sorted(directory.iterdir()):
            if child.is_dir() and child in directories:
                entries.append(("Subdirectories", child.name, f"{child.name}/{_INDEX_FILE}", dir_descriptions.get(child, "")))

        if not entries:
            continue

        computed[directory / _INDEX_FILE] = _format_index(entries)

        if directory != bundle_root and len(entries) == 1 and entries[0][3]:
            dir_descriptions[directory] = entries[0][3]

    return computed


def write_indexes(bundle_root: Path) -> list[Path]:
    """Write `index.md` to every directory that needs one. Returns the paths written, sorted."""
    computed = build_indexes(bundle_root)
    for path, content in computed.items():
        path.write_text(content, encoding="utf-8")
    return sorted(computed)


def check_indexes(bundle_root: Path) -> list[Path]:
    """Return `index.md` paths that are missing or would change on regeneration,
    without writing anything. Sorted.
    """
    computed = build_indexes(bundle_root)
    stale = [path for path, content in computed.items() if not path.exists() or path.read_text(encoding="utf-8") != content]
    return sorted(stale)
