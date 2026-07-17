# okf-metric

A Terraform module that writes/updates one OKF `Metric` concept file. Same contract and
shared internal engine as `../okf-subsystem/` — see `../okf-subsystem/README.md` for the full
write-up, not repeated here.

Structural difference: `resource` (a PromQL expression or Grafana panel URL) routinely
contains YAML-significant characters — quotes, `{`/`}`, colons — that would break an unquoted
scalar. This module always emits it YAML-single-quoted, escaping embedded single quotes the
YAML way (`'` → `''`), verified byte-identical against the hand-authored
`bundle/metrics/checkout-requests-good.md`'s own single-quoting convention.

## Example

See `../../examples/checkout-requests-good/` — reproduces
`bundle/metrics/checkout-requests-good.md`.
