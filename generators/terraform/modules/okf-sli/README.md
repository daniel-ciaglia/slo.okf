# okf-sli

A Terraform module that writes/updates one OKF `SLI` concept file. Same contract and shared
internal engine as `../okf-subsystem/` — see `../okf-subsystem/README.md` for the full
write-up, not repeated here.

Structural difference: VOCABULARY.md §6 requires exactly one of `ratio_metric {good, total}` or
`threshold_metric`. Enforced with `lifecycle.precondition` on the `local_file` resource rather
than a `variable` `validation` block, because a validation block that needs to see *other*
variables (is `threshold_metric` also set?) requires Terraform >= 1.9 — this module (like the
rest of this project's Terraform modules) targets >= 1.3. Two preconditions:

- `ratio_metric_good` and `ratio_metric_total` must be set together or not at all.
- Exactly one of the ratio pair or `threshold_metric` must be set.

## Examples

- `../../examples/checkout-availability-sli/` — reproduces `bundle/slis/checkout-availability.md`
  (`ratio_metric` kind).
- `../../examples/payment-latency-sli/` — reproduces `bundle/slis/payment-latency.md`
  (`threshold_metric` kind).

Both exercised end to end: rendered, validated against `okf_validator`'s real `SLI` model,
confirmed idempotent, and confirmed the precondition fires when neither indicator (or both) is
set.
