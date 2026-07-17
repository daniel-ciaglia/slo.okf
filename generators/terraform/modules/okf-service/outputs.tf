output "id" {
  value       = var.id
  description = "Concept ID (bare filename slug). Prefer concept_id below for frontmatter reference fields — it's already prefixed."
}

output "concept_id" {
  value       = module.address.concept_id
  description = <<-EOT
    Bundle-root-relative concept ID, no ".md" — this project's convention for frontmatter
    typed-relationship fields (VOCABULARY.md §3), matching okf_validator's
    concept_id_for() exactly. Paste directly into e.g. Subsystem.service on another
    concept: service = module.checkout_service.concept_id.
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
    "../services/" prefix and use "$${var.id}.md" directly instead.
  EOT
}

output "md_link" {
  value       = module.address.md_link
  description = <<-EOT
    Ready-to-paste Markdown link (title as link text) for cross-linking this concept
    from another module's freetext, e.g.
    freetext = "Grouped under $${module.checkout_service.md_link}."
  EOT
}
