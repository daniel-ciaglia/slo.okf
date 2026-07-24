# Internal module, not meant to be called directly by end users — shared by every
# okf-<type> module for VOCABULARY.md's `created`/`timestamp` fields.

# Set once on first apply, never changes again — VOCABULARY.md's `created`.
resource "time_static" "created" {}

# Re-stamps only when var.content_hash changes — VOCABULARY.md/README.md's
# "timestamp only advances when the generated frontmatter actually changes" rule,
# implemented without an external diff/check step.
resource "time_static" "updated" {
  triggers = {
    content_hash = var.content_hash
  }
}
