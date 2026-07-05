"""The finding — what disagreement was found. Layer-agnostic."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

# The universal divergence kind (present on one source, confirmed-absent on
# another). Field-level kinds are named after the view field that diverged
# (e.g. "endpoint", "did", "key") and are supplied by the view, not fixed here.
OMISSION = "omission"

# A single source disagreeing with ITSELF across vantages (equivocation by that
# source), distinct from disagreement between sources.
SOURCE_EQUIVOCATION = "source_equivocation"

# Confirmation states (observation-time discipline): a first-seen disagreement
# is suspected; one re-observed past the staleness window is confirmed.
SUSPECTED = "suspected"
CONFIRMED = "confirmed"


@dataclass(frozen=True)
class Finding:
    """One divergence about one subject.

    ``kind`` is ``omission``, ``source_equivocation``, or the name of a view
    field that diverged. ``detail`` carries the contradicting claims (uniform
    per kind): ``{present_on, missing_from}`` for ``omission``, ``{field,
    values}`` for a field divergence, ``{source, field, values}`` for
    ``source_equivocation``. ``confirmation`` distinguishes legitimate
    propagation delay (``suspected``) from persistent disagreement
    (``confirmed``).
    """

    kind: str
    agent_id: str
    detail: dict[str, object] = field(default_factory=dict)
    confirmation: str = SUSPECTED

    def fingerprint(self) -> str:
        """A stable key identifying the *disagreement* — excludes
        ``confirmation`` (which changes as the same finding is re-observed), so
        first-observation tracking and emission-dedup are stable."""
        return json.dumps(
            {"kind": self.kind, "agent_id": self.agent_id, "detail": self.detail},
            sort_keys=True,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "agent_id": self.agent_id,
            "confirmation": self.confirmation,
            "detail": self.detail,
        }
