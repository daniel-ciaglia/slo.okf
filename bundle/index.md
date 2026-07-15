# slo.okf — checkout journey pilot bundle

A worked example of the [SRE OKF vocabulary](../VOCABULARY.md) applied to one critical customer journey: checkout. This is a pilot, not a finished product catalog — see [PLAN.md](../PLAN.md) for the kill criterion.

This directory (`bundle/`) is the actual OKF bundle — every non-reserved `.md` file below is a
concept with `type` frontmatter. `VOCABULARY.md`, `PLAN.md`, `README.md`, and `validator/` are
project-level docs and tooling that sit *outside* the bundle on purpose, so that "every `.md` here
is a concept" stays literally true and the validator only ever walks real concept files.

* [Checkout journey](journeys/checkout.md) - the customer path this bundle documents end-to-end, cart through confirmation
* [VOCABULARY.md](../VOCABULARY.md) - the controlled vocabulary this bundle conforms to: types, frontmatter fields, typed relationships, cardinality rules
* [PLAN.md](../PLAN.md) - how this bundle was scoped and why, including what's deliberately out of scope this pass
* [validator/](../validator/) - the Python CLI that checks this bundle against VOCABULARY.md (`python -m okf_validator validate bundle/ --strict`) and renders it as an HTML graph (`python -m okf_validator visualize bundle/`)
* [generators/](../generators/) - Terraform and ArgoCD generator mapping sketches (design only, not implemented)
* [log.md](log.md) - chronological history of this bundle

## Concepts by type

* [Subsystems](subsystems/) - cart, payment, and checkout-API services involved in the journey
* [Data sources](datasources/) - the Prometheus instance backing every metric below
* [Metrics](metrics/) - the raw counters/histograms the SLIs are built from
* [SLIs](slis/) - indicator definitions
* [SLOs](slos/) - targets and rationale
* [Alerts](alerts/) - what fires, how bad, where to go
* [Runbooks](runbooks/) - oncall response steps
