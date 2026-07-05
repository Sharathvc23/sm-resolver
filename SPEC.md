# Corroboration Kernel — Procedure

**Spec version:** `resolver/0.1-draft`
**Status:** DRAFT / Working Draft
**Last edited:** 2026-07-04

The keywords MUST, MUST NOT, SHOULD, SHOULD NOT, MAY are to be interpreted as in RFC 2119.

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

## 4. The diff

Input is `views[source][subject]`: a view (present), `null` (absent), or *absent
from the mapping* (the `error` case — no claim). Per subject:

- **`omission`** — emit iff present on ≥1 source AND absent on ≥1 other (both
  positive claims). Detail: `{present_on, missing_from}` (sorted source lists).
- **field divergence** — for each field name in any present view's
  `comparable()`, collect the non-`None` values keyed by source; emit a finding
  of `kind = <field name>` iff more than one distinct value appears. Detail:
  `{"field": <name>, "values": {source: value}}`.

The diff MUST be pure: deterministic, no I/O, no raising. A subject MAY produce
multiple findings.

## 5. Corroborator

A `Corroborator` takes two or more resolvers, resolves each subject against each,
builds the `views` mapping (excluding `error` claims), and applies §4. Fewer than
two sources → no-op. It SHOULD deduplicate emitted findings by a stable
fingerprint over `{kind, agent_id, detail}`.

## 6. Conformance

A conforming implementation MUST reproduce, for a fixed set of per-source claim
inputs, the §4 finding set: agreement → none; present + absent → `omission`;
distinct field values → a finding of that field's kind; single/identical value or
one-value-beside-`None` → none; `error`/unreachable → excluded (no `omission`).
The diff is pure and deterministic, so conformance is mechanical.
