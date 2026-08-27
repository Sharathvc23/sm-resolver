"""Cohort comparison — a declaration redirects comparison, it never removes it.

A source that varies a field by an occupiable vantage class is not silenced as a
witness: its per-vantage values are compared against other sources' values *for
the same vantage*. The finding it earns for varying is still emitted, annotated
as declared (SPEC.md §4b: annotate, never withdraw).
"""

from __future__ import annotations

from _helpers import StubView
from test_diff_claims import A, B, _present

from sm_resolver import Declaration, diff_claims

EU, US = "region:eu", "region:us"
DECLARED_ENDPOINT = {(A, "endpoint"): Declaration("region", "7")}


def test_a_declared_source_still_corroborates_and_the_attack_is_caught() -> None:
    # THE invariant (design §2). A declares endpoint varies by region, then
    # serves an attacker endpoint to EU only. B is honest and single-vantage.
    #
    # Without the redirect, suppressing A's equivocation ALSO drops A from
    # cross-source comparison; `agreed` then holds only B's single value, no
    # divergence is found, and the sweep returns a clean AGREE for a registry
    # serving an attacker endpoint to every EU caller.
    claims = [
        _present(A, EU, StubView(endpoint="https://attacker.example")),
        _present(A, US, StubView(endpoint="https://acme.example")),
        _present(B, None, StubView(endpoint="https://acme.example")),
    ]
    findings = diff_claims("x", claims, declared=DECLARED_ENDPOINT)
    kinds = sorted(f.kind for f in findings)
    assert "endpoint" in kinds, "A's EU answer must still be compared against B's"

    endpoint_finding = next(f for f in findings if f.kind == "endpoint")
    assert endpoint_finding.detail["values"] == {A: "https://attacker.example", B: "https://acme.example"}


def test_the_declared_equivocation_is_annotated_not_withdrawn() -> None:
    # SPEC.md §4b: a declaration annotates a finding; it never withdraws one.
    claims = [
        _present(A, EU, StubView(endpoint="https://eu.acme.example")),
        _present(A, US, StubView(endpoint="https://us.acme.example")),
    ]
    findings = diff_claims("x", claims, declared=DECLARED_ENDPOINT)
    assert [f.kind for f in findings] == ["source_equivocation"]
    assert findings[0].declared is True
    assert findings[0].declaration_version == "7"


def test_an_undeclared_equivocation_is_unchanged() -> None:
    claims = [
        _present(A, EU, StubView(endpoint="https://eu.acme.example")),
        _present(A, US, StubView(endpoint="https://us.acme.example")),
        _present(B, None, StubView(endpoint="https://eu.acme.example")),
    ]
    findings = diff_claims("x", claims)
    assert [f.kind for f in findings] == ["source_equivocation"]
    assert findings[0].declared is False


def test_a_declaration_for_another_field_does_not_apply() -> None:
    claims = [
        _present(A, EU, StubView(key="k1")),
        _present(A, US, StubView(key="k2")),
    ]
    findings = diff_claims("x", claims, declared=DECLARED_ENDPOINT)
    assert [f.kind for f in findings] == ["source_equivocation"]
    assert findings[0].declared is False


def test_a_declaration_whose_class_does_not_match_the_vantages_does_not_apply() -> None:
    # A declared variation by region; these vantages are on a different axis, so
    # the declaration says nothing about them and the source is excluded as usual.
    claims = [
        _present(A, "asn:as64500", StubView(endpoint="https://one.example")),
        _present(A, "asn:as64501", StubView(endpoint="https://two.example")),
        _present(B, None, StubView(endpoint="https://one.example")),
    ]
    findings = diff_claims("x", claims, declared=DECLARED_ENDPOINT)
    assert [f.kind for f in findings] == ["source_equivocation"]
    assert findings[0].declared is False
    assert all(f.kind != "endpoint" for f in findings), "excluded source must not corroborate"


def test_cohorts_that_agree_produce_no_finding() -> None:
    claims = [
        _present(A, EU, StubView(endpoint="https://eu.acme.example")),
        _present(A, US, StubView(endpoint="https://us.acme.example")),
        _present(B, EU, StubView(endpoint="https://eu.acme.example")),
        _present(B, US, StubView(endpoint="https://us.acme.example")),
    ]
    declared = {(A, "endpoint"): Declaration("region", "7"), (B, "endpoint"): Declaration("region", "2")}
    findings = diff_claims("x", claims, declared=declared)
    assert [f.kind for f in findings] == ["source_equivocation", "source_equivocation"]
    assert all(f.declared for f in findings)
    assert all(f.kind != "endpoint" for f in findings), "matching cohorts are not a divergence"


def test_a_declared_source_that_does_not_vary_creates_no_cohorts() -> None:
    # A is declared for `endpoint` but serves one value everywhere. A declaration
    # is permission to vary, not an assertion of variation — so A contributes a
    # single value, no cohort is created, and the result is today's shape.
    claims = [
        _present(A, EU, StubView(endpoint="https://one.example")),
        _present(A, US, StubView(endpoint="https://one.example")),
        _present(B, None, StubView(endpoint="https://two.example")),
    ]
    findings = diff_claims("x", claims, declared=DECLARED_ENDPOINT)
    assert [f.kind for f in findings] == ["endpoint"]
    assert findings[0].detail == {"field": "endpoint", "values": {A: "https://one.example", B: "https://two.example"}}


def test_each_cohort_that_disagrees_earns_its_own_finding() -> None:
    # Two regions, two different disagreements. These are separate facts about
    # separate contexts and must not be merged into one.
    claims = [
        _present(A, EU, StubView(endpoint="https://eu-a.example")),
        _present(A, US, StubView(endpoint="https://us-a.example")),
        _present(B, EU, StubView(endpoint="https://eu-b.example")),
        _present(B, US, StubView(endpoint="https://us-b.example")),
    ]
    declared = {(A, "endpoint"): Declaration("region", "7"), (B, "endpoint"): Declaration("region", "2")}
    findings = [f for f in diff_claims("x", claims, declared=declared) if f.kind == "endpoint"]
    assert len(findings) == 2
    assert [f.detail["values"] for f in findings] == [
        {A: "https://eu-a.example", B: "https://eu-b.example"},
        {A: "https://us-a.example", B: "https://us-b.example"},
    ]
