---
type: SLO
title: Payment service latency SLO
description: >
  95th percentile payment request latency must stay under 800ms for at
  least 99.5% of each rolling 30-day window. A breach means checkout feels
  slow enough that customers abandon carts even when requests eventually
  succeed.
sli: slis/payment-latency
target: "99.5%"
time_window: 30d rolling
journey: journeys/checkout
owner: checkout-team
created: 2026-07-15
reviewed: 2026-07-15
review_interval: 90d
valid_from: 2026-07-15
tags: [latency, revenue-critical]
---

# Payment service latency SLO

Target: p95 latency under 800ms, at least 99.5% of the time, 30-day rolling window, backed by
[payment service latency](../slis/payment-latency.md).

## Why this exists separately from the availability SLO

A checkout request can succeed (HTTP 200) and still be slow enough that the customer gives up
before seeing the confirmation page. Availability alone wouldn't catch that — this SLO is what
does.

## If this is breaching

See [payment latency error budget burn](../alerts/payment-latency-error-budget-burn.md).
