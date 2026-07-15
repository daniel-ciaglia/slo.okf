"""Review-staleness pass: for every concept that declares a `review_interval`
(VOCABULARY.md §2), compute whether it's due -- `reviewed` (or, absent that,
`created`, per the field table's fallback framing: "absent = assumed true
since created") plus the interval, compared against today.

Concepts without `review_interval` aren't subject to a review cadence at all
and are skipped entirely -- this pass never invents an obligation the
frontmatter didn't declare. Kept as its own module, not folded into graph.py,
because it's a field-pass concern (per-concept, no graph traversal) computed
against wall-clock time rather than the concept-ID reference graph.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from .graph import ConceptMap

_INTERVAL_RE = re.compile(r"^(\d+)\s*(d|mo)$")


class IntervalError(Exception):
    """Raised when a `review_interval` value doesn't match `<N>d` / `<N>mo`."""


def _add_months(base: date, months: int) -> date:
    month_index = base.month - 1 + months
    year = base.year + month_index // 12
    month = month_index % 12 + 1
    day = base.day
    while True:
        try:
            return date(year, month, day)
        except ValueError:
            day -= 1  # clamp into the target month, e.g. Jan 31 + 1mo -> Feb 28


def due_date(base: date, interval: str) -> date:
    match = _INTERVAL_RE.match(interval.strip())
    if not match:
        raise IntervalError(f"invalid review_interval {interval!r} (expected '<N>d' or '<N>mo')")
    count, unit = match.groups()
    count = int(count)
    return base + timedelta(days=count) if unit == "d" else _add_months(base, count)


@dataclass
class ReviewStatus:
    concept_id: str
    path: Path
    type: str
    basis_field: str  # "reviewed" | "created"
    basis_date: date
    review_interval: str
    due: date
    days_until_due: int  # negative == overdue
    overdue: bool


@dataclass
class ReviewProblem:
    concept_id: str
    path: Path
    message: str


def check_review(concepts: ConceptMap, as_of: date | None = None) -> tuple[list[ReviewStatus], list[ReviewProblem]]:
    as_of = as_of or date.today()
    statuses: list[ReviewStatus] = []
    problems: list[ReviewProblem] = []

    for cid, (concept, _parsed, path) in concepts.items():
        interval = getattr(concept, "review_interval", None)
        if not interval:
            continue

        reviewed = getattr(concept, "reviewed", None)
        created = getattr(concept, "created", None)
        basis_field = "reviewed" if reviewed else "created"
        basis_date = reviewed or created
        if basis_date is None:
            problems.append(
                ReviewProblem(
                    cid,
                    path,
                    "review_interval is set but neither 'reviewed' nor 'created' is present, "
                    "so no due date can be computed",
                )
            )
            continue

        try:
            due = due_date(basis_date, interval)
        except IntervalError as exc:
            problems.append(ReviewProblem(cid, path, str(exc)))
            continue

        days_until_due = (due - as_of).days
        statuses.append(
            ReviewStatus(
                concept_id=cid,
                path=path,
                type=concept.type,
                basis_field=basis_field,
                basis_date=basis_date,
                review_interval=interval,
                due=due,
                days_until_due=days_until_due,
                overdue=days_until_due < 0,
            )
        )

    statuses.sort(key=lambda s: s.days_until_due)
    return statuses, problems
