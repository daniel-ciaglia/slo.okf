# okf-datasource

A Terraform module that writes/updates one OKF `DataSource` concept file — the second
concept type using this pattern, alongside `../okf-subsystem/`. Same contract, same shared
internal engine (`../internal/freetext-marker`, `../internal/timestamps`); see
`../okf-subsystem/README.md` for the full write-up of that contract, not repeated here.

The one structural difference from `okf-subsystem`: `DataSource` has no `journeys`/`service`
typed-relationship fields of its own (VOCABULARY.md §3 — those are Subsystem-specific;
`DataSource` is pointed *at* by `Metric.data_source`/`SLI.data_source`, it doesn't point
anywhere itself), so this module's variable set is correspondingly smaller: `bundle_root`,
`id`, `title`, `resource`, `description`, `owner`, `tags`, `freetext`.

## Example

See `../../examples/prometheus-datasource/` — reproduces `bundle/datasources/prometheus-prod.md`.

```hcl
module "prometheus_datasource" {
  source = "path/to/modules/okf-datasource"

  bundle_root = "/path/to/slo.okf/bundle"
  id          = "prometheus-prod"
  title       = "Prometheus (prod)"
  resource    = "https://prometheus.prod.internal.example.com"
  owner       = "observability-team"
  tags        = ["prometheus"]
  freetext    = "Backs every metric referenced by the checkout journey's SLIs."
}
```

## Where this could go next

If a team's `Metric`/`SLI`/`SLO`/`Alert` definitions are themselves driven by a monitoring
provider's Terraform resources (e.g. Datadog's `datadog_monitor`,
`datadog_service_level_objective`), the same pattern extends naturally: an `okf-metric`,
`okf-sli`, etc. module, each a thin type-specific wrapper calling the same
`internal/freetext-marker` + `internal/timestamps` engine this module and `okf-subsystem` share.
Not built — noted because it's the natural next step if/when a real need for it shows up,
same as `okf-datasource` itself was until now.
