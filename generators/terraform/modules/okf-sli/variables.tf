variable "bundle_root" {
  type        = string
  description = "Path to the OKF bundle root (the directory containing subsystems/, slis/, etc)."

  validation {
    condition     = length(trimspace(var.bundle_root)) > 0
    error_message = "bundle_root must not be empty."
  }
}

variable "id" {
  type        = string
  description = "Concept ID / filename slug. Written to <bundle_root>/slis/<id>.md."

  validation {
    condition     = can(regex("^[a-z0-9]+(-[a-z0-9]+)*$", var.id))
    error_message = "id must be a lowercase, hyphen-separated slug — VOCABULARY.md's determinism rule for generated concept IDs."
  }
}

variable "title" {
  type        = string
  description = "VOCABULARY.md §6 SLI: required."

  validation {
    condition     = length(trimspace(var.title)) > 0
    error_message = "title must not be empty."
  }
}

variable "description" {
  type        = string
  description = "VOCABULARY.md §6 SLI: required. What \"good\" and \"total\" mean."

  validation {
    condition     = length(trimspace(var.description)) > 0
    error_message = "description must not be empty."
  }
}

variable "ratio_metric_good" {
  type        = string
  description = "VOCABULARY.md §3 SLI.ratio_metric.good — link to a Metric concept ID. Set together with ratio_metric_total, and only if threshold_metric is not set (exactly one indicator kind is required — enforced at apply time, since cross-variable validation blocks need Terraform >= 1.9 and this module targets >= 1.3)."
  default     = ""
}

variable "ratio_metric_total" {
  type        = string
  description = "VOCABULARY.md §3 SLI.ratio_metric.total — link to a Metric concept ID. Set together with ratio_metric_good."
  default     = ""
}

variable "threshold_metric" {
  type        = string
  description = "VOCABULARY.md §3 SLI.threshold_metric — link to a Metric concept ID. Set instead of ratio_metric_good/ratio_metric_total, not alongside them."
  default     = ""
}

variable "resource" {
  type        = string
  description = "VOCABULARY.md §6 SLI: optional. Link to a formal SLI spec, if one is ever authored elsewhere."
  default     = ""
}

variable "data_source" {
  type        = string
  description = "VOCABULARY.md §3: SLI.data_source, 0 or 1, link to a DataSource concept ID."
  default     = ""
}

variable "owner" {
  type        = string
  description = "VOCABULARY.md §2: optional. SLI carries no owner/reviewed/review_interval requirement in models.py regardless of generated_by."
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
