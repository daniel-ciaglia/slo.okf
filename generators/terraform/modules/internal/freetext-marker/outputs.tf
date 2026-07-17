output "resolved_freetext" {
  value       = local.resolved_freetext
  description = "The freetext body to render: extracted from the existing file's markers if present, else var.seed."
}

output "markers_intact" {
  value       = local.markers_intact
  description = "False iff the file already exists but its OKF:FREETEXT markers are missing/malformed. Callers should precondition their write on this."
}
