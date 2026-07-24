# ArgoCD ApplicationSet → OKF mapping sketch

**Status: sketch, not implemented.** This was originally written as "same shape as
`../terraform/README.md`, read that one first for the shared determinism/merge-boundary rules."
That's no longer true: the Terraform generator moved from parsing `terraform show -json` to a
module called at the definition site (`../terraform/modules/okf-subsystem/`, see
`../terraform/README.md`), which has no ArgoCD equivalent yet — there's no natural
"module called from the thing being defined" analogue for an ApplicationSet the way there is
for a Terraform resource, since the generator here still means parsing the *generator's
resolved output*, not something authored inline. This doc is therefore self-contained below
rather than deferring to Terraform's.

Whether ArgoCD should eventually get its own definition-site approach (e.g. an annotation or
label on the `Application`/`ApplicationSet` manifest itself, read back the same way Terraform's
module reads the OKF:FREETEXT markers) is an open question, not decided here.

## Input

The ApplicationSet's **generator output** (the resolved list of `Application` manifests it produces), not the `ApplicationSet` object itself — the generator (git directory generator, cluster generator, matrix generator, etc.) is what actually enumerates one entry per environment/cluster/service, and that resolved list is what maps onto topology.

```
argocd appset generate applicationset.yaml -o json > resolved.json
argocd-okf generate --applicationset resolved.json --out subsystems/
```

(`argocd appset generate` runs the generator locally without touching a live cluster — needed for the same determinism reason as `terraform show -json` over live `terraform apply` state: a repeatable, diffable input.)

## Resource-type → concept-type table

| ArgoCD object | OKF concept | Notes |
|---|---|---|
| Each resolved `Application` (one per ApplicationSet-generator entry) | `Subsystem` | One concept per Application — this is the deployment unit an oncall agent actually restarts/rolls back. |
| The manifests an `Application` deploys (`spec.source` → Helm chart / Kustomize output), specifically Kubernetes `Deployment`/`StatefulSet` objects within it | *(not separately generated)* | Modeling one `Subsystem` per underlying Deployment as well as per `Application` would double-count the same unit of ownership — the `Application` is where "who owns this, where's the source" lives. Revisit only if a journey genuinely needs sub-Application granularity. |
| `ApplicationSet` itself | *(not generated as a concept)* | It's a template/generator, not a running thing — nothing for an oncall agent to page about at 2am. |

## Field mapping

- `resource:` → the `Application`'s `spec.source.repoURL` + `spec.source.path` (where the manifests actually live), **not** the cluster-internal ArgoCD UI URL — `resource` should point at source, matching the Terraform generator's convention of "the real thing," not a dashboard.
- `title:` → `Application.metadata.name`.
- `tags:` → from `Application.metadata.labels`, same as Terraform's tag/label merge.

## Link derivation

- ApplicationSet generator-matrix entries (e.g. a matrix of `{cluster} × {service}`) → cross-links between the `Subsystem` concepts they produce, when the matrix itself encodes a dependency (e.g. a canary/stable pairing).
- `Application.spec.source` pointing at the same repo/module as a Terraform-generated `Subsystem` → cross-link the two (deployment-layer `Subsystem` ↔ infra-layer `Subsystem`) so a reader can walk from "what's running" to "what it runs on." Requires the Terraform and ArgoCD generators to agree on a shared ID-slugging convention for the same underlying resource — call this out explicitly as a coordination point if both generators are ever built, not something to solve speculatively now.
- Same rule as Terraform: **never invents `Service` links** — a generated `Subsystem` starts unreferenced. VOCABULARY.md v0.2.0 requires every `Subsystem` to declare exactly one `service`, so this can't stay unreferenced the way it could pre-v0.2.0; a human states that link explicitly, same convention as `../terraform/modules/okf-subsystem`'s `var.service`. Reaching a `CustomerJourney` is now two hops away (`Subsystem.service` → `Service`, then a human wires that `Service` into a journey via `CustomerJourney.services`), not something this generator states directly.

## Determinism & merge boundary

Every generated `Subsystem` file carries `generated_by: argocd-okf@<version>` (VOCABULARY.md §4):

- Concept IDs are slugged deterministically from the `Application`'s resolved identity (e.g.
  cluster/name), never from a random/incremental counter. Output is sorted by concept ID before
  writing, so the same generator-output input always produces byte-identical output.
- **Frontmatter**: fully rewritten from the resolved ApplicationSet output each run — no
  hand-edits to a generated `Subsystem`'s frontmatter survive a regeneration, by design.
- **Body**: written once on first creation (a stub description referencing the `Application`),
  then never touched again — same "seed once, hand-authored notes survive forever after"
  guarantee as VOCABULARY.md §4 describes generally, here implemented by the generator script
  simply refusing to touch the body region on any run after the first, rather than the
  marker-based read-back-and-preserve mechanism `okf-subsystem` uses (see the note above on why
  this generator doesn't have a definition-site equivalent yet).
- `timestamp` is **not** stamped from wall-clock time on every run — it only advances when the
  generated frontmatter actually changes (content-hash comparison before write): `argocd-okf
  check` diffs against the source and exits non-zero on drift without writing; `argocd-okf
  generate` is the one that actually writes.
- An `Application` that disappears from the generator's resolved output does not silently
  delete its `Subsystem` file (that would break inbound links from hand-authored `Service`
  concepts listing it in their `subsystems` back-ref). Instead `argocd-okf check` flags it as
  "stale — no longer in generator output" so a human decides whether to delete it or mark
  `valid_until`.
