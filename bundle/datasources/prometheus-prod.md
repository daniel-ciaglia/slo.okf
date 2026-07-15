---
type: DataSource
title: Prometheus (prod)
description: Primary Prometheus instance scraping the checkout stack.
resource: https://prometheus.prod.internal.example.com
owner: observability-team
created: 2026-07-15
tags: [prometheus]
---

# Prometheus (prod)

Backs every [metric](../metrics/) referenced by the [checkout journey](../journeys/checkout.md)'s
SLIs.
