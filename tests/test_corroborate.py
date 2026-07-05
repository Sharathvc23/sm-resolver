"""The Corroborator — resolve every source, diff, dedupe, emit."""

from __future__ import annotations

import pytest
from _helpers import FakeResolver, StubView

from sm_resolver import Corroborator, Finding


@pytest.mark.asyncio
async def test_single_source_is_noop() -> None:
    corr: Corroborator[StubView] = Corroborator([FakeResolver("a", {"x": ("present", StubView(endpoint="e"))})])
    assert await corr.check(["x"]) == []


@pytest.mark.asyncio
async def test_agreement_no_findings() -> None:
    corr: Corroborator[StubView] = Corroborator(
        [
            FakeResolver("a", {"x": ("present", StubView(endpoint="e"))}),
            FakeResolver("b", {"x": ("present", StubView(endpoint="e"))}),
        ]
    )
    assert await corr.check(["x"]) == []


@pytest.mark.asyncio
async def test_field_divergence_detected() -> None:
    corr: Corroborator[StubView] = Corroborator(
        [
            FakeResolver("a", {"x": ("present", StubView(endpoint="real"))}),
            FakeResolver("b", {"x": ("present", StubView(endpoint="evil"))}),
        ]
    )
    assert [f.kind for f in await corr.check(["x"])] == ["endpoint"]


@pytest.mark.asyncio
async def test_omission_detected() -> None:
    corr: Corroborator[StubView] = Corroborator(
        [
            FakeResolver("a", {"x": ("present", StubView(endpoint="e"))}),
            FakeResolver("b", {"x": ("absent", None)}),
        ]
    )
    assert [f.kind for f in await corr.check(["x"])] == ["omission"]


@pytest.mark.asyncio
async def test_error_source_makes_no_claim() -> None:
    corr: Corroborator[StubView] = Corroborator(
        [
            FakeResolver("a", {"x": ("present", StubView(endpoint="e"))}),
            FakeResolver("b", {"x": ("error", None)}),
        ]
    )
    assert await corr.check(["x"]) == []


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
    first = await corr.check(["x"])
    second = await corr.check(["x"])
    assert [f.kind for f in first] == ["endpoint"]
    assert [f.kind for f in second] == ["endpoint"]  # still returned
    assert len(emitted) == 1  # emitted once


@pytest.mark.asyncio
async def test_dedupes_by_label() -> None:
    a1 = FakeResolver("same", {"x": ("present", StubView(endpoint="e1"))})
    a2 = FakeResolver("same", {"x": ("present", StubView(endpoint="e2"))})
    corr: Corroborator[StubView] = Corroborator([a1, a2])
    assert corr.labels == ["same"]
    assert await corr.check(["x"]) == []  # only one distinct source → no-op


@pytest.mark.asyncio
async def test_a_raising_resolver_is_treated_as_no_claim() -> None:
    class Boom:
        label = "boom"

        async def resolve(self, agent_id: str) -> tuple[str, StubView | None]:
            raise RuntimeError("down")

    corr: Corroborator[StubView] = Corroborator(
        [FakeResolver("a", {"x": ("present", StubView(endpoint="e"))}), Boom()]  # type: ignore[list-item]
    )
    assert await corr.check(["x"]) == []  # boom excluded, only one real claim
