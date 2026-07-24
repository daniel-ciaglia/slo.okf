---
type: Service
title: Checkout API
description: Public-facing API that orchestrates cart-service and payment-service to complete an order.
resource: git@example.com:acme/checkout-api.git
owner: checkout-team
created: 2026-07-15
reviewed: 2026-07-15
review_interval: 90d
journeys:
  - journeys/checkout
tags: [checkout]
---

# Checkout API

The front door of the [checkout journey](../journeys/checkout.md) — customer requests land here
first. Its availability directly backs the
[checkout availability SLO](../slos/checkout-availability-slo.md).
