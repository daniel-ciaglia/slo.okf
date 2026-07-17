output "created" {
  value       = formatdate("YYYY-MM-DD", time_static.created.rfc3339)
  description = "VOCABULARY.md `created` — date-only, stamped once."
}

output "timestamp" {
  value       = formatdate("YYYY-MM-DD", time_static.updated.rfc3339)
  description = "OKF-native `timestamp` field. Must be quoted in YAML frontmatter — it's typed str in models.py, and an unquoted YYYY-MM-DD scalar parses as a YAML date, which fails pydantic validation."
}
