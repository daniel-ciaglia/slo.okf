module "address" {
  source      = "../internal/concept-address"
  bundle_root = var.bundle_root
  type_dir    = "metrics"
  id          = var.id
  title       = var.title
}

locals {
  module_version = "0.1.0"
  generated_by   = "terraform-okf-metric@${local.module_version}"

  filename = module.address.filename

  description_line = var.description != "" ? "description: ${var.description}" : ""
  owner_line       = var.owner != "" ? "owner: ${var.owner}" : ""
  tags_line        = length(var.tags) > 0 ? "tags: [${join(", ", var.tags)}]" : ""
  data_source_line = var.data_source != "" ? "data_source: ${var.data_source}" : ""

  # PromQL expressions routinely contain YAML-significant characters (quotes, braces,
  # colons) — single-quote the YAML scalar and escape embedded single quotes the YAML way.
  resource_quoted = "'${replace(var.resource, "'", "''")}'"

  render_vars = {
    title            = var.title
    resource_quoted  = local.resource_quoted
    generated_by     = local.generated_by
    description_line = local.description_line
    owner_line       = local.owner_line
    tags_line        = local.tags_line
    data_source_line = local.data_source_line
    freetext         = trimspace(var.freetext)
    human_notes      = module.freetext.resolved_freetext
  }

  stable_content = templatefile("${path.module}/templates/metric.md.tftpl", merge(
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

resource "local_file" "metric" {
  filename = local.filename
  content = templatefile("${path.module}/templates/metric.md.tftpl", merge(
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
