variable "filename" {
  type        = string
  description = "Path to the concept file that may or may not exist yet."
}

variable "seed" {
  type        = string
  description = "Freetext to use when the file doesn't exist yet (first creation)."
  default     = ""
}
