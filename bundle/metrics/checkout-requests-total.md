---
type: Metric
title: Checkout API requests (total)
description: Total request count to the checkout API, all status codes.
resource: 'sum(rate(checkout_api_requests_total[5m]))'
data_source: datasources/prometheus-prod
owner: checkout-team
created: 2026-07-15
tags: [prometheus]
---

# Checkout API requests (total)

The denominator for [checkout API availability](../slis/checkout-availability.md).
