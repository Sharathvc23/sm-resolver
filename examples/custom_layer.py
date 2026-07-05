"""Build a new layer on the kernel — a view + resolvers, nothing else.

The kernel is layer-agnostic: define what field(s) matter for your domain as a
``comparable()`` view, write a thin resolver per source, and the same
``Corroborator`` and diff find the disagreements. Here the domain is an agent's
declared *model* — two catalogs that disagree flag a ``model`` divergence.

Run:  python examples/custom_layer.py
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from dataclasses import dataclass

from sm_resolver import Corroborator, Status


@dataclass(frozen=True)
class CapabilityView:
    """A catalog's claim about an agent, reduced to the declared model."""

    model: str | None = None

    def comparable(self) -> Mapping[str, str | None]:
        return {"model": self.model}


class Catalog:
    def __init__(self, label: str, model: str) -> None:
        self.label = label
        self._model = model

    async def resolve(self, agent_id: str) -> tuple[Status, CapabilityView | None]:
        return "present", CapabilityView(model=self._model)


async def main() -> None:
    findings = await Corroborator(
        [Catalog("catalog-a", "claude-opus"), Catalog("catalog-b", "some-other-model")]
    ).check(["acme"])
    for f in findings:
        print(f"  [{f.kind}] {f.agent_id}: {f.detail}")


if __name__ == "__main__":
    asyncio.run(main())
