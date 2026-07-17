# okf-service

A Terraform module that writes/updates one OKF `Service` concept file. Same contract and
shared internal engine as `../okf-subsystem/` and `../okf-datasource/` — see
`../okf-subsystem/README.md` for the full write-up, not repeated here.

Structural difference: `Service` is "pure grouping, no fields of its own beyond description"
(VOCABULARY.md §1) — no `resource` field at all, and no `owner`/`reviewed`/`review_interval`
requirement in `models.py` regardless of `generated_by`. Its one typed-relationship field is
`slos` (VOCABULARY.md §3, 0+), a forward link to `SLO` concept IDs — stated explicitly by the
human calling the module, same convention as `okf-subsystem`'s `journeys`/`service`.

## Example

See `../../examples/checkout-service/` — synthetic, since the real `bundle/` has no
`services/` directory yet (`Service` is the one type the project's own docs note hasn't been
exercised in the pilot bundle).

```hcl
module "checkout_service" {
  source = "path/to/modules/okf-service"

  bundle_root = "/path/to/slo.okf/bundle"
  id          = "checkout-service"
  title       = "Checkout Service"
  owner       = "checkout-team"
  slos        = ["slos/checkout-availability-slo", "slos/payment-latency-slo"]
  freetext    = "Groups the checkout team's SLOs for reporting purposes."
}
```
