# Log

## 2026-07-15

**Creation**: initial checkout journey pilot bundle. Vocabulary (`VOCABULARY.md`), Python validator skeleton (`validator/`), Terraform/ArgoCD generator mapping sketches (`generators/`), and one worked end-to-end journey — cart → payment → checkout API → availability/latency SLOs → error-budget alert → runbook. All concepts hand-authored; no generator exists yet, so no `generated_by` fields appear anywhere in this bundle.

## 2026-07-22 (v0.2.0 migration)

**Migrated to VOCABULARY.md v0.2.0's `Service`/`Subsystem` split** (see VOCABULARY.md's
Changelog for the schema rationale — this bundle was left un-migrated when that schema change
landed, deliberately, to keep the change itself reviewable separately from its example fallout).

- `subsystems/cart-service.md`, `subsystems/checkout-api.md`, `subsystems/payment-service.md`
  became `services/cart-service.md`, `services/checkout-api.md`, `services/payment-service.md`
  (`type: Subsystem` → `type: Service`). Field-for-field this was almost a pure rename — the old
  `Subsystem.journeys` back-ref is now `Service.journeys`, same values, same meaning.
- `journeys/checkout.md`'s `subsystems:` frontmatter field became `services:`, same 3 targets.
- Added one new leaf `Subsystem`, `subsystems/cart-service-redis.md` (`service:
  services/cart-service`), illustrating the actual atomic/leaf role `Subsystem` now has —
  without it, this bundle would demonstrate 8 of the 9 vocabulary types, not all 9, since the
  three original `Subsystem` concepts had all become `Service`s.
- All cross-links updated (`../subsystems/*.md` → `../services/*.md`) in `journeys/checkout.md`,
  `slos/checkout-availability-slo.md`, and `runbooks/checkout-degraded.md`.
- `okf-validator index ../bundle` re-run to regenerate every `index.md`.

Still nothing generated — no `generated_by` field appears anywhere. `cart-service-redis` is
flagged in its own body as a candidate once the Terraform generator lands.
