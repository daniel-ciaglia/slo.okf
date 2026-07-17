variable "bundle_root" {
  type        = string
  description = "Path to the OKF bundle root (the directory containing subsystems/, journeys/, etc)."

  validation {
    condition     = length(trimspace(var.bundle_root)) > 0
    error_message = "bundle_root must not be empty."
  }
}

variable "id" {
  type        = string
  description = "Concept ID / filename slug. Written to <bundle_root>/subsystems/<id>.md."

  validation {
    condition     = can(regex("^[a-z0-9]+(-[a-z0-9]+)*$", var.id))
    error_message = "id must be a lowercase, hyphen-separated slug (e.g. \"cart-service\") — VOCABULARY.md's determinism rule for generated concept IDs."
  }
}

variable "title" {
  type        = string
  description = "VOCABULARY.md §6 Subsystem: required. Human-readable name."

  validation {
    condition     = length(trimspace(var.title)) > 0
    error_message = "title must not be empty."
  }
}

variable "resource" {
  type        = string
  description = "VOCABULARY.md §6 Subsystem: required. The underlying asset — source repo path, Terraform module address, etc. Not a synthetic URI."

  validation {
    condition     = length(trimspace(var.resource)) > 0
    error_message = "resource must not be empty."
  }
}

variable "description" {
  type        = string
  description = "VOCABULARY.md §6 Subsystem: optional. One-line description."
  default     = ""
}

variable "owner" {
  type        = string
  description = "VOCABULARY.md §2: optional here — generated Subsystems carry generated_by, which relaxes the owner/reviewed/review_interval requirement (§2, models.py Subsystem validator). Still useful to record if known."
  default     = ""
}

variable "tags" {
  type        = list(string)
  description = "VOCABULARY.md §2 tags."
  default     = []
}

variable "service" {
  type        = string
  description = "VOCABULARY.md §3: optional link to a Service concept ID (0 or 1)."
  default     = ""
}

variable "journeys" {
  type        = list(string)
  description = <<-EOT
    VOCABULARY.md §3: informational back-ref to CustomerJourney concept IDs.
    MAPPING.md's rule that a generator never *invents* CustomerJourney links still
    holds here — this is not the module inferring anything, it's the human calling
    the module (who is placing it at the network/database/service definition and
    knows which journey it serves) stating the same fact the corresponding
    CustomerJourney.subsystems entry must also state, to satisfy rule 9's
    symmetry check.
  EOT
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
