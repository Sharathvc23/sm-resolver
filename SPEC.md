# Corroboration Kernel — Procedure

**Spec version:** `resolver/0.3-draft`
**Status:** DRAFT / Working Draft
**Last edited:** 2026-08-26

The keywords MUST, MUST NOT, SHOULD, SHOULD NOT, MAY are to be interpreted as in RFC 2119.

This kernel is the reference implementation of the IETF draft *Multi-Source
Corroboration for AI Agent Discovery* (`draft-chandra-agent-registry-corroboration-00`).
Section numbers below in parentheses cite that draft.

---

## 1. Introduction

Given several **sources** that each answer "what do you have for subject *X*?",
the kernel classifies each source's claim, reduces a present claim to a
comparable **view**, and diffs the views into findings. It is source-, format-,
and layer-agnostic; a consumer supplies a view type and a resolver per source.

## 2. Claim classification

For a source *S* and subject *A*, a resolver MUST resolve exactly one of:

- **`present`** — *S* served a claim, reduced to a view (§3).
- **`absent`** — *S* positively asserts *A* is unknown.
- **`error`** — any other outcome (unreachable, timeout, unparseable, or a claim
  the resolver cannot map to a view).

An `error` claim MUST be excluded from the diff entirely. It is NOT `absent`: **a
source that failed to answer has asserted nothing, and MUST NOT be treated as
claiming the subject is absent.** A resolver MUST NOT raise; a failure is `error`.

## 3. The view contract

A `present` claim MUST be reduced to a **view**: an object exposing
`comparable() → Mapping[field_name, str | None]`. The keys are the fields that
participate in the diff; a value of `None` never participates (an unverifiable or
missing field is not a disagreement). The view type is the consumer's choice.

## 3a. Claims and vantage (draft §3)

A **claim** is a source's answer about a subject from one **vantage** at one
instant: `(source, vantage, status, view, observed_at, outcome)`. The unit of the
diff is the claim, so one source observed from several vantages contributes
several claims.

A **vantage** identifies the *observation context* — the conditions under which
the claim was obtained — and NOT the observing instance. Two sweeps of the same
source from two hosts in the same context bear the same vantage.

### 3a.1 Vantage identifiers

A vantage identifier MUST be either `null` (§3a.3) or a string of the form
`class ":" value`, where `class` names the context dimension and `value` names the
point on it. Both parts MUST match `[a-z0-9]([a-z0-9-]*[a-z0-9])?`. Examples:
`region:eu`, `region:us`, `asn:as64500`.

Identifiers are compared by exact octet equality. An implementation MUST NOT
attempt to parse, order, or infer containment between values.

### 3a.2 Requirements on the vocabulary

A vantage vocabulary is only sound if independently-operated sweepers assign the
same identifier to the same context. The following are therefore normative.

- **Shared denotation.** Two claims bearing the same vantage identifier MUST
  denote the same observation context, whichever source or sweeper produced them.
  A sweeper MUST NOT mint a private meaning for a `class` defined elsewhere.
- **Occupiability.** A `class` MUST be *occupiable*: a third party MUST be able to
  construct the context and repeat the observation independently. `region` and
  `asn` are occupiable — a verifier can observe from that region or that network.
  Attributes of the *caller relationship* rather than the observation — caller
  identity, tenant, subscription tier, authorization level — are NOT occupiable
  and MUST NOT be encoded as a vantage. A claim that varies only on a
  non-occupiable attribute cannot be independently checked, and a corroborator
  that accepted one would be reporting the source's own assertion back as
  evidence.
- **Non-overlap.** Within one sweep, the vantages a sweeper uses MUST NOT overlap:
  no observation context may be denoted by two identifiers, and no identifier may
  denote two contexts. A sweeper that cannot guarantee this MUST use `null`
  rather than guess.
- **Cardinality.** A `class` MUST have a small, enumerable value set. A
  high-cardinality dimension partitions observations until nothing is compared
  against anything, which degrades corroboration to silence while appearing to
  function.

### 3a.3 The `null` vantage

`null` means *the sweeper asserts no context* — the observation was made without
controlling for any dimension. It is NOT a distinct context, and it MUST NOT be
compared for equality against a non-`null` identifier as though it named one.

`null` is the correct value for a single-vantage sweeper. It is also the required
value where a sweeper cannot satisfy §3a.2; declining to name a context is always
sound, whereas naming one wrongly is not.

### 3a.4 Absence of variation

A source that does not vary its answers by context and a source whose behaviour is
simply unknown are different states, and today's claim model conflates them: both
appear as a single claim from a single vantage.

An implementation that can distinguish them SHOULD record the distinction, so that
"this source was observed from one vantage only" is not read as "this source does
not vary." How that distinction is carried is out of scope for this version.

## 4. The diff (draft §6)

Input is the set of claims for one subject in one sweep. `error` claims
contribute nothing. Per subject:

- **`omission`** — emit iff present on ≥1 source AND absent on ≥1 other (both
  positive claims). Detail: `{present_on, missing_from}` (sorted source lists).
- **`source_equivocation`** (draft §6.3) — for each source, for each field, if
  that source's vantages report more than one distinct non-`None` value, emit
  `{"source": S, "field": <name>, "values": {vantage: value}}`. Such a
  `(source, field)` then contributes **no** agreed value to the cross-source
  comparison below (a source that disagrees with itself cannot corroborate).
- **field divergence** — for each field name, take each non-equivocating
  source's single agreed non-`None` value; emit a finding of `kind = <field
  name>` iff more than one distinct value appears across sources. Detail:
  `{"field": <name>, "values": {source: value}}`.

The diff MUST be pure: deterministic, no I/O, no raising. A subject MAY produce
multiple findings.

## 4b. Declared divergence (annotation)

A source MAY publish, in advance, a declaration of which fields it varies and
along which vantage class (§3a). A finding therefore carries two further members:

- **`declared`** — a boolean, default `false`. `true` means a declaration
  covering this variation was published by that source *before* the observation,
  and was verified.
- **`declaration_version`** — the revision of the declaration that was matched,
  or `null`. Recording it is REQUIRED whenever `declared` is `true`: without a
  version, a source retroactively legitimises past divergences by publishing a
  broader declaration today.

Three rules govern them.

- **A declaration annotates a finding; it MUST NOT withdraw one.** The finding
  stands, and the verdict (§5) is computed exactly as if the declaration did not
  exist. A corroborator reports what it observed; deciding what an annotated
  divergence is worth is the consumer's judgement, not the corroborator's.
- **`declared` MUST NOT participate in the fingerprint** (§4a). The fingerprint
  identifies the disagreement, and the disagreement does not change when the
  source publishes or revises a declaration. Were it included, publishing a
  declaration would silently reset first-observation tracking on every finding
  already being followed.
- **The kernel MUST NOT set either member.** It holds no declarations and
  performs no verification; a layer that fetches, verifies and matches them
  supplies the annotation. Absent that layer every finding is undeclared, which
  is the conservative reading.

### 4c. Scope violation

`scope_violation` names a distinct and stronger finding: a source
varied a field **contrary to a declaration it had itself published** — most
plainly, one that positively asserted it does not vary. This is not an
undeclared divergence; it is a published rule, broken.

The name is bare because draft §11 reserves un-prefixed kind names for kinds the
draft itself seeds, and draft `-01` seeds this one. A kind introduced by any
other party MUST carry a reverse-DNS or URI prefix. Consumers MUST treat an
unrecognised kind as informational and MUST NOT reject a record for carrying
one.

The kernel never emits this kind, for the same reason it never sets `declared`.
It is named here so that implementations agree on one identifier rather than
minting their own.

## 4a. Observation time and confirmation (draft §7)

Every claim carries `observed_at` (epoch seconds). A finding is **`suspected`**
when first observed and **`confirmed`** once re-observed in a later sweep whose
`observed_at` exceeds the first observation by at least a **staleness window**.
The window absorbs legitimate propagation delay; only persistent disagreement is
confirmed. A finding's stable fingerprint MUST exclude `confirmation` so that
first-observation tracking and emit-dedup are unaffected as it is promoted.

## 5. Corroborator

A `Corroborator` takes two or more resolvers, resolves each subject against each
`(source, vantage)`, and applies §4 and §4a. It returns one **sweep result** per
subject: a **verdict** — `AGREE` (≥2 decisive claims, no findings), `DIVERGENT`
(≥1 finding), or `INSUFFICIENT` (fewer than two decisive `present`/`absent`
claims) — plus the claims (with `error` claims preserved for audit) and the
findings. Resolvers are deduped by `(label, vantage)`. It SHOULD deduplicate
emitted findings by a stable fingerprint over `{kind, agent_id, detail}`.

## 6. Conformance

A conforming implementation MUST reproduce, for a fixed set of per-source claim
inputs, the §4 finding set and §5 verdict: agreement → `AGREE`, none; present +
absent → `DIVERGENT`, `omission`; distinct cross-source field values →
`DIVERGENT`, a finding of that field's kind; a source's vantages disagreeing →
`DIVERGENT`, `source_equivocation` (and no spurious cross-source divergence for
that field); single/identical value or one-value-beside-`None` → `AGREE`, none;
fewer than two decisive claims → `INSUFFICIENT`; `error`/unreachable → excluded
(never `omission`). The diff is pure and deterministic, so conformance is
mechanical.
