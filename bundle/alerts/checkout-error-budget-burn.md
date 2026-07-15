---
type: Alert
title: Checkout error budget burn
description: >
  Fires when the checkout availability SLO's error budget is burning fast
  enough to exhaust it well before the 30-day window ends.
severity: critical
resource: https://alertmanager.prod.internal.example.com/#/alerts?filter=%7Balertname%3D%22CheckoutErrorBudgetBurn%22%7D
slo: slos/checkout-availability-slo
runbook: runbooks/checkout-degraded
notify: "#checkout-oncall"
condition_summary: >
  Multi-window burn-rate condition: fast burn (1h window, 14.4x budget
  consumption) OR slow burn (6h window, 6x budget consumption). See
  `resource` for the actual Alertmanager rule -- this is a prose summary
  for humans, not the source of truth.
owner: checkout-team
created: 2026-07-15
reviewed: 2026-07-15
review_interval: 90d
tags: [alerting, revenue-critical]
---

# Checkout error budget burn

Backs [checkout API availability SLO](../slos/checkout-availability-slo.md). If this fires, go to
[checkout degraded runbook](../runbooks/checkout-degraded.md).
