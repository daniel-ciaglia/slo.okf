# Terraform → OKF mapping

**Status: prototype implemented for 7 of 9 vocabulary types.** `../modules/okf-<type>/` exists
for `Subsystem`, `DataSource`, `Service`, `Metric`, `SLI`, `SLO`, and `Alert` — all working
Terraform modules, each verified end-to-end (rendered, validated against `okf_validator`'s real
pydantic models, applied twice for idempotency, hand-edited and re-applied to confirm
preservation, deliberately broken to confirm they fail safe) against a stand-in for the
matching real `bundle/` file — see `../examples/`. `CustomerJourney` and `Runbook` deliberately
have no module — see "Types this doesn't cover" below. Not yet adopted for the real `bundle/`,
and not yet wired into any real infra codebase.

This supersedes the original design below (kept as "Alternatives considered" — the reasoning
for the change is worth keeping alongside the thing it changed).

## Approach: a module called at the definition site, not a generator over state

Rather than reconstructing topology after the fact by parsing `terraform show -json`, a
generic module is called directly from the Terraform code that defines a subsystem — the
network module, the database module, the service module — at the point a human is already
looking at and reasoning about that resource. The human supplies the OKF vocabulary's
structured fields as module inputs, plus free text describing anything the vocabulary doesn't
capture. This is a deliberate move of the human-authorship step to happen *once*, at
definition time, instead of "generate a stub, then a human edits it separately afterward" —
see "Alternatives considered" below for why the state-parsing design needed that second step
and why that turned out to be the weaker choice.

## Input

One module per concept type, so each has a tightly-typed variable schema matching
VOCABULARY.md §6 rather than one kitchen-sink object covering all 9 types — a single
fully-generic module would need every field `optional()` and conditional `validation` blocks
keyed on a `concept_type` string, trading away exactly the plan-time clarity typed variables
give per type. Modules exist for `Subsystem`, `DataSource`, `Service`, `Metric`, `SLI`, `SLO`,
and `Alert` (`../modules/okf-<type>/`, lowercased). The frontmatter-render/marker-preserve/
timestamp logic they share is factored into two internal modules, not meant to be called
directly:

- `../modules/internal/freetext-marker` — resolves the freetext body (extract from an existing
  file's markers, or seed) and reports whether the markers were intact.
- `../modules/internal/timestamps` — `created`/`timestamp` via `time_static`, given a content
  hash from the caller (see "Determinism" below).

Each type's module otherwise varies with what VOCABULARY.md §6 actually requires — `Service`
has no `resource` field at all; `Metric`'s `resource` (PromQL) is YAML-single-quoted since it
routinely contains braces/quotes/colons; `SLI` enforces "exactly one of `ratio_metric` or
`threshold_metric`" via a `lifecycle.precondition` rather than a `variable` `validation` block,
because a validation block that needs to see *another* variable requires Terraform >= 1.9,
and this project's modules target >= 1.3; `SLO`/`Alert` render their prose fields
(`description`, `condition_summary`) as YAML literal block scalars (`|-`) rather than the
folded style (`>`) the hand-authored bundle files use for the same fields, since a Terraform
string's embedded newlines should round-trip exactly, not get silently reflowed on next parse
— see `../modules/okf-slo/README.md` for the fuller reasoning. See each module's own README for
its specifics; not repeated here.

## Types this doesn't cover

- **`CustomerJourney` and `Runbook`**: VOCABULARY.md §4 is explicit that these are permanently
  hand-authored — "a generator will never produce runbook prose or explain why a journey
  matters... not a v1 limitation to be lifted later." Building a module for either would
  directly contradict that. There's also little a module would manage: both types are almost
  entirely prose, with no infra-derived structured fields to speak of (`Runbook`'s only
  required fields beyond the cross-cutting set are `title`/`description`; `CustomerJourney`'s
  are `title`/`description`/`slos`, all judgment calls). Decided, not just deferred.
- **`SLO`'s `target`/`time_window`/`description`**: VOCABULARY.md §4 singles these out too, in
  the same sentence as `CustomerJourney`/`Runbook`. Unlike those two, an `okf-slo` module was
  still built — see `../modules/okf-slo/README.md` for why passing these as Terraform inputs
  doesn't contradict §4 (the human is still the one deciding the value, same as any other
  field on any other module here) and the one hard rule that keeps it that way: these values
  must be literals a human typed into the module call, never derived from another resource's
  computed attribute.

Inputs, matching the four the design started from:

- `bundle_root` — path to the OKF bundle root.
- concept type — currently fixed per module (`okf-subsystem` always writes a `Subsystem`);
  file lands at `<bundle_root>/subsystems/<id>.md`.
- Required vocabulary fields (`title`, `resource`) plus optional ones (`description`, `owner`,
  `tags`, `service`, `journeys`) as typed Terraform variables, enforced with `validation`
  blocks at plan time — e.g. `id` must be a deterministic lowercase slug, `title`/`resource`
  must be non-empty. Plan-time errors, not a runtime failure deep in a generator script.
- `freetext` — human-authored Markdown, handled per "Merge / regenerate boundary" below.

## Determinism

Same requirement as the original design (a stable input must not produce a spurious diff every
run), met with Terraform-native primitives instead of an external content-hash-before-write
script:

- `time_static.created` — no `triggers`, so it's set once at first creation and never changes.
- `time_static.updated` — `triggers = { content_hash = sha256(stable_content) }`, where
  `stable_content` is the rendered frontmatter+body *excluding* the timestamp fields
  themselves. It only re-stamps when something meaningful actually changed — verified: a
  second `terraform plan` with unchanged inputs reports "No changes," and `timestamp` only
  advances on an apply that changes rendered content.
- Concept IDs (`var.id`) are validated as deterministic lowercase-hyphen slugs, not
  incremental/random — same rule as the original design, just enforced by a `validation`
  block instead of a generator's slugging function.
- **Gotcha found while building `okf-datasource`**: the freetext seed (`var.freetext`, often a
  HCL heredoc) and the text extracted back out of an already-written file must be normalized
  identically before hashing/comparing — a heredoc's trailing newline, un-trimmed on the seed
  path but `trimspace()`-ed on the extraction path, caused a one-time phantom diff on the apply
  immediately after creation. Fixed in `../modules/internal/freetext-marker` by `trimspace()`-ing
  both paths the same way.
- **Second gotcha, found while building `okf-sli`**: `coalesce()` errors out if *every*
  argument is null or `""` — so a first-creation apply with an empty (default) `var.freetext`
  crashed instead of producing an empty body. Fixed by replacing the `coalesce()` in
  `../modules/internal/freetext-marker` with an explicit `local.extracted_freetext != null ?
  ... : ...` conditional, which tolerates a legitimately empty seed.

## Merge / regenerate boundary

- **Frontmatter**: fully owned by the module, rewritten every `terraform apply` from its
  inputs — never hand-edit it.
- **Body**: wrapped in `<!-- OKF:FREETEXT:BEGIN -->` / `<!-- OKF:FREETEXT:END -->` markers.
  `var.freetext` only seeds it on first creation (file doesn't exist yet). On every later
  apply, the module reads the current file with Terraform's `file()`/`fileexists()` builtins,
  extracts whatever's currently between the markers via `regex()`, and keeps it — a human can
  edit prose directly in the generated file and it survives regeneration, same guarantee the
  original design made via "seed once, never touch again," just implemented by reading the
  file back instead of an external tool refusing to touch it.
- If the markers are missing or malformed on an existing file (a human edit removed them, or
  the file predates this module), a `lifecycle.precondition` on the `local_file` resource fails
  the apply with an explanatory error instead of silently overwriting the body. Verified: state
  genuinely doesn't advance on a failed/corrupted-marker apply — no timestamp drift, no data
  loss, just a blocked apply until a human resolves it.

## Link derivation

Every typed-relationship field (VOCABULARY.md §3) is an explicit module input, stated by the
human calling the module — never inferred from anything: `okf-subsystem`'s `journeys`/
`service`, `okf-service`'s `slos`, `okf-metric`'s `data_source`, `okf-sli`'s `ratio_metric`/
`threshold_metric`/`data_source`, `okf-slo`'s `sli`/`journey`, `okf-alert`'s `slo`/`runbook`.
Same rule as the original design's "never invents CustomerJourney or SLO links," just
generalized: instead of a generator abstaining and leaving a concept unreferenced, the human
who's already at the call site states the link directly. Back-ref fields (§3's "informational"
column — `Subsystem.journeys`, `SLO.journey`) still need their forward-side counterpart
hand-authored to satisfy rule 9's symmetry check; no module writes both sides of a link.

Every module also outputs `concept_id` (frontmatter-ready ID, no `.md` — this project's own
convention, not an OKF requirement), `md_link` (ready-to-paste Markdown prose link), and
`relative_path` (same path, no Markdown formatting) — so one module's result can be wired
directly into another's input instead of hand-typing paths. These are pure functions of a
module's own `title`/`id` inputs, never derived from a resource inside the module, which is
why two modules can link to *each other* in prose with no dependency cycle — verified in
`../examples/cart-service/`. Full write-up in `../modules/okf-subsystem/README.md`'s "Linking
concepts to each other".

## `generated_by`

Stamped automatically as `terraform-okf-<type>@<module version>` (a `locals.tf` constant per
module, bumped on release) — VOCABULARY.md §4. This is what makes `owner`/`reviewed`/
`review_interval` optional on these concepts once present (§2). `models.py`'s `Subsystem`
validator already enforced this conditionally; building `okf-slo`/`okf-alert` surfaced that
`SLO`/`Alert` hadn't been given the same treatment (they required these fields unconditionally)
— fixed alongside this work, factored into one shared `_require_staleness_fields_unless_generated`
helper used by all three. `DataSource`/`Metric`/`SLI`/`Service` never required these fields in
the first place, `generated_by` or not.

## Known open questions (not solved yet)

- **Cross-repo write access**: if the bundle lives in a different repo than the infra code
  calling this module, whoever runs `terraform apply` needs write and commit access there too.
  Flagged, not addressed.
- **`CustomerJourney`/`Runbook`**: deliberately not built — see "Types this doesn't cover" above.
- **`valid_from`/`valid_until`/`supersedes`**: no module supports these cross-cutting fields yet
  (VOCABULARY.md §2). Consistent gap across all 7 types, not built until needed.
- **Real adoption**: nothing in the actual `bundle/` is generated by this yet; every file these
  modules reproduce (`cart-service.md`, `prometheus-prod.md`, etc.) stays hand-authored there
  until this is deliberately adopted for it.

---

## Alternatives considered

### Parsing `terraform show -json`

The original design for this generator, before the module-at-definition-site approach above.
Kept here because the reasoning for abandoning it is worth keeping, not because it's still the
plan.

**Why it was rejected:**

1. **The resource-type → concept-type table can never be complete.** It has to enumerate every
   resource type across every provider that might matter (`google_cloud_run_service`,
   `aws_rds_cluster`, ...) and falls back to "skip" for anything unlisted — meaning any shop
   with custom modules, less-common providers, or internal abstractions silently gets nothing
   for those resources. A human calling an explicit "document this" module at the point of
   definition has no such coverage gap — they decide, the same way this design already trusted
   humans to decide `CustomerJourney` wiring.
2. **State-JSON parsing only ever gives you structured facts, never the free text.** The
   "seed a stub body once, never touch it again" rule means the actual operational knowledge —
   why this topology looks the way it does, what's unusual about it — still had to be
   hand-added *after* generation, by someone who might not be the resource's author, in a
   different tool, at a different time. The module approach collects structured fields and
   free text from the same person, at the same time, in the same place.

The rest of this section is preserved as originally written, for reference.

#### Input

Parse `terraform show -json` (state or plan JSON) — **not raw HCL**. It's stable,
machine-friendly, and already resolves modules/variables/`for_each` into concrete resource
instances, which HCL parsing would have to reimplement badly.

```
terraform show -json terraform.tfstate > state.json
terraform-okf generate --state state.json --out subsystems/
```

#### Resource-type → concept-type table

| Terraform resource pattern | OKF concept | Notes |
|---|---|---|
| Compute/container resources relevant to a service (`google_cloud_run_service`, `aws_ecs_service`, `kubernetes_deployment`, etc.) | `Subsystem` | One concept per resource **instance** (post `for_each`/`count` expansion), not per resource block. |
| Managed data stores backing a service (`google_sql_database_instance`, `aws_rds_cluster`, etc.) | `Subsystem` | Same treatment — a datastore a journey depends on is part of its topology. |
| Networking/routing resources (load balancers, API gateways) | `Subsystem` | Only when directly in a modeled journey's dependency path — don't generate a concept for every VPC subnet. |
| Everything else (IAM bindings, DNS records, monitoring config resources) | *(skip)* | Out of scope for v1 — these are plumbing, not things an oncall agent navigates to. Revisit if a real need shows up. |

Module boundaries in the TF address (`module.checkout.module.payment.aws_ecs_service.api`) become `Subsystem.service` grouping hints — one `Service` concept per top-level module that maps onto a logical service, generated once and then treated as a stable anchor (regenerating a `Service` concept is out of scope; it's closer to curated than generated since a module boundary is a human's architectural decision).

#### Field mapping

- `resource:` → the real Terraform resource address (`module.checkout.aws_ecs_service.api`), not a synthetic URI — this is literally "the underlying asset."
- `tags:` → merged from the resource's own `tags`/`labels` attribute, if present.
- `title:` → derived from the resource's `name`/`display_name` attribute, falling back to the last segment of the resource address.

#### Link derivation

- `depends_on` (explicit TF `depends_on` plus implicit references discovered via `terraform show -json`'s `configuration.root_module.resources[].depends_on`) → cross-links between generated `Subsystem` concepts.
- Module nesting → `Subsystem.service` (see above).
- **Never invents `CustomerJourney` or `SLO` links** — those are hand-authored. A generated `Subsystem` starts unreferenced by any journey; a human wires `CustomerJourney.subsystems` to pull it into a journey's story. This keeps rule 6 (no orphaned Subsystem) an honest signal: an orphan after a TF apply means "this resource exists but nobody has said which journey it serves yet," which is worth surfacing, not silencing.

#### Determinism

Same input → byte-identical output, or every `terraform apply` produces a spurious diff that drowns real review (the `okc` prior-art bar). Concretely:

- Concept IDs are slugged deterministically from the TF resource address (lowercase, `.`/`/`→`-`), never from a random/incremental counter.
- Output is sorted by concept ID before writing.
- `timestamp` is **not** stamped from wall-clock time on every run — it only advances when the generated frontmatter actually changes (content-hash comparison before write, mirroring erd2okf's `check` vs `generate` split: `terraform-okf check` diffs against the source and exits non-zero on drift without writing; `terraform-okf generate` is the one that actually writes).

#### Merge / regenerate boundary

Every generated `Subsystem` file carries `generated_by: terraform-okf@<version>` (VOCABULARY.md §4):

- **Frontmatter**: fully rewritten from the TF state each run. TF state is system of record for these fields — no hand-edits to a generated `Subsystem`'s frontmatter survive a regeneration, by design.
- **Body**: written once on first creation (a stub description referencing the TF resource), then **never touched again**. If a human adds operational notes to a `Subsystem`'s body, those survive every future `terraform apply`.
- A resource removed from TF state does not silently delete its `Subsystem` file (that would break inbound links from hand-authored `CustomerJourney`s). Instead `terraform-okf check` flags it as "stale — resource no longer in state" so a human decides whether to delete it or mark `valid_until`.
