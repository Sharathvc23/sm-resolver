# Corroboration Kernel — Procedure

**Spec version:** `resolver/0.2-draft`
**Status:** DRAFT / Working Draft
**Last edited:** 2026-07-04

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
instant: `(source, vantage, status, view, observed_at, outcome)`. A vantage is a
network perspective (a region, a resolver instance); it MAY be `null` for a
single-vantage source. The unit of the diff is the claim, so one source observed
from several vantages contributes several claims.

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
