module "address" {
  source      = "../internal/concept-address"
  bundle_root = var.bundle_root
  type_dir    = "slis"
  id          = var.id
  title       = var.title
}

locals {
  module_version = "0.1.0"
  generated_by   = "terraform-okf-sli@${local.module_version}"

  filename = module.address.filename

  has_ratio_good     = var.ratio_metric_good != ""
  has_ratio_total    = var.ratio_metric_total != ""
  has_ratio          = local.has_ratio_good && local.has_ratio_total
  ratio_pair_matched = local.has_ratio_good == local.has_ratio_total
  has_threshold      = var.threshold_metric != ""

  # Exactly one indicator kind — VOCABULARY.md §6 SLI. Enforced via lifecycle.precondition
  # rather than a variable validation block: cross-variable references in `validation`
  # blocks need Terraform >= 1.9, this module targets >= 1.3.
  exactly_one_indicator = local.has_ratio != local.has_threshold

  ratio_metric_block    = local.has_ratio ? "ratio_metric:\n  good: ${var.ratio_metric_good}\n  total: ${var.ratio_metric_total}" : ""
  threshold_metric_line = local.has_threshold ? "threshold_metric: ${var.threshold_metric}" : ""
  resource_line         = var.resource != "" ? "resource: ${var.resource}" : ""
  data_source_line      = var.data_source != "" ? "data_source: ${var.data_source}" : ""
  owner_line            = var.owner != "" ? "owner: ${var.owner}" : ""
  tags_line             = length(var.tags) > 0 ? "tags: [${join(", ", var.tags)}]" : ""

  render_vars = {
    title                 = var.title
    description           = var.description
    generated_by          = local.generated_by
    ratio_metric_block    = local.ratio_metric_block
    threshold_metric_line = local.threshold_metric_line
    resource_line         = local.resource_line
    data_source_line      = local.data_source_line
    owner_line            = local.owner_line
    tags_line             = local.tags_line
    freetext              = trimspace(var.freetext)
    human_notes           = module.freetext.resolved_freetext
  }

  stable_content = templatefile("${path.module}/templates/sli.md.tftpl", merge(
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

resource "local_file" "sli" {
  filename = local.filename
  content = templatefile("${path.module}/templates/sli.md.tftpl", merge(
    local.render_vars,
    {
      created   = module.timestamps.created
      timestamp = module.timestamps.timestamp
    },
  ))

  lifecycle {
    precondition {
      condition     = local.ratio_pair_matched
      error_message = "ratio_metric_good and ratio_metric_total must be set together or not at all."
    }
    precondition {
      condition     = local.exactly_one_indicator
      error_message = "SLI must set exactly one of {ratio_metric_good, ratio_metric_total} or threshold_metric (VOCABULARY.md §6 SLI)."
    }
    precondition {
      condition     = module.freetext.markers_intact
      error_message = "${local.filename} exists but its OKF:FREETEXT markers are missing or malformed — a human edit may have removed them, or the file predates this module. Refusing to overwrite the body: restore the markers around the intended notes, or delete the file to let Terraform recreate it (var.freetext renders fresh either way; the human notes block resets to empty)."
    }
  }
}
