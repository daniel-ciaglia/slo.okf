variable "content_hash" {
  type        = string
  description = "Hash of the rendered content that should be considered for staleness, excluding the timestamp fields themselves (they'd otherwise chase their own tail)."
}
