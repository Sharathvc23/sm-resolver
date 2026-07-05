"""The finding — what disagreement was found. Layer-agnostic."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

# The universal divergence kind (present on one source, confirmed-absent on
# another). Field-level kinds are named after the view field that diverged
# (e.g. "endpoint", "did", "key") and are supplied by the view, not fixed here.
OMISSION = "omission"


@dataclass(frozen=True)
class Finding:
    """One divergence about one subject across the compared sources.

    ``kind`` is ``omission`` or the name of a view field that diverged.
    ``detail`` carries the contradicting per-source claims. For ``omission`` it
    is ``{present_on, missing_from}``; for a field divergence it is
    ``{field, values}`` (``values`` keyed by source label) — one uniform shape
    across every layer, so any consumer parses findings the same way.
    """

    kind: str
    agent_id: str
    detail: dict[str, object] = field(default_factory=dict)

    def fingerprint(self) -> str:
        """A stable key for deduping a persisting finding across repeated
        checks — same disagreement, same fingerprint."""
        return json.dumps(
            {"kind": self.kind, "agent_id": self.agent_id, "detail": self.detail},
            sort_keys=True,
        )

    def to_dict(self) -> dict[str, object]:
        return {"kind": self.kind, "agent_id": self.agent_id, "detail": self.detail}
