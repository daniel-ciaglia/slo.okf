from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from .graph import Issue, check_backref_symmetry, check_graph, check_supersedes_cycles, discover_concepts


def _print_human(concepts: dict, issues: list[Issue], bundle_root: Path) -> None:
    for issue in issues:
        rel = issue.path.relative_to(bundle_root)
        cid = f" {issue.concept_id}" if issue.concept_id else ""
        print(f"[{issue.severity.upper()}] {rel}:{issue.line} ({issue.rule}){cid}: {issue.message}")

    errors = sum(1 for i in issues if i.severity == "error")
    warnings = sum(1 for i in issues if i.severity == "warning")
    print(f"\n{len(concepts)} concept(s) checked, {errors} error(s), {warnings} warning(s)")


def _print_json(concepts: dict, issues: list[Issue], bundle_root: Path) -> None:
    payload = {
        "concepts_checked": len(concepts),
        "issues": [
            {
                "path": str(issue.path.relative_to(bundle_root)),
                "line": issue.line,
                "concept_id": issue.concept_id,
                "rule": issue.rule,
                "message": issue.message,
                "severity": issue.severity,
            }
            for issue in issues
        ],
    }
    print(json.dumps(payload, indent=2))


def _run_validate(args: argparse.Namespace) -> int:
    bundle_root = args.bundle_dir.resolve()
    if not bundle_root.is_dir():
        print(f"error: {bundle_root} is not a directory", file=sys.stderr)
        return 2

    concepts, issues = discover_concepts(bundle_root)
    issues = issues + check_graph(concepts) + check_backref_symmetry(concepts) + check_supersedes_cycles(concepts)
    issues.sort(key=lambda i: (str(i.path), i.line))

    if args.json:
        _print_json(concepts, issues, bundle_root)
    else:
        _print_human(concepts, issues, bundle_root)

    has_errors = any(i.severity == "error" for i in issues)
    return 1 if (args.strict and has_errors) else 0


def _print_review_human(discovery_issues: list[Issue], statuses: list, problems: list, bundle_root: Path) -> None:
    if discovery_issues:
        _print_human({}, discovery_issues, bundle_root)
        print()

    for status in statuses:
        rel = status.path.relative_to(bundle_root)
        if status.overdue:
            label = "OVERDUE"
            detail = f"overdue by {-status.days_until_due}d"
        else:
            label = "ok"
            detail = f"due in {status.days_until_due}d"
        print(
            f"[{label:7}] {rel} ({status.type}) {status.concept_id}: {detail} "
            f"(due {status.due}, based on {status.basis_field}: {status.basis_date}, interval {status.review_interval})"
        )

    for problem in problems:
        rel = problem.path.relative_to(bundle_root)
        print(f"[ERROR  ] {rel} {problem.concept_id}: {problem.message}")

    overdue = sum(1 for s in statuses if s.overdue)
    print(f"\n{len(statuses)} concept(s) with a review_interval checked, {overdue} overdue, {len(problems)} unresolvable")


def _print_review_json(discovery_issues: list[Issue], statuses: list, problems: list, bundle_root: Path) -> None:
    payload = {
        "discovery_issues": [
            {
                "path": str(issue.path.relative_to(bundle_root)),
                "line": issue.line,
                "concept_id": issue.concept_id,
                "rule": issue.rule,
                "message": issue.message,
                "severity": issue.severity,
            }
            for issue in discovery_issues
        ],
        "checked": len(statuses),
        "overdue": sum(1 for s in statuses if s.overdue),
        "reviews": [
            {
                "concept_id": s.concept_id,
                "path": str(s.path.relative_to(bundle_root)),
                "type": s.type,
                "basis_field": s.basis_field,
                "basis_date": s.basis_date.isoformat(),
                "review_interval": s.review_interval,
                "due": s.due.isoformat(),
                "days_until_due": s.days_until_due,
                "overdue": s.overdue,
            }
            for s in statuses
        ],
        "problems": [
            {"concept_id": p.concept_id, "path": str(p.path.relative_to(bundle_root)), "message": p.message}
            for p in problems
        ],
    }
    print(json.dumps(payload, indent=2))


def _run_review(args: argparse.Namespace) -> int:
    from .review import check_review

    bundle_root = args.bundle_dir.resolve()
    if not bundle_root.is_dir():
        print(f"error: {bundle_root} is not a directory", file=sys.stderr)
        return 2

    concepts, discovery_issues = discover_concepts(bundle_root)
    statuses, problems = check_review(concepts, as_of=args.as_of)

    if args.json:
        _print_review_json(discovery_issues, statuses, problems, bundle_root)
    else:
        _print_review_human(discovery_issues, statuses, problems, bundle_root)

    has_blockers = discovery_issues or problems or any(s.overdue for s in statuses)
    return 1 if (args.strict and has_blockers) else 0


def _run_visualize(args: argparse.Namespace) -> int:
    from .viewer import generate_visualization

    bundle_root = args.bundle_dir.resolve()
    if not bundle_root.is_dir():
        print(f"error: {bundle_root} is not a directory", file=sys.stderr)
        return 2

    out = args.out or (args.bundle_dir / "viz.html")
    stats = generate_visualization(bundle_root, out, bundle_name=args.name)
    print(
        f"Wrote {stats['concepts']} concept(s), {stats['edges']} edge(s) "
        f"({stats['issues']} issue(s) skipped), {stats['bytes']} bytes -> {out}",
        file=sys.stderr,
    )
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="okf-validator",
        description="Validate and visualize OKF bundles for the SRE OKF vocabulary (see VOCABULARY.md).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser(
        "validate",
        help="Check a bundle against VOCABULARY.md (field pass + graph pass).",
    )
    validate.add_argument("bundle_dir", type=Path, help="path to the OKF bundle root")
    validate.add_argument("--strict", action="store_true", help="exit 1 if any error-severity issue is found")
    validate.add_argument("--json", action="store_true", help="machine-readable output")

    review = sub.add_parser(
        "review",
        help="Flag concepts whose 'reviewed' (or 'created') date plus 'review_interval' has elapsed (VOCABULARY.md §2).",
    )
    review.add_argument("bundle_dir", type=Path, help="path to the OKF bundle root")
    review.add_argument(
        "--strict", action="store_true",
        help="exit 1 if any concept is overdue for review, or its due date can't be computed",
    )
    review.add_argument("--json", action="store_true", help="machine-readable output")
    review.add_argument(
        "--as-of", type=date.fromisoformat, default=None, metavar="YYYY-MM-DD",
        help="compute staleness as of this date instead of today",
    )

    visualize = sub.add_parser(
        "visualize",
        help="Generate a self-contained HTML graph view of a bundle.",
    )
    visualize.add_argument("bundle_dir", type=Path, help="path to the OKF bundle root")
    visualize.add_argument(
        "--out", type=Path, default=None,
        help="output HTML path (default: <bundle_dir>/viz.html)",
    )
    visualize.add_argument(
        "--name", default=None,
        help="display name for the bundle (default: bundle directory name)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    if args.command == "validate":
        return _run_validate(args)
    if args.command == "review":
        return _run_review(args)
    return _run_visualize(args)


if __name__ == "__main__":
    sys.exit(main())
