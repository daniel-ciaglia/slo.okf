module "payment_latency_sli" {
  source = "../../modules/okf-sli"

  bundle_root = "${path.module}/output"
  id          = "payment-latency"

  title       = "Payment service latency (p95 under threshold)"
  description = "Proportion of the time p95 payment request latency stays under 800ms."

  threshold_metric = "metrics/payment-latency-p95"
  data_source      = "datasources/prometheus-prod"

  owner = "checkout-team"
  tags  = ["latency"]

  freetext = "A threshold indicator, not a ratio — see [payment latency p95](../metrics/payment-latency-p95.md).\nFeeds the [payment latency SLO](../slos/payment-latency-slo.md)."
}
