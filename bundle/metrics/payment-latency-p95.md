---
type: Metric
title: Payment service p95 request latency
description: 95th percentile request duration for the payment service.
resource: 'histogram_quantile(0.95, sum(rate(payment_service_request_duration_seconds_bucket[5m])) by (le))'
data_source: datasources/prometheus-prod
owner: checkout-team
created: 2026-07-15
tags: [prometheus, latency]
---

# Payment service p95 request latency

Backs [payment service latency](../slis/payment-latency.md) as a threshold metric — the SLI asks
"how often does this stay under 800ms," not "what's the raw ratio."
