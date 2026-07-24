# Prototype: demonstrates Service.parent/children (VOCABULARY.md §3, added in v0.2.0),
# which no real bundle/services/*.md file uses yet -- synthetic, same honesty framing the
# retired ../checkout-service/ example used before the real bundle/services/ existed (see
# bundle/log.md's v0.2.0 migration entry; that example's original purpose is now served for
# non-synthetic content by ../checkout-services/).
#
# "platform" is a company-wide shared-infra Service with no parent of its own;
# "checkout-platform" is the checkout org's slice of it, nested underneath. Demonstrates the
# same bidirectional-no-cycle property as md_link (../okf-subsystem/README.md) applies to
# concept_id too, since parent/children are also pure functions of var.id/var.title -- neither
# module's children/parent value depends on the other module's resources being created first.
#
# Writes into ./output/ (gitignored), NOT into the real bundle/.

module "checkout_platform" {
  source = "../../modules/okf-service"

  bundle_root = "${path.module}/output"
  id          = "checkout-platform"

  title       = "Checkout Platform"
  description = "The checkout org's slice of the shared platform."
  owner       = "checkout-team"
  tags        = ["checkout"]
  parent      = module.platform.concept_id

  freetext = "Nested under ${replace(module.platform.md_link, "../services/", "")}."
}

module "platform" {
  source = "../../modules/okf-service"

  bundle_root = "${path.module}/output"
  id          = "platform"

  title       = "Platform"
  description = "Company-wide shared infrastructure, org-agnostic."
  owner       = "platform-team"
  tags        = ["platform"]
  children    = [module.checkout_platform.concept_id]

  freetext = "Nests several org-level services, including ${replace(module.checkout_platform.md_link, "../services/", "")}."
}

output "service_id" {
  value = module.checkout_platform.id
}

output "service_filename" {
  value = module.checkout_platform.filename
}

output "platform_md_link" {
  value = module.platform.md_link
}
