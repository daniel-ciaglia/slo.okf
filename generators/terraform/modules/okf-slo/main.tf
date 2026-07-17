module "address" {
  source      = "../internal/concept-address"
  bundle_root = var.bundle_root
  type_dir    = "slos"
  id          = var.id
  title       = var.title
}

locals {
  module_version = "0.1.0"
  generated_by   = "terraform-okf-slo@${local.module_version}"

  filename = module.address.filename

  # SLO descriptions are rationale prose, routinely multi-line — render as a YAML block
  # literal scalar so line breaks survive, rather than the inline plain scalar the other
  # okf-<type> modules use for their (typically one-line) description fields.
  description_block = join(
    "\n", concat(["description: |-"], [for line in split("\n", trimspace(var.description)) : "  ${line}"])
  )

  journey_line         = var.journey != "" ? "journey: ${var.journey}" : ""
  resource_line        = var.resource != "" ? "resource: ${var.resource}" : ""
  owner_line           = var.owner != "" ? "owner: ${var.owner}" : ""
  reviewed_line        = var.reviewed != "" ? "reviewed: ${var.reviewed}" : ""
  review_interval_line = var.review_interval != "" ? "review_interval: ${var.review_interval}" : ""
  tags_line            = length(var.tags) > 0 ? "tags: [${join(", ", var.tags)}]" : ""

  render_vars = {
    title                = var.title
    description_block    = local.description_block
    sli                  = var.sli
    target               = var.target
    time_window          = var.time_window
    journey_line         = local.journey_line
    resource_line        = local.resource_line
    generated_by         = local.generated_by
    owner_line           = local.owner_line
    reviewed_line        = local.reviewed_line
    review_interval_line = local.review_interval_line
    tags_line            = local.tags_line
    freetext             = trimspace(var.freetext)
    human_notes          = module.freetext.resolved_freetext
  }

  stable_content = templatefile("${path.module}/templates/slo.md.tftpl", merge(
    local.render_vars, { created = "", timestamp = "" }
  ))
}

module "freetext" {
  source   = "../internal/freetext-marker"
  filename = local.filename
  # No seed: var.freetext renders directly in the body every apply (see render_vars.freetext
  # below), it doesn't seed the preserved block. This block is exclusively for human-added
  # notes, which start empty and are preserved verbatim once a human writes into them.
}

module "timestamps" {
  source       = "../internal/timestamps"
  content_hash = sha256(local.stable_content)
}

resource "local_file" "slo" {
  filename = local.filename
  content = templatefile("${path.module}/templates/slo.md.tftpl", merge(
    local.render_vars,
    {
      created   = module.timestamps.created
      timestamp = module.timestamps.timestamp
    },
  ))

  lifecycle {
    precondition {
      condition     = module.freetext.markers_intact
      error_message = "${local.filename} exists but its OKF:FREETEXT markers are missing or malformed — a human edit may have removed them, or the file predates this module. Refusing to overwrite the body: restore the markers around the intended notes, or delete the file to let Terraform recreate it (var.freetext renders fresh either way; the human notes block resets to empty)."
    }
  }
}
