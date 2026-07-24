# Subdirectories

* [alerts](alerts/index.md)
* [datasources](datasources/index.md) - Primary Prometheus instance scraping the checkout stack.
* [journeys](journeys/index.md) - A customer adds items to their cart, submits payment, and receives order confirmation. This is the revenue-critical path: any sustained failure here stops the business from taking money.
* [metrics](metrics/index.md)
* [runbooks](runbooks/index.md) - Oncall steps for responding to a checkout availability or payment latency error-budget-burn alert.
* [services](services/index.md)
* [slis](slis/index.md)
* [slos](slos/index.md)
* [subsystems](subsystems/index.md) - Session/cart-state cache backing cart-service.
