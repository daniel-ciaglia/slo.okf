"""Renders a bundle into a single self-contained HTML graph view.

Module shape (the html/css/js templating approach, the `generate_visualization`
signature, and the `__BUNDLE_NAME__`/`__BUNDLE_DATA__` placeholder tokens) is
adapted from GoogleCloudPlatform/knowledge-catalog
(okf/src/reference_agent/viewer/generator.py), Copyright Google LLC, licensed
under the Apache License, Version 2.0 -- see ../../../THIRD_PARTY_NOTICES.md
for the full license text.

Unlike Google's reference viewer (which scrapes markdown prose links to build
its graph), this reuses the validator's own typed-relationship reference
fields (`graph.RELATIONSHIPS`, VOCABULARY.md §3) as the edge source -- that
structured graph is this project's actual answer to OKF's missing
typed-relationship vocabulary, so the viewer should show *that* graph, not a
reconstruction of it from prose. Prose links still get rendered (via
`marked.js`) and made clickable in the detail pane, so both signals are
visible: which is deliberate.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..graph import MIRROR_FIELDS, RELATIONSHIPS, ConceptMap, discover_concepts

# Uses the dataviz skill's validated 8-slot categorical palette
# (references/palette.md) as a set -- do not insert a 9th hue. `Service` has
# no instances in the pilot bundle and any future unrecognized `type` falls
# back to the muted default.
#
# Hues are assigned by *graph adjacency*, not palette slot order: types that
# are directly linked (CustomerJourney-SLO, SLO-Alert, Alert-Runbook, SLI-Metric,
# etc.) get pulled from opposite sides of the hue wheel so connected nodes
# stay visually distinct. Dict order below is the "hop order" a reader
# follows (journey -> topology -> data -> indicators -> response), used for
# the legend/filter-dropdown display order only.
_TYPE_PALETTE: dict[str, dict[str, str]] = {
    "CustomerJourney": {"light": "#2a78d6", "dark": "#3987e5"},  # blue
    "Subsystem": {"light": "#eb6834", "dark": "#d95926"},  # orange
    "DataSource": {"light": "#e87ba4", "dark": "#d55181"},  # magenta
    "Metric": {"light": "#eda100", "dark": "#c98500"},  # yellow
    "SLI": {"light": "#4a3aa7", "dark": "#9085e9"},  # violet
    "SLO": {"light": "#008300", "dark": "#008300"},  # green
    "Alert": {"light": "#e34948", "dark": "#e66767"},  # red
    "Runbook": {"light": "#1baf7a", "dark": "#199e70"},  # aqua
}
_DEFAULT_NODE_COLOR = {"light": "#94a3b8", "dark": "#7c8aa0"}

_LINK_RE = re.compile(r"\]\(([^)\s]+\.md)(?:#[A-Za-z0-9_\-]*)?\)")


def _rewrite_body_links(body: str, doc_dir: Path, bundle_root: Path, concept_ids: set[str]) -> str:
    """Rewrite markdown links that resolve to a known concept into an `okf://<id>`
    scheme so the client can make them clickable without re-deriving path
    resolution in JS. Links to unknown targets or external URLs pass through untouched.
    """
    bundle_root_resolved = bundle_root.resolve()

    def _sub(m: re.Match[str]) -> str:
        target = m.group(1)
        if "://" in target or target.startswith("/"):
            return m.group(0)
        try:
            resolved = (doc_dir / target).resolve().relative_to(bundle_root_resolved)
        except ValueError:
            return m.group(0)
        rel = resolved.as_posix()
        if rel.endswith(".md"):
            rel = rel[:-3]
        if rel not in concept_ids:
            return m.group(0)
        return f"](okf://{rel})"

    return _LINK_RE.sub(_sub, body)


def _node(cid: str, concept: Any, body: str) -> dict[str, Any]:
    color = _TYPE_PALETTE.get(concept.type, _DEFAULT_NODE_COLOR)
    return {
        "data": {
            "id": cid,
            "label": concept.title or cid,
            "type": concept.type,
            "description": concept.description or "",
            "resource": concept.resource or "",
            "tags": concept.tags or [],
            "owner": concept.owner or "",
            "reviewed": concept.reviewed.isoformat() if concept.reviewed else "",
            "review_interval": concept.review_interval or "",
            "color": color,
            "size": 30 + min(60, len(body) // 200),
        }
    }


# graph.MIRROR_FIELDS (VOCABULARY.md §3) pairs a forward field with the
# informational back-ref that restates it from the other end -- drawing both
# as separate edges doubles up every one of these links in the graph for no
# new information, which is most of what "too many connections" was. The
# validator now enforces (graph.check_backref_symmetry) that both sides
# agree, so it's safe to just collapse each mirrored pair into the single
# edge the *primary* (forward) field produced.
_BACKREF_OF: dict[tuple[str, str], tuple[str, str]] = {
    backref: primary for primary, backref in MIRROR_FIELDS.items()
}


def _edges(concepts: ConceptMap) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    mirrored_pairs: set[frozenset[str]] = set()

    def add(source: str, target: str | None, field_name: str, type_field: tuple[str, str]) -> None:
        if not target or target == source or target not in concepts:
            return
        pair = frozenset((source, target))
        if type_field in _BACKREF_OF and pair in mirrored_pairs:
            return
        key = (source, target, field_name)
        if key in seen:
            return
        seen.add(key)
        edges.append({
            "data": {
                "id": f"{source}__{field_name}__{target}",
                "source": source,
                "target": target,
                "field": field_name,
            }
        })
        if type_field in MIRROR_FIELDS:
            mirrored_pairs.add(pair)

    # Iterate relationships outer, concepts inner, so a mirrored pair's
    # primary field (always declared first in RELATIONSHIPS) is always
    # processed before its back-ref -- dedup can't depend on bundle directory
    # naming happening to sort concepts in the right order.
    for (t, field_name), (_target_type, cardinality, _required) in RELATIONSHIPS.items():
        for cid, (concept, _parsed, _path) in concepts.items():
            if concept.type != t:
                continue
            value = getattr(concept, field_name, None)
            if cardinality == "many":
                for target_id in value or []:
                    add(cid, target_id, field_name, (t, field_name))
            elif value:
                add(cid, value, field_name, (t, field_name))

    for cid, (concept, _parsed, _path) in concepts.items():
        if concept.type == "SLI":
            ratio = getattr(concept, "ratio_metric", None)
            if ratio is not None:
                add(cid, ratio.good, "ratio_metric.good", ("SLI", "ratio_metric.good"))
                add(cid, ratio.total, "ratio_metric.total", ("SLI", "ratio_metric.total"))
            threshold = getattr(concept, "threshold_metric", None)
            if threshold:
                add(cid, threshold, "threshold_metric", ("SLI", "threshold_metric"))

    return edges


def _build_graph(concepts: ConceptMap, bundle_root: Path) -> dict[str, Any]:
    concept_ids = set(concepts)
    bodies = {
        cid: _rewrite_body_links(parsed.body or "", path.parent, bundle_root, concept_ids)
        for cid, (_concept, parsed, path) in concepts.items()
    }
    nodes = [_node(cid, concept, bodies[cid]) for cid, (concept, _parsed, _path) in concepts.items()]
    edges = _edges(concepts)
    types = sorted({concept.type for concept, _parsed, _path in concepts.values()})
    return {
        "nodes": nodes,
        "edges": edges,
        "bodies": bodies,
        "types": types,
        "palette": _TYPE_PALETTE,
        "defaultColor": _DEFAULT_NODE_COLOR,
    }


def _load_template() -> str:
    return (Path(__file__).parent / "templates" / "viz.html").read_text(encoding="utf-8")


def _load_asset(name: str) -> str:
    return (Path(__file__).parent / "static" / name).read_text(encoding="utf-8")


def generate_visualization(
    bundle_root: Path,
    out_path: Path,
    *,
    bundle_name: str | None = None,
) -> dict[str, int]:
    """Walk a bundle and write a single self-contained HTML visualization.

    Returns counts: {'concepts': N, 'edges': M, 'issues': K, 'bytes': B}.
    `issues` reflects field-pass parse/validation problems found while
    discovering concepts (see graph.discover_concepts) -- the viewer is
    best-effort and renders what it can even over a bundle that wouldn't pass
    `okf-validator --strict`, which is useful for debugging a broken bundle.
    """
    bundle_root = Path(bundle_root)
    out_path = Path(out_path)
    if not bundle_root.is_dir():
        raise FileNotFoundError(f"Bundle directory not found: {bundle_root}")

    concepts, issues = discover_concepts(bundle_root)
    graph = _build_graph(concepts, bundle_root)
    template = _load_template()
    css = _load_asset("viz.css")
    js = _load_asset("viz.js")
    name = bundle_name or bundle_root.resolve().name

    html = (
        template
        .replace("/*__VIZ_CSS__*/", css)
        .replace("/*__VIZ_JS__*/", js)
        .replace("__BUNDLE_NAME__", json.dumps(name))
        .replace("__BUNDLE_DATA__", json.dumps(graph))
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")

    return {
        "concepts": len(concepts),
        "edges": len(graph["edges"]),
        "issues": len(issues),
        "bytes": len(html.encode("utf-8")),
    }
