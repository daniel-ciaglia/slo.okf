"""Graph pass: cardinality, orphan, cycle, and target-type checks over the
concept-ID reference graph built from typed frontmatter relationship fields
(VOCABULARY.md §3, §5). Kept separate from the field pass (models.py) on
purpose -- relational rules are discovered iteratively as real content grows,
and a single if-chain rots fast.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pydantic

from . import frontmatter as fm
from .models import ConceptBase, get_model

RESERVED_FILENAMES = {"index.md", "log.md"}

Severity = str  # "error" | "warning"


@dataclass
class Issue:
    path: Path
    line: int
    concept_id: str | None
    rule: str
    message: str
    severity: Severity


ConceptEntry = tuple[ConceptBase, fm.ParsedFile, Path]
ConceptMap = dict[str, ConceptEntry]

# (concept type, field name) -> (target type, cardinality, required)
# cardinality: "one" | "many"
#
# Ordering matters: for any pair also listed in MIRROR_FIELDS below, the
# primary/forward entry must appear before its back-ref entry. The viewer
# (viewer/generator.py) relies on processing RELATIONSHIPS in this exact
# order to dedupe a mirrored pair into a single edge -- getting the order
# backwards silently produces a duplicate edge instead of an error.
RELATIONSHIPS: dict[tuple[str, str], tuple[str, str, bool]] = {
    ("CustomerJourney", "slos"): ("SLO", "many", True),
    ("CustomerJourney", "services"): ("Service", "many", False),
    ("Subsystem", "services"): ("Service", "many", True),
    ("Service", "slos"): ("SLO", "many", False),
    ("Service", "subsystems"): ("Subsystem", "many", False),
    ("Service", "journeys"): ("CustomerJourney", "many", False),
    ("Service", "parent"): ("Service", "one", False),
    ("Service", "children"): ("Service", "many", False),
    ("Metric", "data_source"): ("DataSource", "one", False),
    ("SLI", "data_source"): ("DataSource", "one", False),
    ("SLO", "sli"): ("SLI", "one", True),
    ("SLO", "journey"): ("CustomerJourney", "one", False),
    ("Alert", "slo"): ("SLO", "one", True),
    ("Alert", "runbook"): ("Runbook", "one", True),
    ("Runbook", "alerts"): ("Alert", "many", False),
}

# Several fields above are declared "informational back-ref" in VOCABULARY.md
# §3 -- they restate, from the other end, a relationship a forward field
# already declares (e.g. `Service.subsystems` mirrors `Subsystem.services`).
# Nothing else checks that both sides agree, so they can silently drift; see
# check_backref_symmetry. Mapping is (primary/forward type, field) ->
# (back-ref type, field). `Service.parent`/`children` mirror each other
# within the same type, which check_backref_symmetry handles the same way.
MIRROR_FIELDS: dict[tuple[str, str], tuple[str, str]] = {
    ("CustomerJourney", "slos"): ("SLO", "journey"),
    ("CustomerJourney", "services"): ("Service", "journeys"),
    ("Subsystem", "services"): ("Service", "subsystems"),
    ("Service", "parent"): ("Service", "children"),
    ("Alert", "runbook"): ("Runbook", "alerts"),
}


def concept_id_for(bundle_root: Path, path: Path) -> str:
    return str(path.relative_to(bundle_root).with_suffix(""))


def discover_concepts(bundle_root: Path) -> tuple[ConceptMap, list[Issue]]:
    concepts: ConceptMap = {}
    issues: list[Issue] = []

    for path in sorted(bundle_root.rglob("*.md")):
        if path.name in RESERVED_FILENAMES:
            continue
        try:
            parsed = fm.parse_file(path)
        except fm.FrontmatterError as exc:
            issues.append(Issue(path, 1, None, "frontmatter-parse", str(exc), "error"))
            continue

        type_name = parsed.frontmatter.get("type")
        if not type_name:
            issues.append(
                Issue(
                    path,
                    parsed.fm_start_line,
                    None,
                    "missing-type",
                    "a non-empty 'type' field is required by the OKF spec",
                    "error",
                )
            )
            continue

        model_cls = get_model(type_name)
        try:
            concept = model_cls.model_validate(parsed.frontmatter)
        except pydantic.ValidationError as exc:
            cid = concept_id_for(bundle_root, path)
            issues.append(Issue(path, parsed.fm_start_line, cid, "field-validation", str(exc), "error"))
            continue

        cid = concept_id_for(bundle_root, path)
        concepts[cid] = (concept, parsed, path)

    return concepts, issues


def _check_target(
    issues: list[Issue],
    concepts: ConceptMap,
    path: Path,
    parsed: fm.ParsedFile,
    cid: str,
    field_name: str,
    target_id: str,
    expected_type: str,
) -> None:
    line = fm.field_line(parsed, field_name)
    entry = concepts.get(target_id)
    if entry is None:
        issues.append(
            Issue(
                path,
                line,
                cid,
                "broken-link",
                f"{field_name} -> '{target_id}' does not resolve to any known concept",
                "error",
            )
        )
        return
    target_concept, _, _ = entry
    if target_concept.type != expected_type:
        issues.append(
            Issue(
                path,
                line,
                cid,
                "type-mismatch",
                f"{field_name} -> '{target_id}' must resolve to type {expected_type}, got {target_concept.type}",
                "error",
            )
        )


def check_graph(concepts: ConceptMap) -> list[Issue]:
    issues: list[Issue] = []

    for cid, (concept, parsed, path) in concepts.items():
        type_name = concept.type

        for (t, field_name), (target_type, cardinality, required) in RELATIONSHIPS.items():
            if type_name != t:
                continue
            value = getattr(concept, field_name, None)

            if cardinality == "many":
                ids = value or []
                if required and len(ids) == 0:
                    issues.append(
                        Issue(
                            path,
                            fm.field_line(parsed, field_name),
                            cid,
                            "cardinality",
                            f"{type_name}.{field_name} requires at least 1 entry",
                            "error",
                        )
                    )
                for target_id in ids:
                    _check_target(issues, concepts, path, parsed, cid, field_name, target_id, target_type)
            else:
                if required and not value:
                    issues.append(
                        Issue(
                            path,
                            fm.field_line(parsed, field_name),
                            cid,
                            "cardinality",
                            f"{type_name}.{field_name} is required",
                            "error",
                        )
                    )
                elif value:
                    _check_target(issues, concepts, path, parsed, cid, field_name, value, target_type)

        # SLI ratio_metric.{good,total} / threshold_metric -> Metric (nested, not in RELATIONSHIPS table)
        if type_name == "SLI":
            if getattr(concept, "ratio_metric", None):
                for attr in ("good", "total"):
                    target_id = getattr(concept.ratio_metric, attr)
                    _check_target(issues, concepts, path, parsed, cid, f"ratio_metric.{attr}", target_id, "Metric")
            if getattr(concept, "threshold_metric", None):
                _check_target(
                    issues, concepts, path, parsed, cid, "threshold_metric", concept.threshold_metric, "Metric"
                )

    return issues


def _field_values(concept: ConceptBase, field_name: str) -> list[str]:
    value = getattr(concept, field_name, None)
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def check_backref_symmetry(concepts: ConceptMap) -> list[Issue]:
    """Rule 9 (VOCABULARY.md §3): a mirrored back-ref field must agree with
    the forward field it restates, in both directions -- otherwise the two
    can silently drift (a subsystem keeps claiming a journey that no longer
    lists it, or vice versa) with nothing else catching it. Broken links and
    type mismatches are already reported by check_graph; this only checks
    agreement between concepts that both resolve and both have the right type.
    """
    issues: list[Issue] = []

    for (primary_type, primary_field), (backref_type, backref_field) in MIRROR_FIELDS.items():
        for cid, (concept, parsed, path) in concepts.items():
            if concept.type != primary_type:
                continue
            for target_id in _field_values(concept, primary_field):
                entry = concepts.get(target_id)
                if entry is None:
                    continue
                target_concept, _, _ = entry
                if target_concept.type != backref_type:
                    continue
                if cid not in _field_values(target_concept, backref_field):
                    issues.append(
                        Issue(
                            path,
                            fm.field_line(parsed, primary_field),
                            cid,
                            "missing-backlink",
                            f"{primary_type}.{primary_field} -> '{target_id}', but {backref_type} "
                            f"'{target_id}' does not list '{cid}' in its {backref_field} back-ref",
                            "error",
                        )
                    )

        for cid, (concept, parsed, path) in concepts.items():
            if concept.type != backref_type:
                continue
            for target_id in _field_values(concept, backref_field):
                entry = concepts.get(target_id)
                if entry is None:
                    continue
                target_concept, _, _ = entry
                if target_concept.type != primary_type:
                    continue
                if cid not in _field_values(target_concept, primary_field):
                    issues.append(
                        Issue(
                            path,
                            fm.field_line(parsed, backref_field),
                            cid,
                            "stale-backlink",
                            f"{backref_type}.{backref_field} -> '{target_id}', but {primary_type} "
                            f"'{target_id}' does not list '{cid}' in its {primary_field} field",
                            "error",
                        )
                    )

    return issues


def _check_self_reference_cycles(concepts: ConceptMap, field_name: str, rule: str) -> list[Issue]:
    """Generic single-valued self-reference cycle detector -- shared by
    `supersedes` (any type, VOCABULARY.md §2) and `Service.parent`
    (VOCABULARY.md §3/rule 7)."""
    issues: list[Issue] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(cid: str, chain: list[str]) -> None:
        if cid in visiting:
            cycle = " -> ".join([*chain[chain.index(cid) :], cid])
            concept, parsed, path = concepts[cid]
            issues.append(Issue(path, parsed.fm_start_line, cid, rule, f"cycle detected: {cycle}", "error"))
            return
        if cid in visited or cid not in concepts:
            return
        visiting.add(cid)
        concept, parsed, path = concepts[cid]
        target = getattr(concept, field_name, None)
        if target:
            dfs(target, [*chain, cid])
        visiting.discard(cid)
        visited.add(cid)

    for cid in concepts:
        if cid not in visited:
            dfs(cid, [])

    return issues


def check_supersedes_cycles(concepts: ConceptMap) -> list[Issue]:
    return _check_self_reference_cycles(concepts, "supersedes", "supersedes-cycle")


def check_service_parent_cycles(concepts: ConceptMap) -> list[Issue]:
    return _check_self_reference_cycles(concepts, "parent", "service-parent-cycle")
