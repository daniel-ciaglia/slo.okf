# Prototype: reproduces bundle/alerts/checkout-error-budget-burn.md.

module "checkout_error_budget_burn" {
  source = "../../modules/okf-alert"

  bundle_root = "${path.module}/output"
  id          = "checkout-error-budget-burn"

  title       = "Checkout error budget burn"
  description = <<-EOT
    Fires when the checkout availability SLO's error budget is burning fast
    enough to exhaust it well before the 30-day window ends.
  EOT

  severity = "critical"
  resource = "https://alertmanager.prod.internal.example.com/#/alerts?filter=%7Balertname%3D%22CheckoutErrorBudgetBurn%22%7D"
  slo      = "slos/checkout-availability-slo"
  runbook  = "runbooks/checkout-degraded"
  notify   = "#checkout-oncall"

  condition_summary = <<-EOT
    Multi-window burn-rate condition: fast burn (1h window, 14.4x budget
    consumption) OR slow burn (6h window, 6x budget consumption). See
    `resource` for the actual Alertmanager rule -- this is a prose summary
    for humans, not the source of truth.
  EOT

  owner           = "checkout-team"
  reviewed        = "2026-07-15"
  review_interval = "90d"
  tags            = ["alerting", "revenue-critical"]

  freetext = "Backs [checkout API availability SLO](../slos/checkout-availability-slo.md). If this fires, go to\n[checkout degraded runbook](../runbooks/checkout-degraded.md)."
}

output "alert_id" {
  value = module.checkout_error_budget_burn.id
}

output "alert_filename" {
  value = module.checkout_error_budget_burn.filename
}
