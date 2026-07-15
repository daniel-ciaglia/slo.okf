---
type: CustomerJourney
title: Checkout
description: >
  A customer adds items to their cart, submits payment, and receives order
  confirmation. This is the revenue-critical path: any sustained failure
  here stops the business from taking money.
owner: checkout-team
created: 2026-07-15
reviewed: 2026-07-15
review_interval: 90d
tags: [checkout, revenue-critical]
slos:
  - slos/checkout-availability-slo
  - slos/payment-latency-slo
subsystems:
  - subsystems/cart-service
  - subsystems/payment-service
  - subsystems/checkout-api
---

# Checkout

The path: cart → payment → confirmation. Three [subsystems](../subsystems/) carry it —
[cart-service](../subsystems/cart-service.md), [payment-service](../subsystems/payment-service.md), and
[checkout-api](../subsystems/checkout-api.md) — and its health is tracked by two SLOs:

- [Checkout API availability](../slos/checkout-availability-slo.md) — is the checkout API up and answering successfully?
- [Payment latency](../slos/payment-latency-slo.md) — is payment fast enough that customers don't abandon their cart?

## Why this journey matters

This is the only journey in the pilot bundle — the kill criterion is
"if sync overhead exceeds retrieval value, stop"), chosen because it's the shortest path from
"a customer is trying to give us money" to "we failed to take it." Any oncall engineer following
[index.md](../index.md) into this journey should end up at the right
[runbook](../runbooks/checkout-degraded.md) within a couple of hops.

## If this journey is breaching

Follow either SLO above to its linked alert —
[checkout error budget burn](../alerts/checkout-error-budget-burn.md) or
[payment latency error budget burn](../alerts/payment-latency-error-budget-burn.md) — both of
which point to the same [runbook](../runbooks/checkout-degraded.md).
