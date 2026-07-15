"""`review` subcommand: due-date computation from `reviewed` (falling back to
`created`) + `review_interval` (VOCABULARY.md §2). See okf_validator/review.py.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from textwrap import dedent

import pytest

from okf_validator.graph import discover_concepts
from okf_validator.review import IntervalError, check_review, due_date


def _write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(body).lstrip(), encoding="utf-8")


def test_due_date_days_and_months():
    assert due_date(date(2026, 1, 1), "90d") == date(2026, 4, 1)
    assert due_date(date(2026, 1, 1), "3mo") == date(2026, 4, 1)


def test_due_date_month_overflow_clamps_to_last_day():
    assert due_date(date(2026, 1, 31), "1mo") == date(2026, 2, 28)


def test_due_date_rejects_bad_interval():
    with pytest.raises(IntervalError):
        due_date(date(2026, 1, 1), "3 weeks")


def test_concept_without_review_interval_is_skipped(tmp_path: Path):
    bundle = tmp_path / "bundle"
    _write(
        bundle / "metrics" / "x.md",
        """
        ---
        type: Metric
        title: X
        resource: foo
        created: 2026-01-01
        ---
        Body.
        """,
    )
    concepts, issues = discover_concepts(bundle)
    assert issues == []
    statuses, problems = check_review(concepts, as_of=date(2026, 7, 15))
    assert statuses == []
    assert problems == []


def test_falls_back_to_created_when_reviewed_absent(tmp_path: Path):
    bundle = tmp_path / "bundle"
    _write(
        bundle / "metrics" / "x.md",
        """
        ---
        type: Metric
        title: X
        resource: foo
        created: 2026-01-01
        review_interval: 3mo
        ---
        Body.
        """,
    )
    concepts, issues = discover_concepts(bundle)
    assert issues == []
    statuses, problems = check_review(concepts, as_of=date(2026, 7, 15))
    assert problems == []
    assert len(statuses) == 1
    status = statuses[0]
    assert status.basis_field == "created"
    assert status.due == date(2026, 4, 1)
    assert status.overdue is True


def test_reviewed_takes_precedence_over_created(tmp_path: Path):
    bundle = tmp_path / "bundle"
    _write(
        bundle / "metrics" / "x.md",
        """
        ---
        type: Metric
        title: X
        resource: foo
        created: 2020-01-01
        reviewed: 2026-07-01
        review_interval: 90d
        ---
        Body.
        """,
    )
    concepts, issues = discover_concepts(bundle)
    assert issues == []
    statuses, _ = check_review(concepts, as_of=date(2026, 7, 15))
    assert statuses[0].basis_field == "reviewed"
    assert statuses[0].overdue is False


def test_missing_basis_date_is_a_problem(tmp_path: Path):
    bundle = tmp_path / "bundle"
    _write(
        bundle / "metrics" / "x.md",
        """
        ---
        type: Metric
        title: X
        resource: foo
        review_interval: 90d
        ---
        Body.
        """,
    )
    concepts, issues = discover_concepts(bundle)
    assert issues == []
    statuses, problems = check_review(concepts, as_of=date(2026, 7, 15))
    assert statuses == []
    assert len(problems) == 1
    assert "neither 'reviewed' nor 'created'" in problems[0].message


def test_bundle_review_is_clean_as_of_creation_date():
    bundle_root = Path(__file__).resolve().parents[2] / "bundle"
    concepts, issues = discover_concepts(bundle_root)
    assert issues == []
    statuses, problems = check_review(concepts, as_of=date(2026, 7, 15))
    assert problems == []
    assert all(not s.overdue for s in statuses)
