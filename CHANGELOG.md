# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and this project adheres to
[Semantic Versioning](https://semver.org/).

## [0.6.0] — 2026-08-28

### Fixed — BREAKING (finding identity)

- **A source that changes its answer no longer restarts as a new finding.**
  `fingerprint()` keyed on the whole `detail`, which carries the observed values,
  so every value change produced a different finding that reset to `suspected`.

  A source rotating its lie faster than the staleness window therefore never
  reached `confirmed` — the staleness abuse described in draft §14, made worse,
  because each rotation had a different key and the pattern did not accumulate
  under one identity either.

  The identity is now per kind and excludes values (`SPEC.md` §4d): who
  disagreed about what, never what they said.

  **Breaking:** existing `_first_seen`/`_emitted` caches key differently. On
  upgrade, findings already being tracked are seen as new and restart at
  `suspected` once.

- **A cohort-scoped field divergence names its cohort** in `detail`, and the
  cohort participates in the identity. Without it, the same sources disagreeing
  in two contexts shared a fingerprint and one masked the other. An unscoped
  finding is unchanged and carries no `cohort`.

## [0.5.0] — 2026-08-28

### Fixed — corrects 0.4.0

- **The outcome channel is `resolve_with_outcome`, not a third element of
  `resolve`.** 0.4.0 widened the `Resolver` protocol's return type to a union of
  a two- and a three-tuple. Nothing broke at runtime, and 0.4.0 described that as
  additive. It was not: every typed consumer that unpacks two values from
  `resolve` now failed `mypy` with *"Too many values to unpack"*.

  A resolver that wants to say why now exposes `resolve_with_outcome`, which the
  Corroborator prefers when present. `resolve` is unchanged, so consumers
  typecheck again, and this follows the `vantage` precedent of duck-typing an
  optional capability rather than widening a shared signature.

  Found by a downstream build, not by this package's own tests — the suite only
  exercises resolvers written against the new shape, so nothing here noticed that
  the old shape had stopped typechecking.

## [0.4.0] — 2026-08-28

A claim now says *why* it ended as it did. Tracks
`draft-chandra-agent-registry-corroboration-02` (in preparation).

### Added

- **A seeded outcome vocabulary** — `OUTCOME_TIMEOUT`, `OUTCOME_UNREACHABLE`,
  `OUTCOME_REFUSED`, `OUTCOME_UNPARSEABLE`, `OUTCOME_UNVERIFIABLE`.

  `Claim.outcome` existed but was set to the status, so it duplicated a field
  already present and carried nothing. That mattered because the diff excludes
  every `error` claim equally: a timeout, a persistently unreachable host, an
  explicit refusal and an unreadable body are different signals about a source,
  and a pattern of refusals is not the same fact as a pattern of timeouts.

  Bare names are reserved for values seeded here; a deployment introducing its own
  MUST namespace it with a reverse-DNS or URI prefix, as finding kinds do, so two
  implementations do not mint incomparable strings for the same condition.

- **A `Resolver` MAY return a third element** carrying the outcome. Only the
  resolver knows why a resolve ended as it did; the kernel cannot infer it. A
  two-element resolver is unaffected and keeps its status as its outcome, so this
  is additive.

  An adapter that raises is recorded as `unreachable` rather than as the bare
  status — the kernel cannot distinguish a timeout from a crashed adapter, so it
  says the least specific true thing rather than guessing.

### Changed

- `SPEC.md` §2a states the vocabulary and one rule that is easy to get wrong:
  **an outcome MUST NOT affect which claims enter the diff.** `status` decides
  that. Were outcome to filter, a source could remove itself from comparison by
  describing itself.

## [0.3.0] — 2026-08-27

Vantage becomes a controlled term, findings carry their declaration state, and
cross-source comparison is scoped to a cohort. Tracks
`draft-chandra-agent-registry-corroboration-01`.

### Changed — BREAKING
- **`Finding.to_dict()` emits two further keys**, `declared` and
  `declaration_version`. Additive to the mapping, but a consumer asserting an
  exact dict, or validating against a schema with `additionalProperties: false`,
  will break. `Finding.fingerprint()` is deliberately **unchanged** — it hashes
  only `{kind, agent_id, detail}`, so a source publishing or revising a
  declaration cannot alter the identity of a finding already being tracked, and
  existing first-observation and dedup caches survive the upgrade intact.
- **`SPEC.md` is `resolver/0.3-draft`.** §3a rewrites vantage as a controlled
  `class:value` term (shared denotation, occupiability, non-overlap, bounded
  cardinality). The kernel still carries a vantage as an opaque string and does
  not validate the form; meeting those obligations is the sweeper's
  responsibility.

### Added
- `Finding.declared` and `Finding.declaration_version` (SPEC.md §4b). A
  declaration **annotates** a finding and never withdraws one: the finding is
  emitted and the verdict is computed as though no declaration existed. The
  kernel sets neither — it holds no declarations and verifies nothing.
- The `scope_violation` finding kind (SPEC.md §4c) — a source varying contrary
  to a declaration it published itself. Bare, not vendor-prefixed: draft §12
  reserves un-prefixed names for kinds the draft seeds, and `-01` seeds this one.
- `Declaration` and `diff_claims(..., declared=...)`. The map is inert,
  already-verified data supplied by a layer above, exactly as the
  `present`/`absent` classification already is. Zero runtime dependencies are
  unaffected: the kernel performs no verification and no I/O.

Where a declaration applies, two things change and only two — the
`source_equivocation` finding is annotated, and the source is **not excluded**
from cross-source comparison; its per-vantage values are compared against other
sources' values for the same vantage. Suppressing the finding while leaving the
exclusion in place — the obvious implementation — would let a source that
declares variation serve one vantage a forged value and be reported `AGREE`,
because nothing would remain to compare it against. A declaration redirects
comparison into a cohort; it never removes comparison.

With no declaration supplied, behaviour is unchanged: the cohort list is empty,
a single cohort spans every claim, and all 39 pre-existing tests pass unmodified.

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
