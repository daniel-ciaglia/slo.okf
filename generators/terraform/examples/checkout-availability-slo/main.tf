# Prototype: reproduces bundle/slos/checkout-availability-slo.md (minus valid_from, which
# no okf-<type> module in this prototype supports yet — out of scope, same as
# supersedes/valid_until elsewhere).

module "checkout_availability_slo" {
  source = "../../modules/okf-slo"

  bundle_root = "${path.module}/output"
  id          = "checkout-availability-slo"

  title       = "Checkout API availability SLO"
  description = <<-EOT
    The checkout API must succeed at least 99.9% of the time over a rolling
    30-day window. This is the primary revenue-protection SLO for the checkout
    journey; breaching it means customers cannot complete purchases.
  EOT

  sli         = "slis/checkout-availability"
  target      = "99.9%"
  time_window = "30d rolling"
  journey     = "journeys/checkout"

  owner           = "checkout-team"
  reviewed        = "2026-07-15"
  review_interval = "90d"
  tags            = ["availability", "revenue-critical"]

  freetext = <<-EOT
    Target: 99.9% success rate, 30-day rolling window, backed by
    [checkout API availability](../slis/checkout-availability.md).

    ## Why 99.9% and not higher

    99.9% allows roughly 43 minutes of full downtime (or a proportionally larger amount of partial
    degradation) per 30-day window before the error budget is exhausted. That's deliberately generous
    relative to a typical 99.95%+ target for pure infra availability — checkout also depends on
    [payment-service](../subsystems/payment-service.md), an external dependency the checkout team
    doesn't fully control, and a target that's frequently breached by factors outside the team's
    control just trains everyone to ignore the alert.

    ## If this is breaching

    See [checkout error budget burn](../alerts/checkout-error-budget-burn.md).
  EOT
}

output "slo_id" {
  value = module.checkout_availability_slo.id
}

output "slo_filename" {
  value = module.checkout_availability_slo.filename
}
