"""The claim — one source's answer about one agent, from one vantage, at one instant.

The unit of observation is ``(source, vantage, agent, observed_at)``. Vantage is
a distinct axis: intra-source disagreement across vantages attributes a different
misbehavior (equivocation by that source) than inter-source disagreement, so the
axes must not be collapsed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic

from .resolver import Status
from .view import ViewT


@dataclass(frozen=True)
class Claim(Generic[ViewT]):
    """One source's classified answer about one agent from one vantage.

    ``view`` is populated only for ``present``. ``observed_at`` is epoch seconds.
    ``outcome`` is the resolver's outcome string (preserved for audit, including
    for ``error`` claims which are excluded from the diff).
    """

    source: str
    vantage: str | None
    status: Status
    view: ViewT | None
    observed_at: float
    outcome: str = ""
