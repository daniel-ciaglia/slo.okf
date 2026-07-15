---
type: SLI
title: Checkout API availability
description: Proportion of checkout API requests that complete without a server error.
ratio_metric:
  good: metrics/checkout-requests-good
  total: metrics/checkout-requests-total
data_source: datasources/prometheus-prod
owner: checkout-team
created: 2026-07-15
tags: [availability]
---

# Checkout API availability

`good / total`, both counters scraped from [Prometheus (prod)](../datasources/prometheus-prod.md).
Feeds the [checkout availability SLO](../slos/checkout-availability-slo.md).
