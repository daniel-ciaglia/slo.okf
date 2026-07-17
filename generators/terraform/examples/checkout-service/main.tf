# Prototype: no bundle/services/ exists in the real bundle yet (Service is the one type
# VOCABULARY.md's own README notes hasn't been exercised), so this is a synthetic example
# grouping the existing cart-service/payment-service Subsystems under a logical Service.

module "checkout_service" {
  source = "../../modules/okf-service"

  bundle_root = "${path.module}/output"
  id          = "checkout-service"

  title       = "Checkout Service"
  description = "Logical grouping of the SLOs owned by the checkout team."
  owner       = "checkout-team"
  tags        = ["checkout"]
  slos        = ["slos/checkout-availability-slo", "slos/payment-latency-slo"]

  freetext = "Groups the checkout team's SLOs for reporting purposes; individual Subsystems (cart-service, payment-service) link back to the checkout journey directly, not through this Service."
}

output "service_id" {
  value = module.checkout_service.id
}

output "service_filename" {
  value = module.checkout_service.filename
}
