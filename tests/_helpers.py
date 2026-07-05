"""Shared test doubles — a stub view and a canned resolver, standing in for a
real layer's view type and per-source adapter.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from sm_resolver import Status


@dataclass(frozen=True)
class StubView:
    """A two-field view (implements the ``View`` contract)."""

    endpoint: str | None = None
    key: str | None = None

    def comparable(self) -> Mapping[str, str | None]:
        return {"endpoint": self.endpoint, "key": self.key}


class FakeResolver:
    """A resolver backed by a canned ``{agent_id: (Status, StubView | None)}`` table."""

    def __init__(self, label: str, table: dict[str, tuple[Status, StubView | None]]) -> None:
        self._label = label
        self._table = table

    @property
    def label(self) -> str:
        return self._label

    async def resolve(self, agent_id: str) -> tuple[Status, StubView | None]:
        return self._table.get(agent_id, ("error", None))
