# ArgoCD ApplicationSet → OKF mapping sketch

**Status: sketch, not implemented.** Same shape as `../terraform/MAPPING.md` — read that one first for the shared determinism/merge-boundary rules, which this doesn't repeat.

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
- Same rule as Terraform: **never invents `CustomerJourney` links** — a generated `Subsystem` starts unreferenced; a human wires it into a journey.

## Determinism & merge boundary

Identical to `../terraform/MAPPING.md`: `generated_by: argocd-okf@<version>`, frontmatter fully rewritten from the resolved ApplicationSet output each run, body seeded once and never touched again, `check`/`generate` split, content-hash-gated `timestamp` bumps, stale-not-deleted handling when an Application disappears from the generator output.
