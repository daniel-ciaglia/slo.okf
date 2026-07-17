variable "bundle_root" {
  type        = string
  description = "Path to the OKF bundle root (the directory containing subsystems/, slos/, etc)."

  validation {
    condition     = length(trimspace(var.bundle_root)) > 0
    error_message = "bundle_root must not be empty."
  }
}

variable "id" {
  type        = string
  description = "Concept ID / filename slug. Written to <bundle_root>/slos/<id>.md."

  validation {
    condition     = can(regex("^[a-z0-9]+(-[a-z0-9]+)*$", var.id))
    error_message = "id must be a lowercase, hyphen-separated slug — VOCABULARY.md's determinism rule for generated concept IDs."
  }
}

variable "title" {
  type        = string
  description = "VOCABULARY.md §6 SLO: required."

  validation {
    condition     = length(trimspace(var.title)) > 0
    error_message = "title must not be empty."
  }
}

variable "description" {
  type        = string
  description = <<-EOT
    VOCABULARY.md §6 SLO: required. The rationale for this target — WHY this number and
    not another. VOCABULARY.md §4 singles this out (alongside CustomerJourney/Runbook
    prose) as content a generator must never invent. Passing it through this module is
    fine only in the sense that Subsystem's title/resource are: it must be a literal
    value a human typed into the module call, never `= some_datadog_resource.attribute`
    or otherwise derived from another resource. If you can't point to the human who
    decided this number, don't use this module for this SLO — hand-author it instead.
  EOT

  validation {
    condition     = length(trimspace(var.description)) > 0
    error_message = "description must not be empty."
  }
}

variable "sli" {
  type        = string
  description = "VOCABULARY.md §3 SLO.sli, exactly 1, required — link to an SLI concept ID."

  validation {
    condition     = length(trimspace(var.sli)) > 0
    error_message = "sli must not be empty."
  }
}

variable "target" {
  type        = string
  description = "VOCABULARY.md §6 SLO: required, e.g. \"99.9%\". Same literal-value-only rule as description — see its comment."

  validation {
    condition     = length(trimspace(var.target)) > 0
    error_message = "target must not be empty."
  }
}

variable "time_window" {
  type        = string
  description = "VOCABULARY.md §6 SLO: required, e.g. \"30d rolling\"."

  validation {
    condition     = length(trimspace(var.time_window)) > 0
    error_message = "time_window must not be empty."
  }
}

variable "journey" {
  type        = string
  description = "VOCABULARY.md §3 SLO.journey, 0 or 1, informational back-ref to a CustomerJourney concept ID. The matching CustomerJourney.slos entry still has to be hand-authored (rule 9 back-ref symmetry) — CustomerJourney is permanently hand-authored (VOCABULARY.md §4), no module ever writes it."
  default     = ""
}

variable "resource" {
  type        = string
  description = "VOCABULARY.md §6 SLO: optional. Link to an executable OpenSLO/Sloth spec, if the target is ever formalized there."
  default     = ""
}

variable "owner" {
  type        = string
  description = "VOCABULARY.md §2. Optional per models.py once generated_by is set, but consider still setting owner/reviewed/review_interval for SLO specifically: unlike Subsystem/DataSource, an SLO's content is judgment (see description's comment), not a structurally-derived fact — the rationale for relaxing staleness review doesn't really apply here even though the field is technically optional."
  default     = ""
}

variable "reviewed" {
  type        = string
  description = "VOCABULARY.md §2, YYYY-MM-DD. See owner's comment on why you probably still want to set this for SLO."
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
