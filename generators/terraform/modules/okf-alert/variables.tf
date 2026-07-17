variable "bundle_root" {
  type        = string
  description = "Path to the OKF bundle root (the directory containing subsystems/, alerts/, etc)."

  validation {
    condition     = length(trimspace(var.bundle_root)) > 0
    error_message = "bundle_root must not be empty."
  }
}

variable "id" {
  type        = string
  description = "Concept ID / filename slug. Written to <bundle_root>/alerts/<id>.md."

  validation {
    condition     = can(regex("^[a-z0-9]+(-[a-z0-9]+)*$", var.id))
    error_message = "id must be a lowercase, hyphen-separated slug — VOCABULARY.md's determinism rule for generated concept IDs."
  }
}

variable "title" {
  type        = string
  description = "VOCABULARY.md §6 Alert: required."

  validation {
    condition     = length(trimspace(var.title)) > 0
    error_message = "title must not be empty."
  }
}

variable "description" {
  type        = string
  description = "VOCABULARY.md §6 Alert: required. What this alert means and why it matters."

  validation {
    condition     = length(trimspace(var.description)) > 0
    error_message = "description must not be empty."
  }
}

variable "severity" {
  type        = string
  description = "VOCABULARY.md §6 Alert: required, one of critical | warning | info."

  validation {
    condition     = contains(["critical", "warning", "info"], var.severity)
    error_message = "severity must be one of: critical, warning, info."
  }
}

variable "resource" {
  type        = string
  description = "VOCABULARY.md §6 Alert: required. The real Alertmanager rule this documents — not a synthetic URI."

  validation {
    condition     = length(trimspace(var.resource)) > 0
    error_message = "resource must not be empty."
  }
}

variable "slo" {
  type        = string
  description = "VOCABULARY.md §3 Alert.slo, exactly 1, required — link to an SLO concept ID."

  validation {
    condition     = length(trimspace(var.slo)) > 0
    error_message = "slo must not be empty."
  }
}

variable "runbook" {
  type        = string
  description = "VOCABULARY.md §3 Alert.runbook, exactly 1, required — link to a Runbook concept ID. This module never creates the Runbook itself: Runbook is permanently hand-authored (VOCABULARY.md §4), so the ID must already exist or be created by a human alongside this call."

  validation {
    condition     = length(trimspace(var.runbook)) > 0
    error_message = "runbook must not be empty."
  }
}

variable "notify" {
  type        = string
  description = "VOCABULARY.md §6 Alert: optional. Plain string — team/channel, not a linked concept (e.g. \"#checkout-oncall\"). Always YAML-quoted by this module since values commonly start with '#', which YAML would otherwise read as a comment."
  default     = ""
}

variable "condition_summary" {
  type        = string
  description = "VOCABULARY.md §6 Alert: optional. Prose restatement of the trigger condition, for humans — not authoritative, `resource` is."
  default     = ""
}

variable "owner" {
  type        = string
  description = "VOCABULARY.md §2. Optional per models.py once generated_by is set, but consider still setting owner/reviewed/review_interval: an Alert's severity/meaning is human judgment, not a structurally-derived fact, similar to okf-slo's note on the same fields."
  default     = ""
}

variable "reviewed" {
  type        = string
  description = "VOCABULARY.md §2, YYYY-MM-DD. See owner's comment."
  default     = ""
}

variable "review_interval" {
  type        = string
  description = "VOCABULARY.md §2, e.g. \"90d\". See owner's comment."
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
