"""The claim — one source's answer about one agent, from one vantage, at one instant.

The unit of observation is ``(source, vantage, agent, observed_at)``. Vantage is
a distinct axis: intra-source disagreement across vantages attributes a different
misbehavior (equivocation by that source) than inter-source disagreement, so the
axes must not be collapsed.

A vantage identifies the *observation context*, not the observing instance, and
SPEC.md §3a.1 gives it a ``class:value`` form drawn from a controlled vocabulary
(``region:eu``, ``asn:as64500``). The kernel does not validate that form — a
vantage is carried and compared as an opaque string — so satisfying §3a.2
(shared denotation, occupiability, non-overlap, bounded cardinality) is the
sweeper's responsibility. ``None`` asserts no context and is always sound; per
§3a.3 it is the required value where those obligations cannot be met.
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
