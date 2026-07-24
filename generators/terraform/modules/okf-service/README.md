# okf-service

A Terraform module that writes/updates one OKF `Service` concept file. Same contract and
shared internal engine as `../okf-subsystem/` and `../okf-datasource/` — see
`../okf-subsystem/README.md` for the full write-up, not repeated here.

**v0.2.0 changed what `Service` is.** It's no longer "pure grouping, no fields of its own
beyond description" — see VOCABULARY.md's "`CustomerJourney` vs `Service`" note in §1 and its
Changelog. It's now a cohesive, owned unit of infrastructure: still no `owner`/`reviewed`/
`review_interval` requirement in `models.py` regardless of `generated_by`, but it gained real
topology and an optional `resource`. Typed-relationship fields, all stated explicitly by the
human calling the module (never inferred, same convention as `okf-subsystem`'s `services`):

- `slos` (0+) — forward link to `SLO` concept IDs grouped under this service.
- `subsystems` (0+, informational back-ref) — mirrors `Subsystem.services` from the other end;
  needs the matching `Subsystem` (hand-authored or its own `okf-subsystem` call) to actually
  list this `Service` in its `services` field, or rule 9's symmetry check flags the drift. A
  `Subsystem` can list more than one `Service` (e.g. a shared Redis instance), in which case it
  shows up in each of their `subsystems` back-refs.
- `journeys` (0+, informational back-ref) — mirrors `CustomerJourney.services`; same
  symmetry requirement.
- `parent` (0 or 1) / `children` (0+, informational back-ref of the child's `parent`) — for
  nesting one `Service` under another, e.g. an umbrella platform service. Not used by any real
  `bundle/services/*.md` file yet; see `../../examples/checkout-platform/` for a synthetic
  demonstration.

## Example

See `../../examples/checkout-services/` — reproduces the real
`bundle/services/{cart-service,payment-service}.md` (migrated from `Subsystem` to `Service` in
v0.2.0, see `bundle/log.md`), including their mutual prose cross-link and `cart-service`'s
`subsystems` back-ref to the real `bundle/subsystems/cart-service-redis.md`.

```hcl
module "cart_service" {
  source = "path/to/modules/okf-service"

  bundle_root = "/path/to/slo.okf/bundle"
  id          = "cart-service"
  title       = "Cart Service"
  description = "Stores and mutates the customer's shopping cart before checkout begins."
  resource    = "git@example.com:acme/cart-service.git"
  owner       = "checkout-team"
  tags        = ["checkout"]
  journeys    = ["journeys/checkout"]
  subsystems  = ["subsystems/cart-service-redis"]

  freetext = "Owns cart state until checkout hands off to payment-service."
}
```
