---
type: Alert
title: Payment latency error budget burn
description: >
  Fires when the payment latency SLO's error budget is burning fast enough
  to exhaust it well before the 30-day window ends.
severity: warning
resource: https://alertmanager.prod.internal.example.com/#/alerts?filter=%7Balertname%3D%22PaymentLatencyErrorBudgetBurn%22%7D
slo: slos/payment-latency-slo
runbook: runbooks/checkout-degraded
notify: "#checkout-oncall"
condition_summary: >
  Single-window burn-rate condition: 6h window, 6x budget consumption. See
  `resource` for the actual Alertmanager rule -- this is a prose summary for
  humans, not the source of truth.
owner: checkout-team
created: 2026-07-15
reviewed: 2026-07-15
review_interval: 90d
tags: [alerting, revenue-critical]
---

# Payment latency error budget burn

Backs [payment service latency SLO](../slos/payment-latency-slo.md). Severity is `warning`, not
`critical` — slow payments hurt conversion but don't necessarily mean checkout is down. If this
fires, go to [checkout degraded runbook](../runbooks/checkout-degraded.md).
