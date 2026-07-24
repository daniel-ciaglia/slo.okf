# okf-alert

A Terraform module that writes/updates one OKF `Alert` concept file. Same contract and shared
internal engine as `../okf-subsystem/` — see `../okf-subsystem/README.md` for the full
write-up, not repeated here.

Structural differences:

- `severity` is validated at plan time against VOCABULARY.md §6's enum (`critical` \|
  `warning` \| `info`) via a `variable` `validation` block.
- `notify` is always YAML-quoted, since values commonly look like `#checkout-oncall` — an
  unquoted leading `#` after a YAML `key: ` is a comment marker, not literal text.
- `description`/`condition_summary` use literal block scalars (`|-`), same round-trip-fidelity
  reasoning as `okf-slo`'s description (see that module's README) — whatever newlines are in
  the Terraform string are preserved exactly, rather than reflowed the way a YAML folded
  scalar (`>`, which the hand-authored bundle files use for the same fields) would on
  re-parse.
- `runbook` is a reference to an existing `Runbook` concept ID, not something this module ever
  creates — `Runbook` stays permanently hand-authored (VOCABULARY.md §4), same reasoning that
  ruled out an `okf-runbook`/`okf-customerjourney` module entirely (see `../../README.md`).
- Same `owner`/`reviewed`/`review_interval` note as `okf-slo`: technically optional once
  `generated_by` is set, but an alert's severity/meaning is human judgment, not a
  structurally-derived fact — consider setting them anyway.

## Example

See `../../examples/checkout-error-budget-burn/` — reproduces
`bundle/alerts/checkout-error-budget-burn.md`.
