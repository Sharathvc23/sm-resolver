# Governance

## Scope

| In scope | Out of scope |
| --- | --- |
| the claim classification (`present`/`absent`/`error`), the view contract (`comparable()`), the pure diff (`omission` + per-field), and the `Corroborator` orchestration | any specific source format or transport (a consumer's resolver owns that); the view type's fields (the consumer defines them); signing / verification (a consumer's resolver applies it before returning a view); a transparency log; and remediation policy on a finding |

The kernel owns one thing — answering *"do these sources disagree about this
subject, and how?"* — for any view type and any layer. Anything outside the table
belongs to a consumer (e.g. `sm-divergence`) or the caller.

## Versioning

Semantic Versioning 2.0.0. The claim classification (SPEC §2), the view contract
(SPEC §3), and the diff (SPEC §4) are frozen within a major; a change requires an
RFC-style PR to `SPEC.md` before code.

## Conformance

An implementation is conforming iff it reproduces the finding set in SPEC §6. The
diff is pure and deterministic by construction, so conformance is mechanical.
