"""What makes two findings the same disagreement.

`fingerprint()` keyed on the whole `detail`, which carries the observed values.
So a source that changed its answer produced a *different* finding, resetting it
to `suspected`.

That is the staleness abuse the draft's own security considerations describe,
made worse: a source rotating its lie faster than the staleness window never
reaches `confirmed`, and because each rotation has a different key, the pattern
does not accumulate under one identity either.

The identity is *who disagreed about what*, not *what they said*. Values change
as the disagreement persists; the disagreement is the same one.
"""

from __future__ import annotations

from dataclasses import replace

from sm_resolver import CONFIRMED, OMISSION, SCOPE_VIOLATION, SOURCE_EQUIVOCATION, Finding

A, B, C = "src-a", "src-b", "src-c"


def _field(values: dict[str, str], cohort: str | None = None) -> Finding:
    detail: dict[str, object] = {"field": "endpoint", "values": values}
    if cohort is not None:
        detail["cohort"] = cohort
    return Finding("endpoint", "x", detail)


# ── the same disagreement, restated ──────────────────────────


def test_a_source_changing_its_value_is_the_same_disagreement() -> None:
    # The one that matters. Rotating a lie must not reset confirmation.
    assert _field({A: "1", B: "2"}).fingerprint() == _field({A: "1", B: "9"}).fingerprint()


def test_both_sources_changing_is_still_the_same_disagreement() -> None:
    assert _field({A: "1", B: "2"}).fingerprint() == _field({A: "7", B: "8"}).fingerprint()


def test_an_equivocating_source_changing_its_values_is_the_same_disagreement() -> None:
    a = Finding(SOURCE_EQUIVOCATION, "x", {"source": A, "field": "endpoint", "values": {"eu": "1", "us": "2"}})
    b = Finding(SOURCE_EQUIVOCATION, "x", {"source": A, "field": "endpoint", "values": {"eu": "3", "us": "4"}})
    assert a.fingerprint() == b.fingerprint()


# ── a different disagreement ─────────────────────────────────


def test_a_different_set_of_sources_is_a_different_disagreement() -> None:
    assert _field({A: "1", B: "2"}).fingerprint() != _field({A: "1", C: "2"}).fingerprint()


def test_a_third_source_joining_is_a_different_disagreement() -> None:
    assert _field({A: "1", B: "2"}).fingerprint() != _field({A: "1", B: "2", C: "3"}).fingerprint()


def test_a_different_field_is_a_different_disagreement() -> None:
    a = _field({A: "1", B: "2"})
    b = Finding("key", "x", {"field": "key", "values": {A: "1", B: "2"}})
    assert a.fingerprint() != b.fingerprint()


def test_the_same_sources_disagreeing_in_two_cohorts_are_two_disagreements() -> None:
    # Without the cohort in the identity these collapse into one, and a
    # divergence in one region would mask a different divergence in another.
    assert _field({A: "1", B: "2"}, "region:eu").fingerprint() != _field({A: "3", B: "4"}, "region:us").fingerprint()


def test_a_different_equivocating_source_is_a_different_disagreement() -> None:
    a = Finding(SOURCE_EQUIVOCATION, "x", {"source": A, "field": "endpoint", "values": {}})
    b = Finding(SOURCE_EQUIVOCATION, "x", {"source": B, "field": "endpoint", "values": {}})
    assert a.fingerprint() != b.fingerprint()


def test_omission_is_keyed_on_which_sources_served_and_which_denied() -> None:
    a = Finding(OMISSION, "x", {"present_on": [A], "missing_from": [B]})
    same = Finding(OMISSION, "x", {"present_on": [A], "missing_from": [B]})
    other = Finding(OMISSION, "x", {"present_on": [A], "missing_from": [C]})
    assert a.fingerprint() == same.fingerprint()
    assert a.fingerprint() != other.fingerprint()


def test_a_different_subject_is_a_different_disagreement() -> None:
    a = _field({A: "1", B: "2"})
    b = replace(a, agent_id="y")
    assert a.fingerprint() != b.fingerprint()


# ── unchanged properties ─────────────────────────────────────


def test_confirmation_and_declaration_still_do_not_participate() -> None:
    f = _field({A: "1", B: "2"})
    assert f.fingerprint() == replace(f, confirmation=CONFIRMED).fingerprint()
    assert f.fingerprint() == replace(f, declared=True, declaration_version="7").fingerprint()


def test_an_unknown_kind_falls_back_to_the_whole_detail() -> None:
    # A namespaced kind this kernel does not seed has no known detail shape, so
    # nothing may be assumed stable. Conservative: key on all of it.
    a = Finding("com.example.custom", "x", {"anything": "1"})
    b = Finding("com.example.custom", "x", {"anything": "2"})
    assert a.fingerprint() != b.fingerprint()


def test_scope_violation_is_keyed_on_the_source_field_and_declared_class() -> None:
    a = Finding(SCOPE_VIOLATION, "x", {"source": A, "field": "endpoint", "declared_class": "region", "observed": "1"})
    b = Finding(SCOPE_VIOLATION, "x", {"source": A, "field": "endpoint", "declared_class": "region", "observed": "2"})
    c = Finding(SCOPE_VIOLATION, "x", {"source": A, "field": "endpoint", "declared_class": "asn", "observed": "1"})
    assert a.fingerprint() == b.fingerprint()
    assert a.fingerprint() != c.fingerprint()


def test_a_namespaced_kind_with_a_values_map_is_still_keyed_on_all_of_it() -> None:
    # A kind this kernel does not seed may use `values` to mean something else
    # entirely. Applying the field-divergence rule to it would silently key on a
    # subset of a shape we do not define, so the whole detail is used.
    a = Finding("com.example.custom", "x", {"field": "f", "values": {A: "1", B: "2"}})
    b = Finding("com.example.custom", "x", {"field": "f", "values": {A: "1", B: "9"}})
    assert a.fingerprint() != b.fingerprint()
