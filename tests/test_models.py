"""The Finding — stable fingerprint for dedup, dict form, and confirmation."""

from __future__ import annotations

from dataclasses import replace

from sm_resolver import CONFIRMED, SUSPECTED, Finding


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
    }
