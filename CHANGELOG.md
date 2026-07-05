# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and this project adheres to
[Semantic Versioning](https://semver.org/).

## [0.2.0] — 2026-07-04

The claim model gains a vantage axis, sweeps carry a verdict, and findings carry
a confirmation state. The `sm-*` stack is the reference implementation of the
IETF draft *Multi-Source Corroboration for AI Agent Discovery*
(`draft-chandra-agent-registry-corroboration-00`).

### Added
- **`Claim`** — one source's answer from one *vantage* at one instant
  (`source`, `vantage`, `status`, `view`, `observed_at`, `outcome`). The vantage
  axis (draft §3) lets a single source be observed from several network
  perspectives.
- **`diff_claims`** — the vantage-aware pure diff. Adds **`source_equivocation`**
  (draft §6.3): a source whose vantages disagree on a field's value is flagged,
  and contributes no agreed value to the cross-source comparison for that field.
- **`SweepResult`** + **`Verdict`** — each `check` now returns one `SweepResult`
  per subject: `AGREE` / `DIVERGENT` / `INSUFFICIENT` (fewer than two decisive
  claims), plus the claims (errors preserved for audit) and findings.
- **Confirmation discipline** (draft §7) — `Finding.confirmation` is `suspected`
  when first seen and `confirmed` once re-observed past `staleness_window_s`.
  `fingerprint()` excludes it, so tracking and emit-dedup stay stable.
- A resolver MAY expose a `vantage`; resolvers are deduped by `(label, vantage)`.

### Changed
- **BREAKING:** `Corroborator.check` returns `list[SweepResult]`, not
  `list[Finding]`. Read `result.findings` for the findings and `result.verdict`
  for the outcome. `check` accepts an optional `observed_at` (epoch seconds).
- **BREAKING:** `Corroborator(...)` accepts `staleness_window_s` (default `0.0`).
- `Finding` gained a `confirmation` field (default `suspected`); `to_dict()`
  now includes it.

`diff_views` is kept as a single-vantage convenience wrapper over `diff_claims`,
so existing view-map callers are unaffected. Still zero runtime dependencies.

## [0.1.0] — 2026-07-04

Initial release — the corroboration kernel, extracted from `sm-divergence` once a
second layer (identity) joined the first (discovery) as a consumer.

### Added
- **`View`** — the comparable-claim contract (`comparable() → named fields`).
- **`Resolver[T]`** — the per-source adapter protocol + `Status`.
- **`diff_views`** — the pure, generic diff (`omission` + per-field divergence),
  with the uniform `{field, values}` finding detail.
- **`Corroborator`** — resolve-all + diff + dedupe-emit orchestration.
- **`Finding`** — the finding type with a stable dedup fingerprint.

Zero runtime dependencies. `make ci-local` gate (ruff / format / mypy --strict /
pytest + runnable examples) on Python 3.11 and 3.12. Full `sm-*` doc set —
README, WHITEPAPER, SPEC, GOVERNANCE, CONTRIBUTING, PUBLISHING — plus
`examples/` and a PyPI trusted-publishing `release.yml`.
