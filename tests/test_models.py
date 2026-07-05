"""The Finding — stable fingerprint for dedup, and dict form."""

from __future__ import annotations

from sm_resolver import Finding


def test_fingerprint_is_stable_and_order_independent() -> None:
    a = Finding("endpoint", "x", {"field": "endpoint", "values": {"a": "1", "b": "2"}})
    b = Finding("endpoint", "x", {"field": "endpoint", "values": {"b": "2", "a": "1"}})
    assert a.fingerprint() == b.fingerprint()


def test_distinct_findings_have_distinct_fingerprints() -> None:
    a = Finding("endpoint", "x", {"field": "endpoint", "values": {"a": "1", "b": "2"}})
    c = Finding("omission", "x", {"present_on": ["a"], "missing_from": ["b"]})
    assert a.fingerprint() != c.fingerprint()


def test_to_dict() -> None:
    f = Finding("key", "x", {"field": "key", "values": {"a": "z1"}})
    assert f.to_dict() == {"kind": "key", "agent_id": "x", "detail": {"field": "key", "values": {"a": "z1"}}}
