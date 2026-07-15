# Terraform → OKF mapping sketch

**Status: sketch, not implemented.** This documents the design a `terraform-okf` generator would follow. No code here yet.

## Input

Parse `terraform show -json` (state or plan JSON) — **not raw HCL**. It's stable, machine-friendly, and already resolves modules/variables/`for_each` into concrete resource instances, which HCL parsing would have to reimplement badly.

```
terraform show -json terraform.tfstate > state.json
terraform-okf generate --state state.json --out subsystems/
```

## Resource-type → concept-type table

| Terraform resource pattern | OKF concept | Notes |
|---|---|---|
| Compute/container resources relevant to a service (`google_cloud_run_service`, `aws_ecs_service`, `kubernetes_deployment`, etc.) | `Subsystem` | One concept per resource **instance** (post `for_each`/`count` expansion), not per resource block. |
| Managed data stores backing a service (`google_sql_database_instance`, `aws_rds_cluster`, etc.) | `Subsystem` | Same treatment — a datastore a journey depends on is part of its topology. |
| Networking/routing resources (load balancers, API gateways) | `Subsystem` | Only when directly in a modeled journey's dependency path — don't generate a concept for every VPC subnet. |
| Everything else (IAM bindings, DNS records, monitoring config resources) | *(skip)* | Out of scope for v1 — these are plumbing, not things an oncall agent navigates to. Revisit if a real need shows up. |

Module boundaries in the TF address (`module.checkout.module.payment.aws_ecs_service.api`) become `Subsystem.service` grouping hints — one `Service` concept per top-level module that maps onto a logical service, generated once and then treated as a stable anchor (regenerating a `Service` concept is out of scope; it's closer to curated than generated since a module boundary is a human's architectural decision).

## Field mapping

- `resource:` → the real Terraform resource address (`module.checkout.aws_ecs_service.api`), not a synthetic URI — this is literally "the underlying asset."
- `tags:` → merged from the resource's own `tags`/`labels` attribute, if present.
- `title:` → derived from the resource's `name`/`display_name` attribute, falling back to the last segment of the resource address.

## Link derivation

- `depends_on` (explicit TF `depends_on` plus implicit references discovered via `terraform show -json`'s `configuration.root_module.resources[].depends_on`) → cross-links between generated `Subsystem` concepts.
- Module nesting → `Subsystem.service` (see above).
- **Never invents `CustomerJourney` or `SLO` links** — those are hand-authored. A generated `Subsystem` starts unreferenced by any journey; a human wires `CustomerJourney.subsystems` to pull it into a journey's story. This keeps rule 6 (no orphaned Subsystem) an honest signal: an orphan after a TF apply means "this resource exists but nobody has said which journey it serves yet," which is worth surfacing, not silencing.

## Determinism

Same input → byte-identical output, or every `terraform apply` produces a spurious diff that drowns real review (the `okc` prior-art bar). Concretely:

- Concept IDs are slugged deterministically from the TF resource address (lowercase, `.`/`/`→`-`), never from a random/incremental counter.
- Output is sorted by concept ID before writing.
- `timestamp` is **not** stamped from wall-clock time on every run — it only advances when the generated frontmatter actually changes (content-hash comparison before write, mirroring erd2okf's `check` vs `generate` split: `terraform-okf check` diffs against the source and exits non-zero on drift without writing; `terraform-okf generate` is the one that actually writes).

## Merge / regenerate boundary

Every generated `Subsystem` file carries `generated_by: terraform-okf@<version>` (VOCABULARY.md §4):

- **Frontmatter**: fully rewritten from the TF state each run. TF state is system of record for these fields — no hand-edits to a generated `Subsystem`'s frontmatter survive a regeneration, by design.
- **Body**: written once on first creation (a stub description referencing the TF resource), then **never touched again**. If a human adds operational notes to a `Subsystem`'s body, those survive every future `terraform apply`.
- A resource removed from TF state does not silently delete its `Subsystem` file (that would break inbound links from hand-authored `CustomerJourney`s). Instead `terraform-okf check` flags it as "stale — resource no longer in state" so a human decides whether to delete it or mark `valid_until`.
