output "filename" {
  value       = local.filename
  description = "Path to the concept file: <bundle_root>/<type_dir>/<id>.md."
}

output "concept_id" {
  value       = local.concept_id
  description = <<-EOT
    Bundle-root-relative concept ID, no ".md" — this project's convention for frontmatter
    typed-relationship fields (VOCABULARY.md §3), matching okf_validator's
    concept_id_for() exactly.
  EOT
}

output "relative_path" {
  value       = local.relative_path
  description = <<-EOT
    Markdown-link-ready relative path, assuming the link is written from a concept file
    in a *different* top-level bundle directory — the common case, since every concept
    type lives one level under bundle_root. For a same-directory link, drop the
    "../<type_dir>/" prefix and use "<id>.md" directly instead.
  EOT
}

output "md_link" {
  value       = local.md_link
  description = "Ready-to-paste Markdown link (title as link text) for cross-linking this concept from another module's freetext."
}
