variable "bundle_root" {
  type        = string
  description = "Path to the OKF bundle root (the directory containing subsystems/, datasources/, etc)."

  validation {
    condition     = length(trimspace(var.bundle_root)) > 0
    error_message = "bundle_root must not be empty."
  }
}

variable "id" {
  type        = string
  description = "Concept ID / filename slug. Written to <bundle_root>/datasources/<id>.md."

  validation {
    condition     = can(regex("^[a-z0-9]+(-[a-z0-9]+)*$", var.id))
    error_message = "id must be a lowercase, hyphen-separated slug (e.g. \"prometheus-prod\") — VOCABULARY.md's determinism rule for generated concept IDs."
  }
}

variable "title" {
  type        = string
  description = "VOCABULARY.md §6 DataSource: required. Human-readable name."

  validation {
    condition     = length(trimspace(var.title)) > 0
    error_message = "title must not be empty."
  }
}

variable "resource" {
  type        = string
  description = "VOCABULARY.md §6 DataSource: required. Prometheus instance URL or job selector — the real telemetry source, not a synthetic URI."

  validation {
    condition     = length(trimspace(var.resource)) > 0
    error_message = "resource must not be empty."
  }
}

variable "description" {
  type        = string
  description = "VOCABULARY.md §6 DataSource: optional. One-line description."
  default     = ""
}

variable "owner" {
  type        = string
  description = "VOCABULARY.md §2: optional here — generated DataSources carry generated_by, which relaxes the owner/reviewed/review_interval requirement (§2). Still useful to record if known."
  default     = ""
}

variable "tags" {
  type        = list(string)
  description = "VOCABULARY.md §2 tags."
  default     = []
}

variable "freetext" {
  type        = string
  description = <<-EOT
    Generator-owned Markdown prose, rendered directly in the body below the title
    and rewritten every `terraform apply` from this input — same lifecycle as the
    frontmatter, not a one-time seed. It is never written into the OKF:FREETEXT
    markers and never overwrites what's between them. For prose a human should own
    and that survives regeneration, edit directly between the OKF:FREETEXT markers
    in the file on disk instead. See README.md in this module for the marker contract.
  EOT
  default     = ""
}
