"""Corroborate sources about the same agent — agreement, then a lie.

Sources are asked about the same agent. Each ``check`` returns one
``SweepResult`` per subject: a verdict (AGREE / DIVERGENT / INSUFFICIENT), the
claims, and the findings. When the sources agree the verdict is AGREE with no
findings. When one serves a different endpoint (tampering) and a third omits the
agent entirely, the verdict is DIVERGENT and the kernel reports exactly those
two disagreements — with no network and no format knowledge, just views and a
diff.

Run:  python examples/corroborate_sources.py
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from dataclasses import dataclass

from sm_resolver import Corroborator, Status


@dataclass(frozen=True)
class RecordView:
    """A source's claim about an agent, reduced to its endpoint."""

    endpoint: str | None = None

    def comparable(self) -> Mapping[str, str | None]:
        return {"endpoint": self.endpoint}


class FakeSource:
    """Stands in for a per-source resolver — canned answers, no I/O."""

    def __init__(self, label: str, table: dict[str, tuple[Status, RecordView | None]]) -> None:
        self.label = label
        self._table = table

    async def resolve(self, agent_id: str) -> tuple[Status, RecordView | None]:
        return self._table.get(agent_id, ("error", None))


async def main() -> None:
    real = RecordView(endpoint="https://acme.example")
    fake = RecordView(endpoint="https://attacker.example")

    honest = FakeSource("registry-a", {"acme": ("present", real)})
    liar = FakeSource("registry-b", {"acme": ("present", fake)})
    hider = FakeSource("registry-c", {"acme": ("absent", None)})

    agree = await Corroborator([honest, FakeSource("registry-d", {"acme": ("present", real)})]).check(["acme"])
    print("Two honest sources agree:")
    for r in agree:
        print(f"  {r.agent_id}: {r.verdict} ({len(r.findings)} findings)")

    diverge = await Corroborator([honest, liar, hider]).check(["acme"])
    print("\nOne tampers, one omits:")
    for r in diverge:
        print(f"  {r.agent_id}: {r.verdict}")
        for f in r.findings:
            print(f"    [{f.kind}/{f.confirmation}] {f.detail}")


if __name__ == "__main__":
    asyncio.run(main())
