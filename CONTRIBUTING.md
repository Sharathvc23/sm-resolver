# Contributing to sm-resolver

Contributions are accepted under the Developer Certificate of Origin (DCO)
sign-off model. Add `Signed-off-by: Your Name <you@example.com>` to every commit
(`git commit -s`).

## Change process

1. Spec-affecting changes open a PR updating the **spec (`SPEC.md`), the tests,
   and the code together**. The `tests/` suite is the authoritative behavioural
   specification of the diff.
2. The gate is `make ci-local` (uv: `ruff` → `ruff format` → `mypy --strict` →
   `pytest`). CI runs the same on Python 3.11 and 3.12. Push only when green.

## House rules

- **A timeout is not a claim.** An unreachable or erroring source MUST be
  excluded from the diff, never counted as an omission. A change here needs an
  RFC-style PR to `SPEC.md` first.
- **The diff stays pure and generic.** `diff_views` is deterministic, does no
  I/O, never raises, and never learns its layer. All I/O lives in resolvers.
- **Zero runtime dependencies.** The kernel is stdlib-only; keep it that way.
- **No expansion of the classification (SPEC §2), the view contract (SPEC §3), or
  the diff (SPEC §4) without an RFC-style PR to `SPEC.md` first.**
