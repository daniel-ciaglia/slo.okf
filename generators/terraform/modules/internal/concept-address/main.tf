# Internal module, not meant to be called directly by end users — shared by every
# okf-<type> module so the "every concept type lives one level under bundle_root"
# directory-layout convention (MAPPING.md) is expressed in exactly one place instead
# of being restated (and kept in sync) across all seven okf-<type> modules.

locals {
  concept_id = "${var.type_dir}/${var.id}"
  filename   = "${var.bundle_root}/${local.concept_id}.md"

  # Assumes the link is written from a concept file in a *different* top-level bundle
  # directory — the common case, since every concept type lives one level under
  # bundle_root. For a same-directory link, the caller should drop the
  # "../<type_dir>/" prefix and use "<id>.md" directly instead.
  relative_path = "../${local.concept_id}.md"
  md_link       = "[${var.title}](${local.relative_path})"
}
