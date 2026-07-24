from __future__ import annotations

import json
import re
from pathlib import Path
from textwrap import dedent

import pytest

from okf_validator.viewer import generate_visualization

BUNDLE_ROOT = Path(__file__).resolve().parents[2] / "bundle"


def _write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(body).lstrip(), encoding="utf-8")


def _make_bundle(root: Path) -> None:
    _write(
        root / "journeys" / "checkout.md",
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
        ---
        See [availability SLO](../slos/availability.md).
        """,
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
        owner: checkout-team
        reviewed: 2026-07-15
        review_interval: 90d
        ---
        Backed by [availability SLI](../slis/availability.md). See also [missing](missing.md).
        """,
    )
    _write(
        root / "slis" / "availability.md",
        """
        ---
        type: SLI
        title: Availability SLI
        description: Ratio of good to total requests.
        ratio_metric:
          good: metrics/requests_good
          total: metrics/requests_total
        ---
        Ratio of [good](../metrics/requests_good.md) to [total](../metrics/requests_total.md).
        """,
    )
    _write(
        root / "metrics" / "requests_good.md",
        """
        ---
        type: Metric
        title: Good requests
        resource: sum(rate(checkout_requests_total{code=~"2.."}[5m]))
        ---
        Good request counter.
        """,
    )
    _write(
        root / "metrics" / "requests_total.md",
        """
        ---
        type: Metric
        title: Total requests
        resource: sum(rate(checkout_requests_total[5m]))
        ---
        Total request counter.
        """,
    )
    # An auto-generated index that should NOT appear as a concept node.
    _write(root / "index.md", "# My Bundle\n- journeys/checkout\n")


def _extract_bundle_data(html: str) -> dict:
    m = re.search(r"window\.BUNDLE\s*=\s*(\{.*?\});", html, re.DOTALL)
    assert m, "BUNDLE JSON not found in generated HTML"
    return json.loads(m.group(1))


def test_generate_visualization_writes_html(tmp_path: Path):
    bundle = tmp_path / "bundle"
    _make_bundle(bundle)
    out = tmp_path / "viz.html"
    stats = generate_visualization(bundle, out, bundle_name="My Bundle")

    assert out.exists()
    assert stats["concepts"] == 5
    assert stats["issues"] == 0
    assert stats["bytes"] > 0
    html = out.read_text(encoding="utf-8")
    assert "<title>OKF Bundle Viewer</title>" in html
    assert "cytoscape" in html.lower()
    assert "marked" in html.lower()
    assert '"My Bundle"' in html


def test_index_md_is_not_a_concept(tmp_path: Path):
    bundle = tmp_path / "bundle"
    _make_bundle(bundle)
    out = tmp_path / "viz.html"
    generate_visualization(bundle, out)
    data = _extract_bundle_data(out.read_text(encoding="utf-8"))
    ids = {n["data"]["id"] for n in data["nodes"]}
    assert "index" not in ids
    assert ids == {
        "journeys/checkout",
        "slos/availability",
        "slis/availability",
        "metrics/requests_good",
        "metrics/requests_total",
    }


def test_edges_come_from_typed_frontmatter_fields_not_prose(tmp_path: Path):
    bundle = tmp_path / "bundle"
    _make_bundle(bundle)
    out = tmp_path / "viz.html"
    generate_visualization(bundle, out)
    data = _extract_bundle_data(out.read_text(encoding="utf-8"))
    pairs = {(e["data"]["source"], e["data"]["target"], e["data"]["field"]) for e in data["edges"]}
    assert pairs == {
        ("journeys/checkout", "slos/availability", "slos"),
        ("slos/availability", "slis/availability", "sli"),
        ("slis/availability", "metrics/requests_good", "ratio_metric.good"),
        ("slis/availability", "metrics/requests_total", "ratio_metric.total"),
    }


def test_missing_link_targets_are_skipped(tmp_path: Path):
    bundle = tmp_path / "bundle"
    _make_bundle(bundle)
    out = tmp_path / "viz.html"
    generate_visualization(bundle, out)
    data = _extract_bundle_data(out.read_text(encoding="utf-8"))
    ids = {n["data"]["id"] for n in data["nodes"]}
    assert "missing" not in ids


def test_prose_links_to_known_concepts_rewritten_to_okf_scheme(tmp_path: Path):
    bundle = tmp_path / "bundle"
    _make_bundle(bundle)
    out = tmp_path / "viz.html"
    generate_visualization(bundle, out)
    data = _extract_bundle_data(out.read_text(encoding="utf-8"))
    checkout_body = data["bodies"]["journeys/checkout"]
    assert "(okf://slos/availability)" in checkout_body
    slo_body = data["bodies"]["slos/availability"]
    assert "(okf://slis/availability)" in slo_body
    # A dangling prose link to a nonexistent concept passes through untouched.
    assert "(missing.md)" in slo_body


def test_node_colors_come_from_validated_palette(tmp_path: Path):
    bundle = tmp_path / "bundle"
    _make_bundle(bundle)
    out = tmp_path / "viz.html"
    generate_visualization(bundle, out)
    data = _extract_bundle_data(out.read_text(encoding="utf-8"))
    by_id = {n["data"]["id"]: n["data"] for n in data["nodes"]}
    assert by_id["journeys/checkout"]["color"] == data["palette"]["CustomerJourney"]
    assert by_id["slos/availability"]["color"] == data["palette"]["SLO"]
    assert by_id["slis/availability"]["color"] == data["palette"]["SLI"]
    assert by_id["metrics/requests_good"]["color"] == data["palette"]["Metric"]


def test_raises_when_bundle_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        generate_visualization(tmp_path / "nope", tmp_path / "viz.html")


def test_checkout_pilot_bundle_visualizes_cleanly(tmp_path: Path):
    out = tmp_path / "viz.html"
    stats = generate_visualization(BUNDLE_ROOT, out, bundle_name="Checkout pilot")
    assert stats["concepts"] == 16
    assert stats["issues"] == 0
    # 28 raw relationship fields minus 8 informational back-refs (SLO.journey x2,
    # Service.journeys x3, Service.subsystems x1, Runbook.alerts x2) that mirror
    # a forward field already producing the same edge.
    assert stats["edges"] == 20


def test_backref_fields_do_not_duplicate_their_forward_edge(tmp_path: Path):
    bundle = tmp_path / "bundle"
    _write(
        bundle / "journeys" / "checkout.md",
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
        services:
          - services/cart-service
        ---
        Body.
        """,
    )
    _write(
        bundle / "slos" / "availability.md",
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
        bundle / "slis" / "availability.md",
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
        bundle / "metrics" / "errors.md",
        """
        ---
        type: Metric
        title: Errors
        resource: sum(rate(errors_total[5m]))
        ---
        Body.
        """,
    )
    _write(
        bundle / "services" / "cart-service.md",
        """
        ---
        type: Service
        title: Cart service
        journeys:
          - journeys/checkout
        ---
        Body.
        """,
    )
    out = tmp_path / "viz.html"
    generate_visualization(bundle, out)
    data = _extract_bundle_data(out.read_text(encoding="utf-8"))
    pairs = {(e["data"]["source"], e["data"]["target"]) for e in data["edges"]}
    # Only the forward-field edges should appear -- not their back-ref mirrors.
    assert ("journeys/checkout", "slos/availability") in pairs
    assert ("slos/availability", "journeys/checkout") not in pairs
    assert ("journeys/checkout", "services/cart-service") in pairs
    assert ("services/cart-service", "journeys/checkout") not in pairs
    assert len(data["edges"]) == 4  # slos, services, sli, threshold_metric -- no duplicates
