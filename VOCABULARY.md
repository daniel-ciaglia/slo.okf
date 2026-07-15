# SRE OKF Vocabulary v0.1

A controlled `type` vocabulary and frontmatter convention for documenting SRE customer journeys — SLI/SLO/alert/runbook chains — as an [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf) (OKF v0.1) bundle.

**Non-goal, stated up front**: a concept file in this vocabulary computes nothing. `type: SLO` is documentation *about* an SLO — target, rationale, owner — not an executable specification. Executable definitions (Prometheus recording rules, Alertmanager rules, Sloth specs) live in their own tooling and are referenced from here via the `resource` field. If you're looking for something that evaluates burn rate, this isn't it; follow `resource` to the thing that does.

Naming donor: [OpenSLO](https://github.com/OpenSLO/OpenSLO)'s object model, for kind names and field shapes only — **no runtime dependency**. OpenSLO has never cut a tagged release and its `main` branch has been idle since 2025-10-09; we borrow its vocabulary because it's a well-thought-through domain schema, not because it's a moving target we track.

Temporal convention: borrowed from [KCP](https://github.com/Cantara/knowledge-context-protocol)'s `valid_from`/`valid_until`/`supersedes` field *names* only, as plain OKF frontmatter — no KCP manifest format, no signing, no trust/federation machinery. KCP itself is a 5-month-old, effectively single-author project; treat the field names as a decent naming convention, not an endorsement of KCP as infrastructure.

---

## 1. Type vocabulary

| `type` | Origin | Role |
|---|---|---|
| `CustomerJourney` | SRE-native | Top of the graph. An end-to-end path a customer/request takes, e.g. checkout. Links ≥1 `SLO`. |
| `Service` | OpenSLO `Service` | Optional logical grouping of SLOs (pure grouping, no fields of its own beyond description). |
| `Subsystem` | SRE-native | An infra/deployment topology node (a Terraform resource, an ArgoCD Application). Generator-owned once generators exist. |
| `DataSource` | OpenSLO `DataSource` | A telemetry source — a Prometheus instance/job, not a single metric. |
| `Metric` | SRE-native | One concrete, named metric (a PromQL expression or dashboard panel). |
| `SLI` | OpenSLO `SLI` | An indicator definition: what "good" and "total" mean, referencing `Metric`/`DataSource`. |
| `SLO` | OpenSLO `SLO`, simplified | A target + rationale for exactly one `SLI`. |
| `Alert` | Collapses OpenSLO `AlertPolicy` + `AlertCondition` | A documented alert: what it means, what severity, which runbook to open. |
| `Runbook` | SRE-native | Oncall prose. Never generated — see §4. |

### Why these deviate from OpenSLO

- **`Alert` collapses `AlertPolicy` + `AlertCondition`, and drops `AlertNotificationTarget` as a type entirely.** OpenSLO's three-way split exists because its consumer is a rule-evaluation engine that needs to model policy/condition/routing separately. OKF's consumer is a human or an oncall agent navigating a graph — it needs "what alert, how bad, which runbook," not a notification-routing model. Routing stays in the real Alertmanager rule, referenced via `resource`; `notify` is a plain informational string field, not a linked concept.
- **`SLO` drops OpenSLO's `objectives[]` composite array.** OpenSLO models a composite/multi-indicator SLO as one `SLO` object with multiple weighted `objectives`, combined via a `budgetingMethod` (`Occurrences`/`Timeslices`/`RatioTimeslices`). That's real computation, and OKF concepts compute nothing. We get the same "end-to-end journey" idea — which is literally how OpenSLO's own docs frame composite SLOs — by keeping `SLO` single-indicator (exactly 1 `SLI`) and letting `CustomerJourney` be the thing that links multiple SLOs. A journey's health is legible as "these N SLOs," not as a weighted formula a reader has to evaluate.
- **`Metric` is promoted to its own type**, where OpenSLO keeps metric definitions inline inside `SLI.ratioMetric`/`thresholdMetric`. OKF's unit of navigation is one concept per file; a metric is frequently reused across multiple SLIs (e.g. `checkout_requests_total` backs both an availability SLI and a latency SLI), so it earns its own concept ID rather than being duplicated inline each time.
- **`type` values keep OpenSLO's PascalCase kind naming** (`DataSource`, `SLI`, `SLO`, `Service`) for instant recognizability to anyone who already knows OpenSLO, even though OKF itself is casing-agnostic.

---

## 2. Cross-cutting frontmatter fields

Available on any type. OKF-native fields (`type`, `title`, `description`, `resource`, `tags`, `timestamp`) follow the [OKF spec](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) exactly — only `type` is required there. Everything below is producer-defined, which the spec explicitly permits.

| Field | Type | Meaning |
|---|---|---|
| `owner` | string | Team or individual accountable for this concept. |
| `created` | date (`YYYY-MM-DD`) | When the concept was first authored. |
| `reviewed` | date (`YYYY-MM-DD`) | Last time a human confirmed this is still accurate. **Attestation, not correctness** — see §3. |
| `review_interval` | string (`<N>d` / `<N>mo`) | Expected cadence between reviews, e.g. `90d`. Used to flag `reviewed` going stale. |
| `valid_from` | date | When this concept's content becomes true (KCP-borrowed). Absent = assumed true since `created`. |
| `valid_until` | date | When this concept's content stops being true. Absent = open-ended. |
| `supersedes` | concept ID | This concept replaces the named one. Declared on the **new** concept only — unidirectional, so a generator can stamp it without touching the file it replaces. |
| `generated_by` | string (`<tool>@<version>`) | Presence marks this concept's frontmatter as generator-owned (see §4). Absence means permanently hand-authored. |

**Required** on `SLO`, `Alert`, `Runbook`, and hand-authored `Subsystem` concepts (i.e. `generated_by` absent): `owner`, `reviewed`, `review_interval`. These are the types where staleness is operationally dangerous — a runbook step for infra that no longer exists, an SLO target nobody re-validated. When `generated_by` is present, `reviewed`/`review_interval` become optional: a structurally-derived fact (e.g. "this Subsystem exists in Terraform state") doesn't need a human review cadence the way judgment-layer content does.

A `reviewed` date with no corresponding change in substance is **attestation, not correctness** — a green `reviewed` field on a substantively stale runbook is worse than an obviously old one, because it manufactures false confidence at 2am. `valid_from`/`valid_until` is the mechanism that actually answers "is this still true," not `reviewed`.

---

## 3. Typed-relationship vocabulary

OKF's own spec has no typed-relationship vocabulary — link semantics live entirely in prose. That's fine for human narrative but not enough for a validator to enforce cardinality or catch a runbook link pointing at the wrong type. **We close this gap with structured frontmatter reference fields**, validated against the concept's actual `type`. Markdown prose links remain, and remain the right way to write `index.md`/navigation — they're just not what the validator's graph pass reads.

| Field | On type | Points to type | Cardinality |
|---|---|---|---|
| `slos` | `CustomerJourney` | `SLO` | ≥1, required |
| `subsystems` | `CustomerJourney` | `Subsystem` | 0+ |
| `slos` | `Service` | `SLO` | 0+ |
| `journeys` | `Subsystem` | `CustomerJourney` | 0+ (informational back-ref) |
| `service` | `Subsystem` | `Service` | 0 or 1 |
| `data_source` | `Metric` | `DataSource` | 0 or 1 |
| `data_source` | `SLI` | `DataSource` | 0 or 1 |
| `ratio_metric.good`, `ratio_metric.total` | `SLI` | `Metric` | required if `ratio_metric` used |
| `threshold_metric` | `SLI` | `Metric` | required if `threshold_metric` used |
| `sli` | `SLO` | `SLI` | exactly 1, required |
| `journey` | `SLO` | `CustomerJourney` | 0 or 1 (informational back-ref) |
| `slo` | `Alert` | `SLO` | exactly 1, required |
| `runbook` | `Alert` | `Runbook` | exactly 1, required |
| `alerts` | `Runbook` | `Alert` | 0+ (informational back-ref) |

---

## 4. Generated-vs-curated boundary

**Generators must never overwrite hand-authored bodies.** The signal is the `generated_by` frontmatter field (§2):

- **Absent** → the concept is permanently hand-authored. This applies to every `CustomerJourney`, `Runbook`, and the rationale/target content of every `SLO` — a generator will never produce runbook prose or explain why a journey matters. That expectation should stay reset; it is not a v1 limitation to be lifted later.
- **Present** (`generated_by: terraform-okf@0.1`, etc.) → the concept's **frontmatter is fully owned by the generator** and gets rewritten on every run, deterministically, from the source of truth (state file, ApplicationSet). The **body markdown is seeded once on first creation and never touched again** — this is the [erd2okf](https://github.com/thorsti/erd2okf) model (its own author describes it as "frontmatter wird bei jeder Generierung aus der DB neu geschrieben, die DB ist system of record; Regenerationen fassen den Body nie an").

In the pilot bundle (this repo, today) nothing is generated — no `generated_by` field appears anywhere, because no generator exists yet (see `generators/*/MAPPING.md` for sketches, not implementations). The first type expected to carry `generated_by` once a Terraform or ArgoCD generator lands is `Subsystem`.

---

## 5. Cardinality / integrity rules (validator-enforced)

Enforced by `validator/` in `--strict` mode (warnings only otherwise, per OKF's permissive-by-default conformance contract):

1. Every `CustomerJourney` has ≥1 `slos`, each resolving to `type: SLO`.
2. Every `SLO` has exactly 1 `sli`, resolving to `type: SLI`.
3. Every `Alert.runbook` resolves to `type: Runbook`.
4. Every `Alert.slo` resolves to `type: SLO`.
5. `SLI.data_source`, if present, resolves to `type: DataSource`.
6. No orphaned `Subsystem` — every `Subsystem` must be referenced by ≥1 `CustomerJourney.subsystems` or by a `Service`.
7. No cycles in the `supersedes` graph.
8. `SLO`, `Alert`, `Runbook`, and hand-authored `Subsystem` concepts have non-empty `owner`, `reviewed`, `review_interval`.
9. Every informational back-ref field agrees with the forward field it mirrors, in both directions: if `CustomerJourney.subsystems` lists a `Subsystem`, that `Subsystem`'s `journeys` must list the journey back (and vice versa); same for `CustomerJourney.slos` ↔ `SLO.journey` and `Alert.runbook` ↔ `Runbook.alerts`. These fields restate the same fact from both ends with nothing else keeping them in sync, so drift between them is treated as an error, not just a lint warning.

Rules 1–7 and 9 are graph-pass rules (structural, over the concept-ID reference graph). Rule 8 is a field-pass rule (per-concept, no graph traversal needed). Kept as separate passes in the validator — see `validator/okf_validator/`.

---

## 6. Per-type frontmatter reference

Fields not listed in §2 (cross-cutting) or §3 (typed relationships). `resource` conventions per type are the load-bearing part — this is how each documentation concept points at its executable counterpart.

### `CustomerJourney`
- **Required**: `title`, `description`
- **Optional**: `resource` (link to a dashboard summarizing the journey, if one exists)

### `Service`
- **Required**: `title`
- **Optional**: `description`

### `Subsystem`
- **Required**: `title`, `resource` (source repo path, Terraform module address, or ArgoCD Application name)
- **Optional**: `description`

### `DataSource`
- **Required**: `title`, `resource` (Prometheus instance URL or job selector)
- **Optional**: `description`

### `Metric`
- **Required**: `title`, `resource` (PromQL expression or Grafana panel URL)
- **Optional**: `description`

### `SLI`
- **Required**: `title`, `description`, exactly one of `ratio_metric: {good, total}` or `threshold_metric`
- **Optional**: `resource` (link to a formal SLI spec if one is ever authored elsewhere)

### `SLO`
- **Required**: `title`, `description`, `target` (e.g. `"99.9%"`), `time_window` (e.g. `"30d rolling"`)
- **Optional**: `resource` (link to an executable OpenSLO/Sloth spec, if the target is ever formalized there — nothing requires this to exist)

### `Alert`
- **Required**: `title`, `description`, `severity` (`critical` \| `warning` \| `info`), `resource` (the Alertmanager rule this documents)
- **Optional**: `notify` (plain string — team/channel, not a linked concept), `condition_summary` (prose restatement of the trigger condition, for humans; not authoritative — `resource` is)

### `Runbook`
- **Required**: `title`, `description`
- **Optional**: none beyond the cross-cutting required set in §2

---

## Sources consulted

- OKF spec: `github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md`
- OpenSLO: `github.com/OpenSLO/OpenSLO` (README + spec files, v1 fields; v2alpha explicitly unstable, not cited)
- KCP: `github.com/Cantara/knowledge-context-protocol` (`SPEC.md` §4.22, `schema/knowledge-schema.json`, `cli/src/validator.ts`)
- erd2okf: `github.com/thorsti/erd2okf`
- `okf-lint`: `github.com/thisismydesign/okf-lint` · `okf-conformance`: `github.com/Sudhakaran88/okf-conformance`
