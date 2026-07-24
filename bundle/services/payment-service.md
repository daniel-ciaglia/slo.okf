---
type: Service
title: Payment Service
description: Charges the customer's payment method and returns success/failure to checkout-api.
resource: git@example.com:acme/payment-service.git
owner: payments-team
created: 2026-07-15
reviewed: 2026-07-15
review_interval: 90d
journeys:
  - journeys/checkout
tags: [checkout, payments]
---

# Payment Service

Sits between [cart-service](cart-service.md) and [checkout-api](checkout-api.md) in the
[checkout journey](../journeys/checkout.md). Its latency directly backs the
[payment latency SLO](../slos/payment-latency-slo.md) — this is the service to look at first
when that SLO is breaching.
