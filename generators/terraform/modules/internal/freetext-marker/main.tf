# Internal module, not meant to be called directly by end users — shared by every
# okf-<type> module so the "seed once, preserve a human's in-place edits after that"
# marker contract only has to be implemented once. See ../../okf-subsystem/README.md
# for the user-facing contract this implements.

locals {
  # First apply: file doesn't exist yet, freetext is seeded from var.seed.
  # Later applies: preserve whatever a human left between the markers on disk.
  existing_content = fileexists(var.filename) ? file(var.filename) : null

  extracted_freetext = local.existing_content == null ? null : try(
    trimspace(regex(
      "(?s)<!-- OKF:FREETEXT:BEGIN -->\n(.*)\n<!-- OKF:FREETEXT:END -->",
      local.existing_content,
    )[0]),
    null,
  )

  # true when there's nothing to preserve (first apply) or the markers parsed cleanly.
  # false only means "file exists but markers are missing/corrupted" — a real problem,
  # not this module inventing/discarding content.
  markers_intact = local.existing_content == null || local.extracted_freetext != null

  # trimspace both sides so the seed path and the extract-from-existing-file path
  # normalize identically — otherwise a seed with e.g. a heredoc's trailing newline
  # would hash differently from what gets read back after being written once,
  # causing a permanent one-time "phantom" diff on the apply right after creation.
  #
  # Deliberately not coalesce(): it errors out if *all* arguments are null/"", which
  # a legitimately empty var.seed on first creation would trigger.
  resolved_freetext = local.extracted_freetext != null ? local.extracted_freetext : trimspace(var.seed)
}
