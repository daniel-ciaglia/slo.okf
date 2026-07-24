# SRE OKF Vocabulary v0.2.0

A controlled `type` vocabulary and frontmatter convention for documenting SRE customer journeys — SLI/SLO/alert/runbook chains — as an [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf) (OKF v0.1) bundle.

**Non-goal, stated up front**: a concept file in this vocabulary computes nothing. `type: SLO` is documentation *about* an SLO — target, rationale, owner — not an executable specification. Executable definitions (Prometheus recording rules, Alertmanager rules, Sloth specs) live in their own tooling and are referenced from here via the `resource` field. If you're looking for something that evaluates burn rate, this isn't it; follow `resource` to the thing that does.

Naming donor: [OpenSLO](https://github.com/OpenSLO/OpenSLO)'s object model, for kind names and field shapes only — **no runtime dependency**. OpenSLO has never cut a tagged release and its `main` branch has been idle since 2025-10-09; we borrow its vocabulary because it's a well-thought-through domain schema, not because it's a moving target we track.

Temporal convention: borrowed from [KCP](https://github.com/Cantara/knowledge-context-protocol)'s `valid_from`/`valid_until`/`supersedes` field *names* only, as plain OKF frontmatter — no KCP manifest format, no signing, no trust/federation machinery. KCP itself is a 5-month-old, effectively single-author project; treat the field names as a decent naming convention, not an endorsement of KCP as infrastructure.

**Tie-breaker**: OpenSLO and KCP are naming/field-shape donors only (see above) — neither is an authority on what an SRE concept actually *means*. Where a term's meaning is ambiguous or sources disagree (as happened with `CustomerJourney` vs `Service`, see §1), this vocabulary defers to Google's [SRE Book](https://sre.google/sre-book/) and [SRE Workbook](https://sre.google/workbook/) as the deciding reference.

---

## 1. Type vocabulary

| `type` | Origin | Role |
|---|---|---|
| `CustomerJourney` | SRE-native (Google SRE Workbook "critical user journey") | Top of the graph. An end-to-end path a customer/request takes, e.g. checkout. Links ≥1 `SLO`, and 0+ `Service`s it depends on. Routinely crosses `Service` boundaries. |
| `Service` | OpenSLO `Service`, extended | A cohesive, owned unit of infrastructure — "the thing a team is on call for." Groups the `Subsystem`s it's made of, and optionally the `SLO`s attributed to it; can nest under a parent `Service`. |
| `Subsystem` | SRE-native | An infra/deployment topology node (a Terraform resource, an ArgoCD Application) — the atomic, individually-monitored leaf. Belongs to one or more `Service`s — most commonly one, but a single shared piece of infra (a Redis instance, a DBMS) legitimately backs more than one independently-owned `Service`. Generator-owned once generators exist. |
| `DataSource` | OpenSLO `DataSource` | A telemetry source — a Prometheus instance/job, not a single metric. |
| `Metric` | SRE-native | One concrete, named metric (a PromQL expression or dashboard panel). |
| `SLI` | OpenSLO `SLI` | An indicator definition: what "good" and "total" mean, referencing `Metric`/`DataSource`. |
| `SLO` | OpenSLO `SLO`, simplified | A target + rationale for exactly one `SLI`. |
| `Alert` | Collapses OpenSLO `AlertPolicy` + `AlertCondition` | A documented alert: what it means, what severity, which runbook to open. |
| `Runbook` | SRE-native | Oncall prose. Never generated — see §4. |

### `CustomerJourney` vs `Service`: two axes, not a redundancy

Both types can point at `SLO`, which invites the question of why both exist. They answer different
questions over the same underlying SLO graph:

- **`CustomerJourney` answers "why does this matter to a customer."** Per the
  [SRE Workbook's critical-user-journey (CUJ) technique](https://sre.google/workbook/implementing-slos/),
  a journey is defined by what the customer is trying to do, not by who owns the systems along the
  way — and it routinely **crosses multiple `Service`s**. The pilot bundle's `checkout` journey
  spans three separately-owned services (cart, payment, checkout-api). A journey with zero SLOs isn't a
  journey yet, just an idea — `slos` stays required, `≥1`.
- **`Service` answers "who is on call, what runs as a unit."** This is OpenSLO's original sense
  (`spec.service` — a single ownership scope an SLO is filed under), extended here with real
  topology (`subsystems`) since in practice a service *is* the infrastructure it's made of, not
  just a label. A service can legitimately have **zero SLOs of its own** — plenty of supporting
  infrastructure matters operationally without yet having a dedicated SLO — so `slos` stays optional, `0+`.

The asymmetry (`CustomerJourney.slos` required-`≥1`, `Service.slos` optional-`0+`) is the
machine-checkable signal for which type a given grouping should be. If you're modeling something
that must be true before it counts as "tracked," it's a journey. If you're modeling something
someone owns and pages on, whether or not it has its own SLO yet, it's a service.

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
| `services` | `CustomerJourney` | `Service` | 0+ |
| `journeys` | `Service` | `CustomerJourney` | 0+ (informational back-ref) |
| `slos` | `Service` | `SLO` | 0+ |
| `subsystems` | `Service` | `Subsystem` | 0+ (informational back-ref) |
| `parent` | `Service` | `Service` | 0 or 1 |
| `children` | `Service` | `Service` | 0+ (informational back-ref) |
| `services` | `Subsystem` | `Service` | ≥1, required |
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

In the pilot bundle (this repo, today) nothing is generated — no `generated_by` field appears anywhere, because no generator exists yet (see `generators/*/README.md` for sketches, not implementations). The first type expected to carry `generated_by` once a Terraform or ArgoCD generator lands is `Subsystem`.

---

## 5. Cardinality / integrity rules (validator-enforced)

Enforced by `validator/` in `--strict` mode (warnings only otherwise, per OKF's permissive-by-default conformance contract):

1. Every `CustomerJourney` has ≥1 `slos`, each resolving to `type: SLO`.
2. Every `SLO` has exactly 1 `sli`, resolving to `type: SLI`.
3. Every `Alert.runbook` resolves to `type: Runbook`.
4. Every `Alert.slo` resolves to `type: SLO`.
5. `SLI.data_source`, if present, resolves to `type: DataSource`.
6. Every `Subsystem` has at least one entry in `services`, each resolving to `type: Service` — a `Subsystem` can no longer be orphaned, because membership in a `Service` isn't optional. More than one entry is legitimate: a single shared piece of infra can back more than one `Service`.
7. No cycles in the `supersedes` graph, or in the `Service.parent` graph.
8. `SLO`, `Alert`, `Runbook`, and hand-authored `Subsystem` concepts have non-empty `owner`, `reviewed`, `review_interval`.
9. Every informational back-ref field agrees with the forward field it mirrors, in both directions: if `CustomerJourney.services` lists a `Service`, that `Service`'s `journeys` must list the journey back (and vice versa); same for `Subsystem.services` ↔ `Service.subsystems`, `Service.parent` ↔ `Service.children`, `CustomerJourney.slos` ↔ `SLO.journey`, and `Alert.runbook` ↔ `Runbook.alerts`. These fields restate the same fact from both ends with nothing else keeping them in sync, so drift between them is treated as an error, not just a lint warning. For `Subsystem.services` ↔ `Service.subsystems` this now checks agreement pairwise across a many-to-many relationship — a shared `Subsystem` must appear in the `subsystems` list of *every* `Service` it names, not just one.

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
- Google SRE Book: `sre.google/sre-book/` · SRE Workbook: `sre.google/workbook/` (tie-breaker authority, see top of file)

---

## Changelog

### v0.2.0

Breaking schema change, surfaced by building a second, independent bundle and finding that
`CustomerJourney`/`Service`/`Subsystem` couldn't express its infrastructure without a workaround.

- **`Service` gains real topology**: `subsystems` (informational back-ref of `Subsystem.services`),
  and `parent`/`children` for nesting one `Service` under another. It's no longer a bare SLO
  label — see the new "`CustomerJourney` vs `Service`" note in §1 for why both types still earn
  their keep despite both pointing at `SLO`.
- **`Subsystem.service` tightened from `0 or 1` to exactly `1`, required**, then widened again to
  **`Subsystem.services` (1+, required)** once a real bundle turned up a `Subsystem` (a shared
  Redis instance, a DBMS) backing more than one independently-owned `Service` — exactly-1 had no
  way to express that without picking one owner arbitrarily or duplicating the concept file per
  consumer. A `Subsystem` that doesn't belong to any `Service` still doesn't validate (rule 6, §5);
  the orphan-prevention goal only ever needed a lower bound, not an upper one.
  - **Considered and rejected**: keeping `Subsystem.service` singular (one accountable on-call
    owner, matching the SRE Book/Workbook's "a Service is the thing a team is on call for") and
    adding a separate 0+ "consumes" field on `Service` for non-owning dependents — mirroring how
    `CustomerJourney.services` already separates "depends on" from ownership. Rejected for the
    simpler shared-`Subsystem` model actually adopted: one list field, one mental model, at the
    cost of no longer distinguishing "owns" from "merely uses" when a `Subsystem` lists more than
    one `Service` — all listed `Service`s are equally on the hook for it. Revisit if that
    distinction becomes operationally necessary; it layers back in without conflicting with this
    shape.
  - `Service.subsystems` (back-ref) is unaffected — it was always `0+`. Rule 9 (§5)'s back-ref
    symmetry check now holds pairwise across every `Service` a shared `Subsystem` names, not just
    one.
- **`CustomerJourney.subsystems` removed, replaced by `CustomerJourney.services` (0+).** A
  journey names the services it depends on; the subsystems inside those services are an
  implementation detail the journey doesn't need to enumerate. `Subsystem.journeys` is removed
  for the same reason — a `Subsystem`'s only outward link is now `services`.
- Rule 7 (§5) extended to also forbid cycles in the new `Service.parent` graph, alongside the
  existing `supersedes` cycle check.
- New tie-breaker rule (top of file): when sources disagree on a definition, Google's SRE
  Book/Workbook wins over OpenSLO or KCP.

The pilot `bundle/` was migrated to this shape in a same-day follow-up (see `bundle/log.md`,
2026-07-22 entry): `cart-service`/`checkout-api`/`payment-service` became `Service` concepts, and
one new leaf `Subsystem` (`cart-service-redis`) was added so the bundle keeps demonstrating all 9
types. The Terraform generators (`generators/terraform/modules/okf-subsystem`,
`generators/terraform/modules/okf-service`) and their examples were migrated in a second
same-day follow-up — see `generators/terraform/README.md`'s "Migrated to VOCABULARY.md v0.2.0"
note. The ArgoCD generator remains an unimplemented mapping sketch, unaffected either way.

### v0.1

Initial vocabulary: 9 types, cross-cutting frontmatter fields, typed-relationship vocabulary,
generated-vs-curated boundary, cardinality rules. See `bundle/log.md` for the pilot bundle this
version shipped with.
