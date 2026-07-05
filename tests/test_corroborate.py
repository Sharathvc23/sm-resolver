"""The Corroborator — resolve every (source, vantage), diff, confirm, emit."""

from __future__ import annotations

import pytest
from _helpers import FakeResolver, StubView

from sm_resolver import CONFIRMED, SUSPECTED, Corroborator, Finding, SweepResult


def _findings(results: list[SweepResult[StubView]], agent_id: str = "x") -> list[Finding]:
    return next(r.findings for r in results if r.agent_id == agent_id)


def _verdict(results: list[SweepResult[StubView]], agent_id: str = "x") -> str:
    return next(r.verdict for r in results if r.agent_id == agent_id)


@pytest.mark.asyncio
async def test_single_source_is_insufficient() -> None:
    corr: Corroborator[StubView] = Corroborator([FakeResolver("a", {"x": ("present", StubView(endpoint="e"))})])
    results = await corr.check(["x"])
    assert _findings(results) == []
    assert _verdict(results) == "INSUFFICIENT"  # only one decisive claim


@pytest.mark.asyncio
async def test_agreement_verdict_agree() -> None:
    corr: Corroborator[StubView] = Corroborator(
        [
            FakeResolver("a", {"x": ("present", StubView(endpoint="e"))}),
            FakeResolver("b", {"x": ("present", StubView(endpoint="e"))}),
        ]
    )
    results = await corr.check(["x"])
    assert _findings(results) == []
    assert _verdict(results) == "AGREE"


@pytest.mark.asyncio
async def test_field_divergence_detected() -> None:
    corr: Corroborator[StubView] = Corroborator(
        [
            FakeResolver("a", {"x": ("present", StubView(endpoint="real"))}),
            FakeResolver("b", {"x": ("present", StubView(endpoint="evil"))}),
        ]
    )
    results = await corr.check(["x"])
    assert [f.kind for f in _findings(results)] == ["endpoint"]
    assert _verdict(results) == "DIVERGENT"


@pytest.mark.asyncio
async def test_omission_detected() -> None:
    corr: Corroborator[StubView] = Corroborator(
        [
            FakeResolver("a", {"x": ("present", StubView(endpoint="e"))}),
            FakeResolver("b", {"x": ("absent", None)}),
        ]
    )
    results = await corr.check(["x"])
    assert [f.kind for f in _findings(results)] == ["omission"]
    assert _verdict(results) == "DIVERGENT"


@pytest.mark.asyncio
async def test_error_source_makes_no_claim() -> None:
    corr: Corroborator[StubView] = Corroborator(
        [
            FakeResolver("a", {"x": ("present", StubView(endpoint="e"))}),
            FakeResolver("b", {"x": ("error", None)}),
        ]
    )
    results = await corr.check(["x"])
    assert _findings(results) == []
    # one present claim + one error (not decisive) → INSUFFICIENT, never omission.
    assert _verdict(results) == "INSUFFICIENT"


@pytest.mark.asyncio
async def test_source_equivocation_across_vantages() -> None:
    # One source, two vantages, disagreeing on the endpoint value.
    corr: Corroborator[StubView] = Corroborator(
        [
            FakeResolver("s", {"x": ("present", StubView(endpoint="here"))}, vantage="eu"),
            FakeResolver("s", {"x": ("present", StubView(endpoint="there"))}, vantage="us"),
        ]
    )
    results = await corr.check(["x"])
    findings = _findings(results)
    assert [f.kind for f in findings] == ["source_equivocation"]
    assert findings[0].detail["source"] == "s"
    assert findings[0].detail["field"] == "endpoint"
    assert findings[0].detail["values"] == {"eu": "here", "us": "there"}
    assert _verdict(results) == "DIVERGENT"


@pytest.mark.asyncio
async def test_confirmation_suspected_then_confirmed() -> None:
    corr: Corroborator[StubView] = Corroborator(
        [
            FakeResolver("a", {"x": ("present", StubView(endpoint="real"))}),
            FakeResolver("b", {"x": ("present", StubView(endpoint="evil"))}),
        ],
        staleness_window_s=10.0,
    )
    first = _findings(await corr.check(["x"], observed_at=1000.0))
    assert [f.confirmation for f in first] == [SUSPECTED]
    # re-observed inside the window → still suspected.
    inside = _findings(await corr.check(["x"], observed_at=1005.0))
    assert [f.confirmation for f in inside] == [SUSPECTED]
    # re-observed past the window → confirmed.
    past = _findings(await corr.check(["x"], observed_at=1020.0))
    assert [f.confirmation for f in past] == [CONFIRMED]


@pytest.mark.asyncio
async def test_on_finding_fires_once_per_finding() -> None:
    emitted: list[Finding] = []
    corr: Corroborator[StubView] = Corroborator(
        [
            FakeResolver("a", {"x": ("present", StubView(endpoint="real"))}),
            FakeResolver("b", {"x": ("present", StubView(endpoint="evil"))}),
        ],
        on_finding=emitted.append,
    )
    first = _findings(await corr.check(["x"]))
    second = _findings(await corr.check(["x"]))
    assert [f.kind for f in first] == ["endpoint"]
    assert [f.kind for f in second] == ["endpoint"]  # still returned
    assert len(emitted) == 1  # emitted once (fingerprint stable across suspected→confirmed)


@pytest.mark.asyncio
async def test_dedupes_by_label_and_vantage() -> None:
    a1 = FakeResolver("same", {"x": ("present", StubView(endpoint="e1"))})
    a2 = FakeResolver("same", {"x": ("present", StubView(endpoint="e2"))})
    corr: Corroborator[StubView] = Corroborator([a1, a2])
    assert corr.labels == ["same"]
    results = await corr.check(["x"])
    assert _findings(results) == []
    assert _verdict(results) == "INSUFFICIENT"  # only one distinct (label, vantage)


@pytest.mark.asyncio
async def test_a_raising_resolver_is_treated_as_no_claim() -> None:
    class Boom:
        label = "boom"
        vantage = None

        async def resolve(self, agent_id: str) -> tuple[str, StubView | None]:
            raise RuntimeError("down")

    corr: Corroborator[StubView] = Corroborator(
        [FakeResolver("a", {"x": ("present", StubView(endpoint="e"))}), Boom()]  # type: ignore[list-item]
    )
    results = await corr.check(["x"])
    assert _findings(results) == []
    assert _verdict(results) == "INSUFFICIENT"  # boom is an error claim, not decisive
