# Prototype: reproduces bundle/slis/checkout-availability.md (ratio_metric kind).

module "checkout_availability_sli" {
  source = "../../modules/okf-sli"

  bundle_root = "${path.module}/output"
  id          = "checkout-availability"

  title       = "Checkout API availability"
  description = "Proportion of checkout API requests that complete without a server error."

  ratio_metric_good  = "metrics/checkout-requests-good"
  ratio_metric_total = "metrics/checkout-requests-total"
  data_source        = "datasources/prometheus-prod"

  owner = "checkout-team"
  tags  = ["availability"]

  freetext = "`good / total`, both counters scraped from [Prometheus (prod)](../datasources/prometheus-prod.md).\nFeeds the [checkout availability SLO](../slos/checkout-availability-slo.md)."
}

output "sli_id" {
  value = module.checkout_availability_sli.id
}

output "sli_filename" {
  value = module.checkout_availability_sli.filename
}
