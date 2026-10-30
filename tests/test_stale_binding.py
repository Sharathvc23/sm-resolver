"""Supersession (SPEC.md §3b, §4e): a source behind the current lease sequence is
``stale_binding``, never a field divergence against the current source.

Motivation: registry-assisted resolution issues subject-to-target bindings as
renewable leases with a monotonically increasing ``sequence`` per authority
scope. Two registries serving the same subject at sequences 13 and 14 are not
disagreeing — one is behind. Before this rule the diff reported that as an
``endpoint`` divergence, which reads as tampering. That is a false accusation
against an honest-but-lagging source.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from sm_resolver import (
    STALE_BINDING,
    Binding,
    Claim,
    Corroborator,
    Finding,
    Status,
    diff_claims,
)


@dataclass(frozen=True)
class LeaseView:
    """A view carrying a lease position (implements ``binding()``)."""

    endpoint: str | None = None
    sequence: int | None = None
    scope: str | None = None

    def comparable(self) -> Mapping[str, str | None]:
        return {"endpoint": self.endpoint}

    def binding(self) -> Binding | None:
        if self.sequence is None:
            return None
        return Binding(self.sequence, self.scope)


def _claim(source: str, view: LeaseView | None, status: Status = "present", vantage: str | None = None) -> Claim:
    return Claim(source, vantage, status, view, 0.0, status)


def _kinds(findings: list[Finding]) -> list[str]:
    return sorted(f.kind for f in findings)


# --- the core rule --------------------------------------------------------


def test_lower_sequence_is_stale_binding_not_field_divergence() -> None:
    findings = diff_claims(
        "a",
        [
            _claim("reg-a", LeaseView("https://new", 14)),
            _claim("reg-b", LeaseView("https://old", 13)),
        ],
    )
    assert _kinds(findings) == [STALE_BINDING]
    (f,) = findings
    assert f.detail == {
        "source": "reg-b",
        "scope": None,
        "sequence": 13,
        "current_sequence": 14,
        "current_on": ["reg-a"],
    }


def test_equal_sequence_different_value_is_still_divergent() -> None:
    """Sequence equal, values differ: that is the real disagreement supersession
    exists to isolate. It must still surface as a field finding."""
    findings = diff_claims(
        "a",
        [
            _claim("reg-a", LeaseView("https://real", 14)),
            _claim("reg-b", LeaseView("https://evil", 14)),
        ],
    )
    assert _kinds(findings) == ["endpoint"]


def test_current_sources_still_compared_after_stale_withheld() -> None:
    """Withholding the stale claim must not withhold the comparison among the
    sources that are current."""
    findings = diff_claims(
        "a",
        [
            _claim("reg-a", LeaseView("https://real", 14)),
            _claim("reg-b", LeaseView("https://evil", 14)),
            _claim("reg-c", LeaseView("https://older", 12)),
        ],
    )
    assert _kinds(findings) == ["endpoint", STALE_BINDING]
    endpoint = next(f for f in findings if f.kind == "endpoint")
    assert endpoint.detail["values"] == {"reg-a": "https://real", "reg-b": "https://evil"}
    stale = next(f for f in findings if f.kind == STALE_BINDING)
    assert stale.detail["source"] == "reg-c"
    assert stale.detail["current_on"] == ["reg-a", "reg-b"]


# --- scope ------------------------------------------------------------------


def test_sequences_compare_only_within_one_scope() -> None:
    """Two authority scopes have unrelated sequence spaces. A low number in one
    is not behind a high number in the other; both are current, and their
    values are compared as ordinary claims."""
    findings = diff_claims(
        "a",
        [
            _claim("reg-a", LeaseView("https://x", 3, scope="https://issuer-a")),
            _claim("reg-b", LeaseView("https://x", 900, scope="https://issuer-b")),
        ],
    )
    assert findings == []


def test_stale_within_scope_alongside_other_scope() -> None:
    findings = diff_claims(
        "a",
        [
            _claim("reg-a", LeaseView("https://x", 5, scope="s1")),
            _claim("reg-b", LeaseView("https://y", 4, scope="s1")),
            _claim("reg-c", LeaseView("https://x", 1, scope="s2")),
        ],
    )
    assert _kinds(findings) == [STALE_BINDING]
    assert findings[0].detail["scope"] == "s1"
    assert findings[0].detail["source"] == "reg-b"


# --- mixed sequenced / unsequenced ----------------------------------------


def test_unsequenced_source_is_current_in_its_own_right() -> None:
    """A source with no lease model (a DNS record, say) is neither current nor
    stale by sequence. It is compared as before."""
    findings = diff_claims(
        "a",
        [
            _claim("reg-a", LeaseView("https://real", 14)),
            _claim("dns", LeaseView("https://real")),
            _claim("reg-b", LeaseView("https://old", 13)),
        ],
    )
    assert _kinds(findings) == [STALE_BINDING]


def test_unsequenced_source_disagreeing_with_current_is_divergent() -> None:
    findings = diff_claims(
        "a",
        [
            _claim("reg-a", LeaseView("https://real", 14)),
            _claim("dns", LeaseView("https://other")),
        ],
    )
    assert _kinds(findings) == ["endpoint"]


def test_no_sequences_anywhere_is_unchanged_behaviour() -> None:
    findings = diff_claims(
        "a",
        [
            _claim("reg-a", LeaseView("https://real")),
            _claim("reg-b", LeaseView("https://evil")),
        ],
    )
    assert _kinds(findings) == ["endpoint"]


# --- omission is unaffected ------------------------------------------------


def test_stale_claim_still_counts_as_present_for_omission() -> None:
    """Being behind on the binding does not mean the subject is unknown to that
    source. A stale source is still ``present_on`` when another is absent."""
    findings = diff_claims(
        "a",
        [
            _claim("reg-a", LeaseView("https://real", 14)),
            _claim("reg-b", LeaseView("https://old", 13)),
            _claim("reg-c", None, status="absent"),
        ],
    )
    kinds = _kinds(findings)
    assert kinds == ["omission", STALE_BINDING]
    omission = next(f for f in findings if f.kind == "omission")
    assert omission.detail["present_on"] == ["reg-a", "reg-b"]


# --- vantages ---------------------------------------------------------------


def test_one_finding_per_source_across_vantages() -> None:
    """A source behind from two vantages is one condition, not two."""
    findings = diff_claims(
        "a",
        [
            _claim("reg-a", LeaseView("https://real", 14)),
            _claim("reg-b", LeaseView("https://old", 13), vantage="region:us"),
            _claim("reg-b", LeaseView("https://old", 13), vantage="region:de"),
        ],
    )
    assert _kinds(findings) == [STALE_BINDING]


def test_source_current_on_one_vantage_stale_on_another() -> None:
    """Propagation mid-flight: one vantage has caught up. The stale vantage is
    withheld; the current one is compared; no equivocation is charged, because
    the source is not serving two *current* answers."""
    findings = diff_claims(
        "a",
        [
            _claim("reg-a", LeaseView("https://real", 14)),
            _claim("reg-b", LeaseView("https://real", 14), vantage="region:us"),
            _claim("reg-b", LeaseView("https://old", 13), vantage="region:de"),
        ],
    )
    assert _kinds(findings) == [STALE_BINDING]


# --- malformed bindings ------------------------------------------------------


def test_malformed_sequence_does_not_participate() -> None:
    @dataclass(frozen=True)
    class BadView:
        endpoint: str

        def comparable(self) -> Mapping[str, str | None]:
            return {"endpoint": self.endpoint}

        def binding(self) -> object:
            return Binding(-1)  # type: ignore[arg-type]

    @dataclass(frozen=True)
    class RaisingView:
        endpoint: str

        def comparable(self) -> Mapping[str, str | None]:
            return {"endpoint": self.endpoint}

        def binding(self) -> Binding | None:
            raise RuntimeError("boom")

    findings = diff_claims(
        "a",
        [
            Claim("reg-a", None, "present", LeaseView("https://real", 14), 0.0, "present"),
            Claim("reg-b", None, "present", BadView("https://real"), 0.0, "present"),
            Claim("reg-c", None, "present", RaisingView("https://real"), 0.0, "present"),
        ],
    )
    assert findings == []


def test_bool_is_not_a_sequence() -> None:
    @dataclass(frozen=True)
    class BoolView:
        def comparable(self) -> Mapping[str, str | None]:
            return {"endpoint": "https://real"}

        def binding(self) -> Binding | None:
            return Binding(True)  # type: ignore[arg-type]

    findings = diff_claims(
        "a",
        [
            Claim("reg-a", None, "present", LeaseView("https://real", 0), 0.0, "present"),
            Claim("reg-b", None, "present", BoolView(), 0.0, "present"),
        ],
    )
    assert findings == []


# --- identity and confirmation -------------------------------------------------


def test_identity_is_source_and_scope_not_sequence_numbers() -> None:
    """A source that stays one step behind a moving current is one persistent
    finding and must reach ``confirmed``; keying on numbers would reset it."""
    a = Finding(STALE_BINDING, "a", {"source": "reg-b", "scope": None, "sequence": 13, "current_sequence": 14})
    b = Finding(STALE_BINDING, "a", {"source": "reg-b", "scope": None, "sequence": 14, "current_sequence": 15})
    c = Finding(STALE_BINDING, "a", {"source": "reg-b", "scope": "s1", "sequence": 13, "current_sequence": 14})
    assert a.fingerprint() == b.fingerprint()
    assert a.fingerprint() != c.fingerprint()


class _Reg:
    def __init__(self, label: str, view: LeaseView) -> None:
        self._label = label
        self._view = view

    @property
    def label(self) -> str:
        return self._label

    async def resolve(self, agent_id: str) -> tuple[Status, LeaseView | None]:
        return "present", self._view


async def test_verdict_is_divergent_and_finding_confirms_past_window() -> None:
    """The verdict rule is unchanged: a finding is a finding. A lagging source
    inside the staleness window is ``suspected``; one still behind after the
    window is ``confirmed`` — persistent staleness is the replay signal."""
    corr = Corroborator(
        [_Reg("a", LeaseView("https://x", 14)), _Reg("b", LeaseView("https://x", 13))], staleness_window_s=60
    )
    (r1,) = await corr.check(["s"], observed_at=1_000)
    assert r1.verdict == "DIVERGENT"
    assert [f.confirmation for f in r1.findings] == ["suspected"]
    (r2,) = await corr.check(["s"], observed_at=1_100)
    assert [f.confirmation for f in r2.findings] == ["confirmed"]
