"""The Finding — stable fingerprint for dedup, dict form, and confirmation."""

from __future__ import annotations

from dataclasses import replace

from sm_resolver import CONFIRMED, SCOPE_VIOLATION, SUSPECTED, Finding


def test_fingerprint_is_stable_and_order_independent() -> None:
    a = Finding("endpoint", "x", {"field": "endpoint", "values": {"a": "1", "b": "2"}})
    b = Finding("endpoint", "x", {"field": "endpoint", "values": {"b": "2", "a": "1"}})
    assert a.fingerprint() == b.fingerprint()


def test_distinct_findings_have_distinct_fingerprints() -> None:
    a = Finding("endpoint", "x", {"field": "endpoint", "values": {"a": "1", "b": "2"}})
    c = Finding("omission", "x", {"present_on": ["a"], "missing_from": ["b"]})
    assert a.fingerprint() != c.fingerprint()


def test_confirmation_defaults_to_suspected() -> None:
    assert Finding("key", "x", {}).confirmation == SUSPECTED


def test_fingerprint_ignores_confirmation() -> None:
    # The same disagreement keeps one fingerprint as it moves suspected→confirmed.
    f = Finding("endpoint", "x", {"field": "endpoint", "values": {"a": "1", "b": "2"}})
    assert f.fingerprint() == replace(f, confirmation=CONFIRMED).fingerprint()


def test_to_dict() -> None:
    f = Finding("key", "x", {"field": "key", "values": {"a": "z1"}})
    assert f.to_dict() == {
        "kind": "key",
        "agent_id": "x",
        "confirmation": SUSPECTED,
        "detail": {"field": "key", "values": {"a": "z1"}},
        "declared": False,
        "declaration_version": None,
    }


# ── declared divergence: annotation, not absolution ──────────


def test_declared_and_declaration_version_default_to_undeclared() -> None:
    f = Finding("endpoint", "x", {})
    assert f.declared is False
    assert f.declaration_version is None


def test_fingerprint_ignores_declaration_state() -> None:
    # The fingerprint identifies the DISAGREEMENT. A source publishing an Answer
    # Scope must not change the identity of a finding already being tracked —
    # otherwise `_first_seen`/`_emitted` miss and every historical finding
    # re-emits as suspected.
    f = Finding("endpoint", "x", {"field": "endpoint", "values": {"a": "1", "b": "2"}})
    annotated = replace(f, declared=True, declaration_version="7")
    assert f.fingerprint() == annotated.fingerprint()


def test_to_dict_carries_the_declaration_state() -> None:
    f = Finding("key", "x", {"field": "key", "values": {"a": "z1"}}, declared=True, declaration_version="3")
    assert f.to_dict() == {
        "kind": "key",
        "agent_id": "x",
        "confirmation": SUSPECTED,
        "detail": {"field": "key", "values": {"a": "z1"}},
        "declared": True,
        "declaration_version": "3",
    }


def test_scope_violation_kind_is_bare() -> None:
    # draft §11 reserves un-prefixed kind names for kinds the draft seeds, and
    # draft -01 seeds this one. A vendor prefix here would be wrong: it would
    # namespace the kind against our own document.
    assert SCOPE_VIOLATION == "scope_violation"
    assert "." not in SCOPE_VIOLATION
