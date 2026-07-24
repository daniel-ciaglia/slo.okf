# Prototype: reproduces bundle/subsystems/cart-service-redis.md as if it were generated at
# the point the cache is actually defined -- see ../../modules/okf-subsystem/README.md.
#
# Added in the v0.2.0 migration pass (see bundle/log.md): cart-service-redis is the one real
# Subsystem in bundle/ post-migration, since cart-service/checkout-api/payment-service all
# became Service concepts (see ../checkout-services/). Demonstrates the now-required
# `service` input, replacing the retired ../cart-service/ example (which called
# okf-subsystem for cart-service/payment-service back when those were Subsystems).
#
# Writes into ./output/ (gitignored), NOT into the real bundle/.

module "cart_service_redis_subsystem" {
  source = "../../modules/okf-subsystem"

  bundle_root = "${path.module}/output"
  id          = "cart-service-redis"

  title       = "Cart Service Redis"
  description = "Session/cart-state cache backing cart-service."
  resource    = "module.cart_service.aws_elasticache_replication_group.session_cache"
  services    = ["services/cart-service"]

  owner = "checkout-team"
  tags  = ["checkout", "redis"]

  freetext = "Holds in-progress cart state so a page reload mid-checkout doesn't lose the customer's cart."
}

output "subsystem_id" {
  value = module.cart_service_redis_subsystem.id
}

output "subsystem_filename" {
  value = module.cart_service_redis_subsystem.filename
}
