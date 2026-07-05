# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and this project adheres to
[Semantic Versioning](https://semver.org/).

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
