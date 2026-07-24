output "id" {
  value       = var.id
  description = "Concept ID (bare filename slug). Prefer concept_id below for frontmatter reference fields — it's already prefixed."
}

output "concept_id" {
  value       = module.address.concept_id
  description = <<-EOT
    Bundle-root-relative concept ID, no ".md" — this project's convention for frontmatter
    typed-relationship fields (VOCABULARY.md §3), matching okf_validator's
    concept_id_for() exactly. Paste directly into e.g. Runbook.alerts on another
    concept (hand-authored, but the ID string is still this format):
    alerts = [module.checkout_error_budget_burn.concept_id].
    Not an OKF spec requirement — OKF itself has no typed-relationship vocabulary, this ID
    format is this project's own.
  EOT
}

output "filename" {
  value       = local.filename
  description = "Path to the written concept file."
}

output "relative_path" {
  value       = module.address.relative_path
  description = <<-EOT
    Markdown-link-ready relative path, assuming the link is written from a concept file
    in a *different* top-level bundle directory — the common case, since every concept
    type lives one level under bundle_root. For a same-directory link, drop the
    "../alerts/" prefix and use "$${var.id}.md" directly instead.
  EOT
}

output "md_link" {
  value       = module.address.md_link
  description = <<-EOT
    Ready-to-paste Markdown link (title as link text) for cross-linking this concept
    from another module's freetext, e.g.
    freetext = "Backs $${module.checkout_availability_slo.md_link}. If this fires, go to
    the checkout degraded runbook (hand-authored — Runbook has no module, see ../../README.md)."
  EOT
}
