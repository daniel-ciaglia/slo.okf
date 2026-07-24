---
type: Service
title: Cart Service
description: Stores and mutates the customer's shopping cart before checkout begins.
resource: git@example.com:acme/cart-service.git
owner: checkout-team
created: 2026-07-15
reviewed: 2026-07-15
review_interval: 90d
journeys:
  - journeys/checkout
subsystems:
  - subsystems/cart-service-redis
tags: [checkout]
---

# Cart Service

Owns cart state until checkout hands off to [payment-service](payment-service.md). Part of the
[checkout journey](../journeys/checkout.md).

No `generated_by` field — this is hand-authored today. Once the Terraform generator sketched in
[../../generators/terraform/README.md](../../generators/terraform/README.md) exists, this concept
is a candidate to become generator-owned.
