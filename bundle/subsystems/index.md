# Subsystem

* [Cart Service](cart-service.md) - Stores and mutates the customer's shopping cart before checkout begins.
* [Checkout API](checkout-api.md) - Public-facing API that orchestrates cart-service and payment-service to complete an order.
* [Payment Service](payment-service.md) - Charges the customer's payment method and returns success/failure to checkout-api.
