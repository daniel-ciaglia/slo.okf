# SLO

* [Checkout API availability SLO](checkout-availability-slo.md) - The checkout API must succeed at least 99.9% of the time over a rolling 30-day window. This is the primary revenue-protection SLO for the checkout journey; breaching it means customers cannot complete purchases.
* [Payment service latency SLO](payment-latency-slo.md) - 95th percentile payment request latency must stay under 800ms for at least 99.5% of each rolling 30-day window. A breach means checkout feels slow enough that customers abandon carts even when requests eventually succeed.
