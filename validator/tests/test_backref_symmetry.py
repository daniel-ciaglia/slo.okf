"""Rule 9 (VOCABULARY.md §5): informational back-ref fields must agree with
the forward field they mirror, in both directions -- see graph.check_backref_symmetry.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from okf_validator.graph import check_backref_symmetry, discover_concepts


def _write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(body).lstrip(), encoding="utf-8")


def _journey(root: Path, subsystems: list[str]) -> None:
    subsystems_field = "subsystems: []" if not subsystems else (
        "subsystems:\n" + "\n".join(f"  - {s}" for s in subsystems)
    )
    _write(
        root / "journeys" / "checkout.md",
        dedent(
            """
            ---
            type: CustomerJourney
            title: Checkout
            description: Cart to confirmation.
            owner: checkout-team
            created: 2026-07-15
            reviewed: 2026-07-15
            review_interval: 90d
            slos:
              - slos/availability
            """
        ).lstrip()
        + subsystems_field
        + "\n---\n\nBody.\n",
    )
    _write(
        root / "slos" / "availability.md",
        """
        ---
        type: SLO
        title: Availability
        description: 99.9% success rate.
        sli: slis/availability
        target: "99.9%"
        time_window: 30d rolling
        journey: journeys/checkout
        owner: checkout-team
        reviewed: 2026-07-15
        review_interval: 90d
        ---
        Body.
        """,
    )
    _write(
        root / "slis" / "availability.md",
        """
        ---
        type: SLI
        title: Availability SLI
        description: Ratio of good to total requests.
        threshold_metric: metrics/errors
        ---
        Body.
        """,
    )
    _write(
        root / "metrics" / "errors.md",
        """
        ---
        type: Metric
        title: Errors
        resource: sum(rate(errors_total[5m]))
        ---
        Body.
        """,
    )


def _subsystem(root: Path, name: str, journeys: list[str]) -> None:
    journeys_field = "journeys: []" if not journeys else (
        "journeys:\n" + "\n".join(f"  - {j}" for j in journeys)
    )
    _write(
        root / "subsystems" / f"{name}.md",
        dedent(
            f"""
            ---
            type: Subsystem
            title: {name.title()}
            resource: services/{name}
            owner: checkout-team
            reviewed: 2026-07-15
            review_interval: 90d
            """
        ).lstrip()
        + journeys_field
        + "\n---\n\nBody.\n",
    )


def test_consistent_backrefs_pass_cleanly(tmp_path: Path):
    bundle = tmp_path / "bundle"
    _journey(bundle, subsystems=["subsystems/cart-service"])
    _subsystem(bundle, "cart-service", journeys=["journeys/checkout"])
    concepts, discovery_issues = discover_concepts(bundle)
    assert discovery_issues == []
    assert check_backref_symmetry(concepts) == []


def test_forward_reference_without_matching_backref_is_an_error(tmp_path: Path):
    bundle = tmp_path / "bundle"
    _journey(bundle, subsystems=["subsystems/cart-service"])
    _subsystem(bundle, "cart-service", journeys=[])  # forgot to declare the back-ref
    concepts, discovery_issues = discover_concepts(bundle)
    assert discovery_issues == []
    issues = check_backref_symmetry(concepts)
    assert len(issues) == 1
    assert issues[0].rule == "missing-backlink"
    assert issues[0].concept_id == "journeys/checkout"
    assert issues[0].severity == "error"


def test_stale_backref_with_no_matching_forward_reference_is_an_error(tmp_path: Path):
    bundle = tmp_path / "bundle"
    _journey(bundle, subsystems=[])  # journey no longer lists the subsystem
    _subsystem(bundle, "cart-service", journeys=["journeys/checkout"])  # but subsystem still claims it
    concepts, discovery_issues = discover_concepts(bundle)
    assert discovery_issues == []
    issues = check_backref_symmetry(concepts)
    assert len(issues) == 1
    assert issues[0].rule == "stale-backlink"
    assert issues[0].concept_id == "subsystems/cart-service"
    assert issues[0].severity == "error"
