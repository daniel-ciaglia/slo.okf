---
type: Metric
title: Checkout API requests (successful)
description: Successful (non-5xx) request count to the checkout API.
resource: 'sum(rate(checkout_api_requests_total{status!~"5.."}[5m]))'
data_source: datasources/prometheus-prod
owner: checkout-team
created: 2026-07-15
tags: [prometheus]
---

# Checkout API requests (successful)

The numerator for [checkout API availability](../slis/checkout-availability.md).
