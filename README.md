# slo.okf

An [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf) (OKF) convention for documenting SRE customer journeys, SLI/SLO/alert/runbook chains, so an oncall human or agent can navigate from "what's breaking" to "what do I do about it" in a few hops. Borrows [OpenSLO](https://github.com/OpenSLO/OpenSLO)'s object model as a naming donor and [KCP](https://github.com/Cantara/knowledge-context-protocol)'s temporal-validity field names, without depending on either.

## What's here

- **[VOCABULARY.md](VOCABULARY.md)** — the controlled vocabulary: 9 concept types, frontmatter fields, typed-relationship conventions, cardinality rules. Read this before adding a concept.
- **[bundle/](bundle/)** — the actual OKF bundle, one worked example (a checkout journey) end to end. Start at [bundle/index.md](bundle/index.md).
- **[validator/](validator/)** — a Python CLI, `okf-validator`, with a `validate` subcommand (checks `bundle/` against `VOCABULARY.md`), a `review` subcommand (flags concepts overdue for re-review; see "Reviewing staleness" below), a `visualize` subcommand (renders `bundle/` as a self-contained HTML graph view; see "Visualizing the bundle" below), and an `index` subcommand (generates `index.md` files per the OKF spec's §6; see "Generating index.md files" below).
- **[generators/](generators/)** — Terraform generator: working module prototypes for 7 of the
  9 vocabulary types (`generators/terraform/modules/okf-<type>/`), see "Documenting
  infrastructure with Terraform" below. ArgoCD generator: still a mapping sketch, not
  implemented.

## What's missing

The biggest risk in a huge pile of writeup is the immediate start of aging after saving.
By adopting certain frontmatter fields I hope to counter this; ideally there is a review process, even better the sources are code and text is generated. 

_(from [VOCABULARY.md](VOCABULARY.md]) section "2. Cross-cutting frontmatter fields")_

| Field | Type | Meaning |
|---|---|---|
| `created` | date (`YYYY-MM-DD`) | When the concept was first authored. |
| `reviewed` | date (`YYYY-MM-DD`) | Last time a human confirmed this is still accurate. **Attestation, not correctness** — see §3. |
| `review_interval` | string (`<N>d` / `<N>mo`) | Expected cadence between reviews, e.g. `90d`. Used to flag `reviewed` going stale. |

The validator's `review` subcommand computes which concepts are due, so nothing has to be
tracked by hand — see "Reviewing staleness" below. Whether the content is *still correct*, only
the reviewer knows ;-)

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

OKF's own convention treats a bundle's root `index.md` as the natural entry point, which argues for putting it at the
repo root. But this repo also needs project docs (`VOCABULARY.md`, `README.md`) and tooling (`validator/`, `generators/`)
that are emphatically *not* concepts — and the validator's core invariant is "every non-reserved `.md` file in the bundle
has `type` frontmatter."

## Running the validator

```sh
cd validator
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/okf-validator validate ../bundle --strict
```

Default mode prints issues and exits 0 (OKF's own conformance rules are permissive by design). `--strict` exits 1 on any
error-severity issue — this is our producer-side CI discipline, deliberately stricter than what OKF requires of consumers
(see `VOCABULARY.md` §5). Add `--json` for machine-readable output.

**Please note**, the validator checks links and back-links between eg. Journey and Sub-systems and enforces the inherit
loose coupling of free text.

Run the test suite (validates the checkout bundle as a regression guard, since CI wiring is deferred):

```sh
.venv/bin/pytest
```

## Reviewing staleness

`okf-validator`'s `review` subcommand walks every concept in the bundle and, for each one that
declares a `review_interval` (`VOCABULARY.md` §2), computes whether it's due: `reviewed` plus
the interval, compared against today. If `reviewed` is absent, `created` is used as the starting
point instead — a concept that's never been formally reviewed is still aging from the day it was
written. Concepts with no `review_interval` at all aren't subject to a review cadence and are
skipped.

```sh
cd validator
.venv/bin/okf-validator review ../bundle --strict
```

Default mode prints a status line per concept (`ok` / `OVERDUE`, its due date, and which field the
due date was computed from) and exits 0. `--strict` exits 1 if anything is overdue, or if a
concept sets `review_interval` but has neither `reviewed` nor `created` to compute a due date
from (so a due date genuinely can't be determined) — same producer-side CI discipline as
`validate --strict`. Add `--json` for machine-readable output, or `--as-of YYYY-MM-DD` to check
staleness as of a date other than today.

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

## Generating index.md files

The OKF spec's §6 says an `index.md` MAY appear in any directory, enumerating that directory's
contents for progressive disclosure, and that producers MAY generate it automatically. Google's
own reference implementation does this as a post-step of its agentic bundle-authoring pipeline
(LLM-synthesized one-line blurb for subdirectories with more than one child). `okf-validator`'s
`index` subcommand is a deterministic port: same per-directory, per-type grouping and relative-link
format, but no LLM call — a subdirectory's description is reused only when it has exactly one
entry with a description, and left blank otherwise.

```sh
cd validator
.venv/bin/okf-validator index ../bundle --check   # exit 1 if any index.md is missing or stale
.venv/bin/okf-validator index ../bundle           # write/overwrite every index.md the bundle needs
```

## Documenting infrastructure with Terraform

`generators/terraform/modules/okf-<type>/` are Terraform modules — one each for `Subsystem`,
`DataSource`, `Service`, `Metric`, `SLI`, `SLO`, and `Alert` — that write/update one concept
file, called directly from the Terraform code that defines the thing being documented (a
network, database, service, telemetry source, or — if a team's monitoring is itself Terraform,
e.g. Datadog's provider — a metric/indicator/objective/alert), at the point a human is already
looking at and reasoning about that resource, rather than reverse-engineering topology from
`terraform show -json` after the fact. `CustomerJourney` and `Runbook` deliberately have no
module — VOCABULARY.md §4 states they're permanently hand-authored, and a module would
contradict that.

```hcl
module "cart_service_subsystem" {
  source = "path/to/slo.okf/generators/terraform/modules/okf-subsystem"

  bundle_root = "/path/to/slo.okf/bundle"
  id          = "cart-service"
  title       = "Cart Service"
  resource    = "git@example.com:acme/cart-service.git"
  owner       = "checkout-team"
  journeys    = ["journeys/checkout"]
  freetext    = "Owns cart state until checkout hands off to payment-service."
}
```

Frontmatter is fully owned by the module and rewritten every `terraform apply`; the free-text
body is wrapped in `OKF:FREETEXT` markers and, once the file exists, a human can edit that prose
directly and it survives regeneration — the module reads it back off disk rather than
overwriting it. `created`/`timestamp` are stamped via the `hashicorp/time` provider's
`time_static`, keyed off a content hash, so a no-op `terraform apply` produces no diff and no
timestamp bump. All seven modules share that marker-preserve/timestamp logic via two internal
modules (`generators/terraform/modules/internal/`) rather than duplicating it — see
`generators/terraform/modules/okf-subsystem/README.md` for the full contract,
`generators/terraform/examples/` for worked examples (one per type, each reproducing a real
`bundle/` file), and `generators/terraform/MAPPING.md` for the design rationale (including the
state-parsing approach originally sketched there, kept as "alternatives considered", and why
`CustomerJourney`/`Runbook` are excluded).

Not yet adopted for the real `bundle/` above, and not yet wired into any real infra codebase —
see the modules' READMEs for open questions (notably: who has write/commit access to this repo
when the calling Terraform lives elsewhere).

## Relevant links

- [Open Knowledge Format Spec](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf)
- [OpenSLO](https://github.com/OpenSLO/OpenSLO)
- [KCP](https://github.com/Cantara/knowledge-context-protocol)
- A replik upon release of PKF by KCP founder Thor Henning Hetland [Google's Open Knowledge Format and the problems it deliberately doesn't solve](https://wiki.totto.org/blog/2026/06/17/googles-open-knowledge-format-and-the-problems-it-deliberately-doesnt-solve/)


## Third-party code

`validator/okf_validator/viewer/` (`viz.css`, `viz.html`, `viz.js`, and to a lesser extent
`generator.py`) is adapted from Google's own OKF reference implementation,
[`GoogleCloudPlatform/knowledge-catalog`](https://github.com/GoogleCloudPlatform/knowledge-catalog)
(`okf/src/reference_agent/viewer/`). Per that repository's own README: "All solutions within
this repository are provided under the [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0)
license." See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for which files, what changed, and
the full license text.

## Licence

Following Google's code, I provide this repo under the [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0) license.

## Status

- Vocabulary: drafted, not yet exercised by a second journey.
- Validator: field pass + graph pass implemented, smoke-tested against deliberately broken input (type-mismatch, cardinality, broken-link all caught correctly). Not fuzzed, not exercised against adversarial frontmatter.
- Review: `okf-validator review` implemented and unit-tested (day/month intervals, month-overflow clamping, `reviewed`-absent fallback to `created`, missing-basis and bad-interval reporting); the checkout bundle is confirmed clean as of its `created`/`reviewed` date.
- Viewer: `okf-validator visualize` implemented and tested against the checkout bundle; renders the typed-relationship graph, not a markdown-link reconstruction of it.
- Index: `okf-validator index` implemented and unit-tested (per-type grouping, relative links, single-child description reuse, `--check` mode); not yet run against the real `bundle/`, whose root `index.md` is still hand-authored.
- Generators: Terraform — 7 module prototypes (`Subsystem`, `DataSource`, `Service`, `Metric`, `SLI`, `SLO`, `Alert`) implemented and verified (rendered, validated against `okf_validator`'s real pydantic models, idempotent from first apply, hand-edit-preserving, fail safe on corrupted markers), sharing marker-preserve/timestamp logic via internal modules; `CustomerJourney`/`Runbook` deliberately excluded (VOCABULARY.md §4); not yet adopted for the real `bundle/`. ArgoCD — mapping sketch only, no generator written.
- CI: not wired up. Run the validator or `pytest` manually before pushing.
