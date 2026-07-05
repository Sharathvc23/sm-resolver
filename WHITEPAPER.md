# sm-resolver: A Corroboration Kernel for the Internet of AI Agents

*Personal research contribution by [Stellarminds.ai](https://stellarminds.ai), aligned with [Project NANDA](https://projectnanda.org) standards.*

---

## Abstract

Accountability for a federated system where agents reach each other through
middlemen — registries, name services, DID methods, catalogs — reduces to one
question asked over and over: *do independent sources agree about the same
subject, and if not, how do they differ?* This paper describes the minimal,
source-agnostic machinery that answers it: a per-source **resolver** that
normalizes any format to one comparable **view**, and a pure **diff** that turns
the views from all sources into findings. `sm-resolver` is that machinery and
nothing else — a dependency-free kernel other packages build layers on.

## 1. Problem

A middleman can lie: it can tamper with what it serves, omit a subject it holds,
or equivocate between clients. Signing an artifact defeats tampering, but no
signature proves what a source *withheld* or whether it showed everyone the same
thing. The robust defense is corroboration — ask two or more sources and treat
disagreement as a signal — and it recurs at every layer: a registry about an
agent's endpoint, a DID method about its key, a catalog about its capabilities.
The comparison logic is identical each time; only the wire format differs. Left
un-factored, every layer reimplements the same diff and the same "a timeout is
not an absence" subtleties, and drifts.

## 2. The corroboration primitive

The operation factors into three pieces, and only the first knows a format:

- **Resolve** — a per-source *resolver* performs that source's query, applies its
  native verification, and returns a *view*. It is the only format-aware piece;
  a thin adapter lives here.
- **View** — the comparable reduction of a claim to named string fields
  (`comparable() → {field: value}`). A `None` value never participates.
- **Diff** — a pure function over the views from all sources. It emits `omission`
  (present on one, positively absent on another) and one finding per view field
  whose values disagree. It never learns what layer it serves.

Because the diff operates on normalized views, it is untouched by format
heterogeneity — the same code compares a registry claim and a DID-document claim
once each is a view. A `Corroborator` wires it together: resolve every source,
diff, emit new findings once.

## 3. Why it is a separate package

The kernel is small (three types and one pure function) but it is the part every
accountability layer shares, so it earns its own package the moment a second
layer consumes it. Extracting it keeps each layer a *thin adapter* — a view type
and per-source resolvers — with no generic machinery of its own, and lets a layer
depend on the kernel without dragging any sibling's wire code along. The kernel
carries **zero runtime dependencies**, so adopting it commits a consumer to
nothing but the standard library.

## 4. Design axioms

Consequences of the threat model, not preferences.

1. **Corroborate, don't trust.** One artifact proves its own contents, not that
   the source served it honestly or to everyone. The minimum unit of
   accountability is two independent sources; with one, the kernel is a no-op
   rather than false assurance.
2. **A timeout is not a claim.** An unreachable source has asserted nothing and
   is excluded — never counted as an omission — so a transient fault cannot
   manufacture a false finding.
3. **Only present, comparable values disagree.** A `None` field contributes
   nothing; an unverifiable value is not a disagreement and cannot be laundered
   into one that discredits an honest source.
4. **Detect; do not remediate.** The kernel reports *that* sources disagree and
   *how*. What to do about it is caller policy.

## 5. Composition

`sm-resolver` is the base; layers supply a view and resolvers:

```
                         sm-resolver  (View · Resolver[T] · diff · Corroborator)
                                    ▲                ▲               ▲
                        discovery layer      identity layer     capability / evidence
                        RecordView +         DidView +           (a view + resolvers)
                        registry resolvers   DID-method resolvers
```

[`sm-divergence`](https://github.com/Sharathvc23/sm-divergence) is the reference
consumer: a discovery layer (registries — NEST, the NANDA Index) and an identity
layer (DID methods — `did:key`, `did:web`, a Universal Resolver), each a thin set
of resolvers over this kernel.

## 6. NANDA alignment

Project NANDA's discovery is multi-source by design — a lean Index delegating to
a quilt of registries. Corroboration is only *possible* because of that
decentralization: the redundancy built for resilience doubles as an integrity
check. `sm-resolver` is the mechanism that turns that latent property into an
active one, underpinning **accountable discovery** across the DNS and CA pillars.

## 7. Future work

- A quorum reducer over findings (*k*-of-*n* agreement) for more than two sources.
- Durable per-source divergence history (source reputation).
- A normative wire schema for a shareable `Finding` (cross-tool interchange).

## 8. Related packages

| Package | Role |
| --- | --- |
| [`sm-divergence`](https://github.com/Sharathvc23/sm-divergence) | The reference discovery + identity layers built on this kernel. |
| [`sm-bridge`](https://github.com/Sharathvc23/sm-bridge) | NANDA-compatible registry endpoints — a source a resolver corroborates across. |
| [`sm-conformance`](https://github.com/Sharathvc23/sm-conformance) | The shared Ed25519 / JCS signing convention a resolver's verification uses. |

---

## License

[MIT](LICENSE).
