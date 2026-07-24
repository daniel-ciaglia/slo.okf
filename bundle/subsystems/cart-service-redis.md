---
type: Subsystem
title: Cart Service Redis
description: Session/cart-state cache backing cart-service.
resource: module.cart_service.aws_elasticache_replication_group.session_cache
services:
  - services/cart-service
owner: checkout-team
created: 2026-07-15
reviewed: 2026-07-15
review_interval: 90d
tags: [checkout, redis]
---

# Cart Service Redis

Backs [Cart Service](../services/cart-service.md) — holds in-progress cart state so a page
reload mid-checkout doesn't lose the customer's cart.

Added when `bundle/` migrated to VOCABULARY.md v0.2.0's `Service`/`Subsystem` split (see
`log.md`), so this pilot bundle keeps demonstrating all 9 vocabulary types — `cart-service`,
`payment-service`, and `checkout-api` became `Service` concepts in that migration, which would
otherwise have left `Subsystem` with no worked example at all.

No `generated_by` field — hand-authored today. Once the Terraform generator sketched in
[../../generators/terraform/README.md](../../generators/terraform/README.md) exists, this
concept is a candidate to become generator-owned.
