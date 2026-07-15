---
type: SLI
title: Payment service latency (p95 under threshold)
description: Proportion of the time p95 payment request latency stays under 800ms.
threshold_metric: metrics/payment-latency-p95
data_source: datasources/prometheus-prod
owner: checkout-team
created: 2026-07-15
tags: [latency]
---

# Payment service latency (p95 under threshold)

A threshold indicator, not a ratio — see [payment latency p95](../metrics/payment-latency-p95.md).
Feeds the [payment latency SLO](../slos/payment-latency-slo.md).
