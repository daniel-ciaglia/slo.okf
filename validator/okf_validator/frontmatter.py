"""Minimal OKF frontmatter parsing: a leading '---' YAML block, then a markdown body.

Deliberately hand-rolled instead of depending on `python-frontmatter`, since we
also need best-effort per-field line numbers for error reporting, which off-the-shelf
frontmatter parsers don't expose.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

_DELIM = re.compile(r"^---\s*$")
_KEY_RE_CACHE: dict[str, re.Pattern[str]] = {}


class FrontmatterError(Exception):
    """Raised when a file doesn't parse as a valid OKF concept file."""


@dataclass
class ParsedFile:
    path: Path
    frontmatter: dict
    body: str
    fm_start_line: int  # 1-indexed line of the opening '---'
    fm_end_line: int  # 1-indexed line of the closing '---'


def parse_file(path: Path) -> ParsedFile:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or not _DELIM.match(lines[0]):
        raise FrontmatterError(f"{path}: missing frontmatter block (file must start with '---')")

    end = None
    for i in range(1, len(lines)):
        if _DELIM.match(lines[i]):
            end = i
            break
    if end is None:
        raise FrontmatterError(f"{path}: unterminated frontmatter block (no closing '---')")

    fm_text = "\n".join(lines[1:end])
    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as exc:
        raise FrontmatterError(f"{path}: invalid YAML frontmatter: {exc}") from exc
    if not isinstance(fm, dict):
        raise FrontmatterError(f"{path}: frontmatter must be a YAML mapping, got {type(fm).__name__}")

    body = "\n".join(lines[end + 1 :])
    return ParsedFile(path=path, frontmatter=fm, body=body, fm_start_line=1, fm_end_line=end + 1)


def field_line(parsed: ParsedFile, field: str) -> int:
    """Best-effort line number of a top-level frontmatter key, for error messages.

    Falls back to the frontmatter block's start line when the key can't be
    located textually (e.g. nested fields like ratio_metric.good).
    """
    top_level_field = field.split(".")[0]
    pattern = _KEY_RE_CACHE.setdefault(top_level_field, re.compile(rf"^{re.escape(top_level_field)}\s*:"))
    with parsed.path.open(encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            if parsed.fm_start_line < i < parsed.fm_end_line and pattern.match(line.strip()):
                return i
    return parsed.fm_start_line
