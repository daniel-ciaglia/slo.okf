variable "bundle_root" {
  type        = string
  description = "Path to the OKF bundle root (the directory containing subsystems/, journeys/, etc)."
}

variable "type_dir" {
  type        = string
  description = "Bundle-root-relative directory this concept type is written under, e.g. \"subsystems\" or \"slis\"."

  validation {
    condition     = can(regex("^[a-z]+$", var.type_dir))
    error_message = "type_dir must be a lowercase directory name (e.g. \"subsystems\")."
  }
}

variable "id" {
  type        = string
  description = "Concept ID / filename slug."
}

variable "title" {
  type        = string
  description = "Human-readable title, used as the link text in md_link."
}
