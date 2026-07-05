"""The vantage-aware diff — claims carry (source, vantage), so a source that
disagrees with itself across vantages is source_equivocation, distinct from
cross-source field divergence."""

from __future__ import annotations

from _helpers import StubView

from sm_resolver import Claim, diff_claims

A = "src-a"
B = "src-b"


def _present(source: str, vantage: str | None, view: StubView) -> Claim[StubView]:
    return Claim(source, vantage, "present", view, 0.0, "present")


def _absent(source: str, vantage: str | None = None) -> Claim[StubView]:
    return Claim(source, vantage, "absent", None, 0.0, "absent")


def test_two_sources_agree_yields_nothing() -> None:
    claims = [_present(A, None, StubView(endpoint="e")), _present(B, None, StubView(endpoint="e"))]
    assert diff_claims("x", claims) == []


def test_cross_source_field_divergence() -> None:
    claims = [_present(A, None, StubView(endpoint="real")), _present(B, None, StubView(endpoint="evil"))]
    findings = diff_claims("x", claims)
    assert [f.kind for f in findings] == ["endpoint"]
    assert findings[0].detail == {"field": "endpoint", "values": {A: "real", B: "evil"}}


def test_omission() -> None:
    claims = [_present(A, None, StubView(endpoint="e")), _absent(B)]
    findings = diff_claims("x", claims)
    assert [f.kind for f in findings] == ["omission"]
    assert findings[0].detail == {"present_on": [A], "missing_from": [B]}


def test_source_equivocation_across_vantages() -> None:
    # One source, two vantages, disagreeing on endpoint.
    claims = [
        _present(A, "eu", StubView(endpoint="here")),
        _present(A, "us", StubView(endpoint="there")),
    ]
    findings = diff_claims("x", claims)
    assert [f.kind for f in findings] == ["source_equivocation"]
    assert findings[0].detail == {
        "source": A,
        "field": "endpoint",
        "values": {"eu": "here", "us": "there"},
    }


def test_equivocating_source_is_excluded_from_cross_source_comparison() -> None:
    # A equivocates on endpoint; B agrees with one of A's vantages. The only
    # finding is A's self-equivocation — A contributes no agreed value, so there
    # is no spurious cross-source endpoint divergence.
    claims = [
        _present(A, "eu", StubView(endpoint="here")),
        _present(A, "us", StubView(endpoint="there")),
        _present(B, None, StubView(endpoint="here")),
    ]
    kinds = sorted(f.kind for f in diff_claims("x", claims))
    assert kinds == ["source_equivocation"]


def test_consistent_vantages_are_not_equivocation() -> None:
    # A's two vantages agree; B differs → ordinary cross-source divergence.
    claims = [
        _present(A, "eu", StubView(endpoint="same")),
        _present(A, "us", StubView(endpoint="same")),
        _present(B, None, StubView(endpoint="other")),
    ]
    findings = diff_claims("x", claims)
    assert [f.kind for f in findings] == ["endpoint"]
    assert findings[0].detail == {"field": "endpoint", "values": {A: "same", B: "other"}}


def test_none_field_never_participates() -> None:
    claims = [
        _present(A, None, StubView(endpoint="e", key="z6MkA")),
        _present(B, None, StubView(endpoint="e", key=None)),
    ]
    assert diff_claims("x", claims) == []


def test_error_claim_contributes_nothing() -> None:
    claims: list[Claim[StubView]] = [
        _present(A, None, StubView(endpoint="e")),
        Claim(B, None, "error", None, 0.0, "error"),
    ]
    assert diff_claims("x", claims) == []
