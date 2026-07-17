variable "bundle_root" {
  type        = string
  description = "Path to the OKF bundle root (the directory containing subsystems/, metrics/, etc)."

  validation {
    condition     = length(trimspace(var.bundle_root)) > 0
    error_message = "bundle_root must not be empty."
  }
}

variable "id" {
  type        = string
  description = "Concept ID / filename slug. Written to <bundle_root>/metrics/<id>.md."

  validation {
    condition     = can(regex("^[a-z0-9]+(-[a-z0-9]+)*$", var.id))
    error_message = "id must be a lowercase, hyphen-separated slug — VOCABULARY.md's determinism rule for generated concept IDs."
  }
}

variable "title" {
  type        = string
  description = "VOCABULARY.md §6 Metric: required. Human-readable name."

  validation {
    condition     = length(trimspace(var.title)) > 0
    error_message = "title must not be empty."
  }
}

variable "resource" {
  type        = string
  description = "VOCABULARY.md §6 Metric: required. A PromQL expression or Grafana panel URL — often contains characters (quotes, braces, colons) that need YAML single-quoting, which this module handles."

  validation {
    condition     = length(trimspace(var.resource)) > 0
    error_message = "resource must not be empty."
  }
}

variable "description" {
  type        = string
  description = "VOCABULARY.md §6 Metric: optional. One-line description."
  default     = ""
}

variable "owner" {
  type        = string
  description = "VOCABULARY.md §2: optional. Metric carries no owner/reviewed/review_interval requirement in models.py regardless of generated_by."
  default     = ""
}

variable "tags" {
  type        = list(string)
  description = "VOCABULARY.md §2 tags."
  default     = []
}

variable "data_source" {
  type        = string
  description = "VOCABULARY.md §3: Metric.data_source, 0 or 1, link to a DataSource concept ID (e.g. \"datasources/prometheus-prod\")."
  default     = ""
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
