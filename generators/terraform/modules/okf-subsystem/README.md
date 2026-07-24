# okf-subsystem

A Terraform module that writes/updates one OKF `Subsystem` concept file, called from
wherever in an infra codebase a network, database, or service is actually defined —
instead of reverse-engineering topology from `terraform show -json` after the fact
(see `../../README.md`, whose state-parsing approach this module is an alternative to).

## Contract

- **Frontmatter is fully owned by this module**, rewritten every `terraform apply`
  from the module's inputs. Never hand-edit it — it will be overwritten.
- **`var.freetext` is rendered directly in the body, below the title, and rewritten
  every `terraform apply`** — same lifecycle as the frontmatter, not a seed. It never
  touches the `OKF:FREETEXT` markers.
- **The body between the `OKF:FREETEXT` markers is yours, always.** This block starts
  empty and is never written to by this module's inputs — a human adds notes directly
  in `bundle/subsystems/*.md`, and whatever's between the markers on disk is preserved
  verbatim on every later apply, same as a hand-authored concept would. Implemented by
  the shared `../internal/freetext-marker` module (see below), called with no seed.
  Editing `var.freetext` in Terraform config keeps landing on every apply, unlike the
  human notes block — if you hand-edit the generated prose above the markers expecting
  it to stick, it won't; move that text below the markers instead.
- If the markers are missing or malformed on a file that already exists (e.g. a human
  edit removed them, or the file predates this module), `terraform apply` **fails with
  an explanatory error** instead of silently overwriting the body. Restore the markers,
  or delete the file to let Terraform recreate it — `var.freetext` renders fresh either
  way, and the human notes block resets to empty.
- `created` is stamped once, at first creation, and never changes again.
- `timestamp` only advances when the rendered content (frontmatter + resolved body,
  before stamping) actually changes hash-for-hash — not on every apply — via
  `time_static.updated`'s `triggers`. A no-op apply produces a byte-identical file and
  no timestamp bump. Implemented by the shared `../internal/timestamps` module.
- `generated_by: terraform-okf-subsystem@<version>` is stamped automatically
  (VOCABULARY.md §4); `owner`/`reviewed`/`review_interval` are therefore optional
  (VOCABULARY.md §2, `models.py`'s `Subsystem` validator).
- **`var.services` is required, >=1 entry, not optional** (v0.2.0 tightened `Subsystem.service`
  from `0 or 1` to exactly `1`, then widened it to `Subsystem.services` (1+) once a real bundle
  needed one `Subsystem` — a shared Redis instance, say — to back more than one independently-owned
  `Service`; see VOCABULARY.md's Changelog). A `Subsystem` with no `Service` still doesn't
  validate, so this module fails at plan time (`validation` block) rather than writing a file the
  field pass would reject anyway.
- **No `journeys` input** (removed in v0.2.0 — `Subsystem.journeys` no longer exists in the
  vocabulary; a journey now reaches infrastructure via `CustomerJourney.services` →
  `Service`, not through individual `Subsystem`s). If you're migrating a pre-v0.2.0 call to
  this module, drop `journeys = [...]` and add the required `services = [...]` instead.

## Example

See `../../examples/cart-service-redis/` — a stand-in Terraform module call reproducing
`bundle/subsystems/cart-service-redis.md`'s content as if it were generated at the point
the cache is defined, writing into a local `output/` (not the real `bundle/`, which stays
hand-authored until this module is adopted for real).

```hcl
module "cart_service_redis_subsystem" {
  source = "path/to/modules/okf-subsystem"

  bundle_root = "/path/to/slo.okf/bundle"
  id          = "cart-service-redis"

  title       = "Cart Service Redis"
  description = "Session/cart-state cache backing cart-service."
  resource    = "module.cart_service.aws_elasticache_replication_group.session_cache"
  services    = ["services/cart-service"]

  owner = "checkout-team"
  tags  = ["checkout", "redis"]

  freetext = "Holds in-progress cart state so a page reload mid-checkout doesn't lose the customer's cart."
}
```

## Linking concepts to each other

Every `okf-<type>` module exposes outputs for wiring one module's result into another's
input, so you don't hand-type relative paths or IDs and risk getting them wrong:

- **`concept_id`** — bundle-root-relative ID, no `.md` (e.g. `"subsystems/cart-service"`).
  This project's convention for **frontmatter typed-relationship fields**
  (`VOCABULARY.md §3`: `journeys`, `services`, `data_source`, `sli`, `slo`, `runbook`, `slos`,
  etc.), matching `okf_validator`'s `concept_id_for()` exactly. **Not an OKF spec
  requirement** — OKF itself has no typed-relationship vocabulary at all ("link semantics
  live entirely in prose," `VOCABULARY.md §3`); this ID format is this project's own
  invention, only enforced by this project's own validator.
- **`md_link`** — a ready-to-paste **Markdown prose link** using the concept's `title` as
  link text (e.g. `"[Cart Service Redis](../subsystems/cart-service-redis.md)"`), for the *body*
  freetext, not frontmatter. Assumes the link is written from a concept file in a
  *different* top-level bundle directory (the common case, since every type lives one
  level under `bundle_root`); for a same-directory link, strip the `"../<dir>/"` prefix
  (see `relative_path` below).
- **`relative_path`** — same relative path as `md_link` but without the Markdown
  brackets/title, for when you want custom link text instead of the concept's `title`.

```hcl
module "cart_service_postgres_subsystem" {
  source      = "path/to/modules/okf-subsystem"
  bundle_root = local.bundle_root
  id          = "cart-service-postgres"
  title       = "Cart Service Postgres"
  resource    = "module.cart_service.aws_db_instance.cart_state"
  services    = ["services/cart-service"]
  freetext    = "Durable store cart-service falls back to when the Redis cache misses."
}

module "cart_service_redis_subsystem" {
  source      = "path/to/modules/okf-subsystem"
  bundle_root = local.bundle_root
  id          = "cart-service-redis"
  title       = "Cart Service Redis"
  resource    = "module.cart_service.aws_elasticache_replication_group.session_cache"
  services    = ["services/cart-service"]
  # cart-service-postgres.md is in the same directory, so strip the "../subsystems/" prefix:
  freetext    = "Falls back to ${replace(module.cart_service_postgres_subsystem.md_link, "../subsystems/", "")} on a cache miss."
}
```

**Bidirectional links work with no dependency cycle.** The pair above (illustrative —
`cart-service-postgres` isn't in the real `bundle/`, only `cart-service-redis` is)
demonstrates two `Subsystem`s linking to *each other* in prose, both directions wired via
`md_link`, applying cleanly and staying idempotent — the same property
`../../examples/cart-service-redis/`'s predecessor verified before the v0.2.0 migration
retired the `okf-subsystem`-typed `cart-service`/`payment-service` example pair (both are
`Service`s now — see `../okf-service/README.md`'s own bidirectional-link example instead).
This works because `concept_id`/`md_link`/`relative_path` are pure functions of a module's own
`var.title`/`var.id` — never derived from `local_file`/`time_static` or any other resource
inside the module — so neither module's output actually depends on the other module's
resources being created first, even though the *values* reference each other.
(A different design, where these outputs derived from a resource attribute instead of an
input variable, would genuinely deadlock — Terraform would refuse to build that graph.)

## Shared internal engine

The marker-preserve and content-hash-gated-timestamp logic isn't specific to `Subsystem` — every
`okf-<type>` module (`okf-datasource`, `okf-service`, `okf-metric`, `okf-sli`, `okf-slo`,
`okf-alert`) needs the exact same behavior. Rather than duplicate it, all of them call two
internal modules (not meant to be used directly):

- `../internal/freetext-marker` — given a `filename` that may or may not exist yet and a
  `seed`, resolves the freetext body (extract-from-existing-markers, or seed) and reports
  whether the markers were intact.
- `../internal/timestamps` — given a `content_hash`, exposes `created` (stamped once) and
  `timestamp` (re-stamped only when the hash changes) via `time_static`.

Each `okf-<type>` module still owns its own `variables.tf` (so required/optional fields and
validation messages stay type-specific — VOCABULARY.md §6 differs per type) and its own
`templates/*.md.tftpl`, and is the one that actually writes the `local_file` with the
markers-intact precondition.

## Known open questions (not solved here)

- **Cross-repo write access**: if the bundle lives in a different repo than the
  infra code calling this module, whoever runs `terraform apply` needs write and
  commit access to the bundle repo too. Not addressed by this prototype.
- **`CustomerJourney`/`Runbook`**: deliberately not built — VOCABULARY.md §4 states these are
  permanently hand-authored; see `../../README.md`'s "Types this doesn't cover".
- **`valid_from`/`valid_until`/`supersedes`**: no `okf-<type>` module supports these
  cross-cutting fields yet (VOCABULARY.md §2).
