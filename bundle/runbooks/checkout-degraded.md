---
type: Runbook
title: Checkout degraded / error budget burn
description: >
  Oncall steps for responding to a checkout availability or payment latency
  error-budget-burn alert.
alerts:
  - alerts/checkout-error-budget-burn
  - alerts/payment-latency-error-budget-burn
owner: checkout-team
created: 2026-07-15
reviewed: 2026-07-15
review_interval: 90d
tags: [oncall, revenue-critical]
---

# Checkout degraded / error budget burn

Triggered by either [checkout error budget burn](../alerts/checkout-error-budget-burn.md) (severity
`critical`) or [payment latency error budget burn](../alerts/payment-latency-error-budget-burn.md)
(severity `warning`).

## 1. Confirm scope

- Check the [checkout API availability SLI](../slis/checkout-availability.md) and
  [payment latency SLI](../slis/payment-latency.md) dashboards for the current burn rate.
- Is this checkout-wide, or isolated to one subsystem? Check
  [checkout-api](../subsystems/checkout-api.md), [payment-service](../subsystems/payment-service.md),
  and [cart-service](../subsystems/cart-service.md) individually.

## 2. If payment-service is the bottleneck

- Payment is often the slowest hop and the one this team least controls. Check payment-service's
  own dashboards for upstream (external payment processor) latency before assuming a regression
  in our own code.
- If the processor itself is degraded, this may not be actionable beyond communicating status —
  don't burn time trying to "fix" a third party.

## 3. If checkout-api or cart-service is the bottleneck

- Check recent deploys to [checkout-api](../subsystems/checkout-api.md) or
  [cart-service](../subsystems/cart-service.md) — a bad rollout is the most common cause of a fast
  burn (1h window, 14.4x).
- Roll back the most recent deploy if the timing correlates.

## 4. Escalate

- Page `#checkout-oncall` if not already engaged (this is the `notify` target on both alerts).
- This journey is revenue-critical (see [checkout journey](../journeys/checkout.md)) — don't sit on
  a `critical`-severity burn waiting for confirmation if the dashboards already show clear signal.

## Known limitations of this runbook

This is a pilot bundle (see [PLAN.md](../../PLAN.md)) — these steps are illustrative, not drawn from a
real incident history. Treat as a starting structure to fill in with real postmortem-derived steps,
not as tested guidance.
