"""Graph-pass checks introduced/changed in VOCABULARY.md v0.2.0:

- `Subsystem.services` is now required, >=1 entry (rule 6) -- a `Subsystem` with
  an empty list no longer validates, replacing the old "no orphaned Subsystem"
  graph-pass rule. Widened from exactly-1 to 1+ so a `Subsystem` can list more
  than one owning/consuming `Service` (e.g. a Redis instance shared across
  services) -- see VOCABULARY.md's Changelog.
- `Service.parent` can form a cycle, same class of bug as `supersedes` (rule 7)
  -- see graph.check_service_parent_cycles.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from okf_validator.graph import check_service_parent_cycles, discover_concepts


def _write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(body).lstrip(), encoding="utf-8")


def test_subsystem_without_services_is_a_field_validation_error(tmp_path: Path):
    bundle = tmp_path / "bundle"
    _write(
        bundle / "subsystems" / "redis.md",
        """
        ---
        type: Subsystem
        title: Redis
        resource: services/redis
        owner: platform-team
        reviewed: 2026-07-15
        review_interval: 90d
        ---
        Body.
        """,
    )
    concepts, issues = discover_concepts(bundle)
    assert concepts == {}
    assert len(issues) == 1
    assert issues[0].rule == "field-validation"
    assert "services" in issues[0].message


def test_subsystem_with_service_discovers_cleanly(tmp_path: Path):
    bundle = tmp_path / "bundle"
    _write(
        bundle / "services" / "cart-service.md",
        """
        ---
        type: Service
        title: Cart Service
        ---
        Body.
        """,
    )
    _write(
        bundle / "subsystems" / "redis.md",
        """
        ---
        type: Subsystem
        title: Redis
        resource: services/redis
        services:
          - services/cart-service
        owner: platform-team
        reviewed: 2026-07-15
        review_interval: 90d
        ---
        Body.
        """,
    )
    concepts, issues = discover_concepts(bundle)
    assert issues == []
    assert "subsystems/redis" in concepts


def test_subsystem_with_multiple_services_discovers_cleanly(tmp_path: Path):
    bundle = tmp_path / "bundle"
    _write(
        bundle / "services" / "cart-service.md",
        "---\ntype: Service\ntitle: Cart Service\n---\nBody.\n",
    )
    _write(
        bundle / "services" / "checkout-api.md",
        "---\ntype: Service\ntitle: Checkout Api\n---\nBody.\n",
    )
    _write(
        bundle / "subsystems" / "redis.md",
        """
        ---
        type: Subsystem
        title: Redis
        resource: services/redis
        services:
          - services/cart-service
          - services/checkout-api
        owner: platform-team
        reviewed: 2026-07-15
        review_interval: 90d
        ---
        Body.
        """,
    )
    concepts, issues = discover_concepts(bundle)
    assert issues == []
    assert "subsystems/redis" in concepts


def test_service_parent_cycle_is_detected(tmp_path: Path):
    bundle = tmp_path / "bundle"
    _write(bundle / "services" / "a.md", "---\ntype: Service\ntitle: A\nparent: services/b\n---\nBody.\n")
    _write(bundle / "services" / "b.md", "---\ntype: Service\ntitle: B\nparent: services/a\n---\nBody.\n")
    concepts, issues = discover_concepts(bundle)
    assert issues == []
    cycle_issues = check_service_parent_cycles(concepts)
    assert len(cycle_issues) == 1
    assert cycle_issues[0].rule == "service-parent-cycle"


def test_service_parent_chain_without_cycle_is_clean(tmp_path: Path):
    bundle = tmp_path / "bundle"
    _write(bundle / "services" / "platform.md", "---\ntype: Service\ntitle: Platform\n---\nBody.\n")
    _write(
        bundle / "services" / "cart-service.md",
        "---\ntype: Service\ntitle: Cart Service\nparent: services/platform\n---\nBody.\n",
    )
    concepts, issues = discover_concepts(bundle)
    assert issues == []
    assert check_service_parent_cycles(concepts) == []
