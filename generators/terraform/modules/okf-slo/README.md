# okf-slo

A Terraform module that writes/updates one OKF `SLO` concept file. Same contract and shared
internal engine as `../okf-subsystem/` — see `../okf-subsystem/README.md` for the full
write-up, not repeated here.

## The one rule that's different here: literal values only

VOCABULARY.md §4 singles out "the rationale/target content of every SLO" as something a
generator must never invent, in the same sentence as `CustomerJourney`/`Runbook` prose. That
doesn't rule out this module — `var.description`/`var.target`/`var.time_window` being Terraform
inputs is no different from `okf-subsystem`'s `var.title`/`var.resource`: a human is still the
one deciding the content, just typing it into an HCL module call instead of directly into
Markdown.

**What it does rule out**: deriving these values from another resource's attribute — e.g.
`target = "${datadog_service_level_objective.checkout.target_threshold}%"`. That would cross
from "a human typed a number" into "a generator invented an SLO target from infrastructure
state," exactly what §4 forbids. If you can't point to the specific human who decided this
target and why, this module is the wrong tool — hand-author the concept instead.

`var.description`'s own field description repeats this rule so it's visible from `terraform
plan`/docs generation, not just this README.

## `owner`/`reviewed`/`review_interval`

`models.py`'s `SLO` validator now relaxes these to optional once `generated_by` is present
(this prototype's other modules already had this; `SLO`/`Alert` didn't until this module was
built — see the models.py fix noted in `../../README.md`). But consider setting them anyway
for SLOs specifically: the reason VOCABULARY.md §2 relaxes staleness review for generated
concepts is "a structurally-derived fact doesn't need a human review cadence" — and per the
rule above, an SLO's content here is never a structurally-derived fact, it's the same human
judgment a hand-authored SLO would carry. The fields are optional so the module doesn't force
an error, not because skipping them is recommended.

## Example

See `../../examples/checkout-availability-slo/` — reproduces
`bundle/slos/checkout-availability-slo.md`, minus `valid_from` (no module in this prototype
supports `valid_from`/`valid_until`/`supersedes` yet — out of scope, consistent across types).
