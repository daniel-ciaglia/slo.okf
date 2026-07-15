# slo.okf

An [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf) (OKF) convention for documenting SRE customer journeys — SLI/SLO/alert/runbook chains — so an oncall human or agent can navigate from "what's breaking" to "what do I do about it" in a few hops. Borrows [OpenSLO](https://github.com/OpenSLO/OpenSLO)'s object model as a naming donor and [KCP](https://github.com/Cantara/knowledge-context-protocol)'s temporal-validity field names, without depending on either.

## What's here

- **[VOCABULARY.md](VOCABULARY.md)** — the controlled vocabulary: 9 concept types, frontmatter fields, typed-relationship conventions, cardinality rules. Read this before adding a concept.
- **[bundle/](bundle/)** — the actual OKF bundle, one worked example (a checkout journey) end to end. Start at [bundle/index.md](bundle/index.md).
- **[validator/](validator/)** — a Python CLI, `okf-validator`, with a `validate` subcommand (checks `bundle/` against `VOCABULARY.md`) and a `visualize` subcommand (renders `bundle/` as a self-contained HTML graph view; see "Visualizing the bundle" below).
- **[generators/](generators/)** — Terraform and ArgoCD generator mapping sketches (design docs, not implemented).

## Where the checkout example's SRE patterns come from

The checkout journey's *content* is fictional — every `resource` field in `bundle/` points at
`example.com`/`acme` placeholders, not a real Prometheus, Alertmanager, or git host. But the SRE
*patterns* it demonstrates aren't invented; they're straight out of Google's SRE book and
workbook:

- Ratio-based availability SLI (`slis/checkout-availability.md`) and threshold-based latency SLI
  (`slis/payment-latency.md`): [SRE Workbook ch. 2, Implementing SLOs](https://sre.google/workbook/implementing-slos/)
- SLO target-setting, and why 99.9% and not higher (`slos/*.md`): [SRE Book ch. 4, Service Level Objectives](https://sre.google/sre-book/service-level-objectives/)
- Error budgets — why a breached SLO matters more than raw downtime: [SRE Book ch. 3, Embracing Risk](https://sre.google/sre-book/embracing-risk/)
- Multiwindow, multi-burn-rate alerting — `bundle/alerts/*.md` use Google's own reference pair
  verbatim (1h window / 14.4x burn rate, 6h window / 6x burn rate): [SRE Workbook ch. 5, Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/)

The Workbook's own worked example is a mobile game, not a checkout flow — the checkout scenario
here is this project's own choice of illustration, applying the same patterns.

## Why the bundle is a subdirectory, not the repo root

OKF's own convention treats a bundle's root `index.md` as the natural entry point, which argues for putting it at the repo root. But this repo also needs project docs (`VOCABULARY.md`, `README.md`) and tooling (`validator/`, `generators/`) that are emphatically *not* concepts — and the validator's core invariant is "every non-reserved `.md` file in the bundle has `type` frontmatter."

## Running the validator

```sh
cd validator
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/okf-validator validate ../bundle --strict
```

Default mode prints issues and exits 0 (OKF's own conformance rules are permissive by design). `--strict` exits 1 on any error-severity issue — this is our producer-side CI discipline, deliberately stricter than what OKF requires of consumers (see `VOCABULARY.md` §5). Add `--json` for machine-readable output.

Run the test suite (validates the checkout bundle as a regression guard, since CI wiring is deferred):

```sh
.venv/bin/pytest
```

## Visualizing the bundle

Google's own OKF reference implementation ships an HTML graph viewer; `okf-validator`'s
`visualize` subcommand is the equivalent, generating a single self-contained HTML file
(Cytoscape.js graph + Marked.js markdown pane, both loaded from CDN, no build step):

```sh
cd validator
.venv/bin/okf-validator visualize ../bundle --name "Checkout journey pilot"
```

Writes `../bundle/viz.html` by default (`--out` to change the path) — open it in a browser.
Click a node for its frontmatter, rendered body, and typed links in/out; filter by type or search
by title/id/tag.

Unlike the Google reference viewer, which reconstructs its graph by scraping markdown prose links,
edges here come from this project's own typed-relationship frontmatter fields (`VOCABULARY.md`
§3) — the same structured graph the validator's graph pass checks. Prose links in the body are
still rendered and made clickable, so both signals are visible. `viz.html` is a generated artifact
(gitignored), not something to hand-edit or commit.

## Third-party code

`validator/okf_validator/viewer/` (`viz.css`, `viz.html`, `viz.js`, and to a lesser extent
`generator.py`) is adapted from Google's own OKF reference implementation,
[`GoogleCloudPlatform/knowledge-catalog`](https://github.com/GoogleCloudPlatform/knowledge-catalog)
(`okf/src/reference_agent/viewer/`). Per that repository's own README: "All solutions within
this repository are provided under the [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0)
license." See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for which files, what changed, and
the full license text.

## Status

- Vocabulary: drafted, not yet exercised by a second journey.
- Validator: field pass + graph pass implemented, smoke-tested against deliberately broken input (type-mismatch, cardinality, broken-link all caught correctly). Not fuzzed, not exercised against adversarial frontmatter.
- Viewer: `okf-validator visualize` implemented and tested against the checkout bundle; renders the typed-relationship graph, not a markdown-link reconstruction of it.
- Generators: mapping sketches only. No Terraform or ArgoCD generator has been written.
- CI: not wired up. Run the validator or `pytest` manually before pushing.
