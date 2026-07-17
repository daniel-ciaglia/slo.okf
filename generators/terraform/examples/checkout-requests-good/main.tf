# Prototype: reproduces bundle/metrics/checkout-requests-good.md.

module "checkout_requests_good" {
  source = "../../modules/okf-metric"

  bundle_root = "${path.module}/output"
  id          = "checkout-requests-good"

  title       = "Checkout API requests (successful)"
  description = "Successful (non-5xx) request count to the checkout API."
  resource    = "sum(rate(checkout_api_requests_total{status!~\"5..\"}[5m]))"

  owner       = "checkout-team"
  tags        = ["prometheus"]
  data_source = "datasources/prometheus-prod"

  freetext = "The numerator for [checkout API availability](../slis/checkout-availability.md)."
}

output "metric_id" {
  value = module.checkout_requests_good.id
}

output "metric_filename" {
  value = module.checkout_requests_good.filename
}
