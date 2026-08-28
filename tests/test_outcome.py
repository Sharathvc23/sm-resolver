"""An `error` claim should say why it failed.

`outcome` was set to the status, so it duplicated a field already present and
carried nothing. But a consumer needs to tell apart a source that timed out, one
that is persistently unreachable, one that refused, and one that answered with a
body it could not read — those are different signals about the source, and the
diff deliberately excludes all of them equally.

The kernel cannot know which it was; only the resolver can. So a resolver MAY
return a third element saying so, and the vocabulary is seeded here rather than
left for each implementation to invent incomparable strings.
"""

from __future__ import annotations

import pytest
from _helpers import StubView

from sm_resolver import (
    OUTCOME_REFUSED,
    OUTCOME_TIMEOUT,
    OUTCOME_UNPARSEABLE,
    OUTCOME_UNREACHABLE,
    OUTCOME_UNVERIFIABLE,
    Corroborator,
    Status,
)


class TwoTuple:
    """A resolver written before outcomes existed."""

    def __init__(self, status: Status = "error", label: str = "legacy") -> None:
        self._status = status
        self.label = label

    async def resolve(self, agent_id: str) -> tuple[Status, StubView | None]:
        return self._status, (StubView(endpoint="https://a.example") if self._status == "present" else None)


class ThreeTuple:
    """A resolver that says why."""

    label = "modern"

    def __init__(self, status: Status, outcome: str) -> None:
        self._status, self._outcome = status, outcome

    async def resolve(self, agent_id: str) -> tuple[Status, StubView | None, str]:
        view = StubView(endpoint="https://a.example") if self._status == "present" else None
        return self._status, view, self._outcome


@pytest.mark.asyncio
async def test_a_resolver_can_say_why_it_failed() -> None:
    c = Corroborator([ThreeTuple("error", OUTCOME_TIMEOUT), TwoTuple("present")])
    (result,) = await c.check(["x"])
    outcomes = {claim.source: claim.outcome for claim in result.claims}
    assert outcomes["modern"] == OUTCOME_TIMEOUT


@pytest.mark.asyncio
async def test_a_resolver_that_does_not_still_works() -> None:
    # Back-compat: a two-tuple resolver keeps its status as the outcome, which is
    # what it did before and is the least specific honest answer.
    c = Corroborator([TwoTuple("error", "a"), TwoTuple("present", "b")])
    (result,) = await c.check(["x"])
    assert {claim.outcome for claim in result.claims} == {"error", "present"}


@pytest.mark.asyncio
async def test_an_outcome_does_not_change_the_diff() -> None:
    # Saying WHY a source failed must not make it count as a claim. An error is
    # excluded from the diff whatever its outcome.
    c = Corroborator([ThreeTuple("error", OUTCOME_REFUSED), TwoTuple("present")])
    (result,) = await c.check(["x"])
    assert result.verdict == "INSUFFICIENT"
    assert result.findings == []


@pytest.mark.asyncio
async def test_a_resolver_that_raises_is_still_an_error() -> None:
    class Boom:
        label = "boom"

        async def resolve(self, agent_id: str) -> tuple[Status, StubView | None]:
            raise RuntimeError("network")

    c = Corroborator([Boom(), TwoTuple("present")])
    (result,) = await c.check(["x"])
    boom = next(claim for claim in result.claims if claim.source == "boom")
    assert boom.status == "error"
    assert boom.outcome == OUTCOME_UNREACHABLE


def test_the_seeded_vocabulary_is_bare_and_distinct() -> None:
    # Bare names are reserved for values this kernel seeds; anything else a
    # deployment introduces carries a reverse-DNS prefix, as finding kinds do.
    seeded = {
        OUTCOME_TIMEOUT,
        OUTCOME_UNREACHABLE,
        OUTCOME_REFUSED,
        OUTCOME_UNPARSEABLE,
        OUTCOME_UNVERIFIABLE,
    }
    assert len(seeded) == 5
    assert all("." not in o for o in seeded)


@pytest.mark.asyncio
async def test_an_outcome_never_decides_which_claims_are_compared() -> None:
    # Two sources that both answered, disagreeing on the endpoint. One carries a
    # deployment-specific outcome. `status` decides what enters the diff; outcome
    # is provenance and must not filter anything, or a source could be dropped
    # from comparison by describing itself.
    class Serving:
        def __init__(self, label: str, endpoint: str, outcome: str) -> None:
            self.label, self._endpoint, self._outcome = label, endpoint, outcome

        async def resolve(self, agent_id: str) -> tuple[Status, StubView | None, str]:
            return "present", StubView(endpoint=self._endpoint), self._outcome

    c = Corroborator(
        [
            Serving("a", "https://one.example", "com.example.served-from-cache"),
            Serving("b", "https://two.example", "present"),
        ]
    )
    (result,) = await c.check(["x"])
    assert result.verdict == "DIVERGENT"
    assert [f.kind for f in result.findings] == ["endpoint"]
