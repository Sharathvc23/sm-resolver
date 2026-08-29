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

# A source varied a field contrary to its OWN published Answer Scope — it
# declared a rule and broke it. A strictly stronger accusation than an
# undeclared divergence. Bare (un-prefixed) per draft §12, which reserves bare
# names for kinds the draft itself seeds; this kind is seeded by draft -01. The
# kernel never emits it — it has no declarations, so the layer that fetches and
# matches them supplies it. Named here so the vocabulary is one thing.
SCOPE_VIOLATION = "scope_violation"

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
    declared: bool = False
    declaration_version: str | None = None

    def _identity(self) -> object:
        """The part of ``detail`` that identifies *which* disagreement this is.

        Who disagreed about what, never what they said. Values change while a
        disagreement persists, and keying on them made a source that rotated its
        answer look like a stream of unrelated findings, each restarting at
        ``suspected`` and never reaching ``confirmed``. That is the staleness
        abuse of draft §14, made worse: the pattern did not accumulate under one
        identity either.

        A kind this kernel does not seed has no known detail shape, so nothing
        may be assumed stable and the whole of it is used.
        """
        d = self.detail
        if self.kind == OMISSION:
            return {"present_on": d.get("present_on"), "missing_from": d.get("missing_from")}
        if self.kind == SOURCE_EQUIVOCATION:
            return {"source": d.get("source"), "field": d.get("field")}
        if self.kind == SCOPE_VIOLATION:
            return {
                "source": d.get("source"),
                "field": d.get("field"),
                "declared_class": d.get("declared_class"),
            }
        values = d.get("values")
        if "." not in self.kind and isinstance(values, dict):
            # A field divergence. The participating sources and the cohort are
            # the identity; the cohort matters because the same sources can
            # disagree differently in two contexts, and without it those two
            # disagreements collapse into one.
            return {
                "field": d.get("field"),
                "sources": sorted(values),
                "cohort": d.get("cohort"),
            }
        return d

    def fingerprint(self) -> str:
        """A stable key identifying the *disagreement*.

        Excludes ``confirmation`` (which changes as the same finding is
        re-observed), the declaration state (which changes when a source
        publishes or revises an Answer Scope), and the observed values (which
        change while the same disagreement persists) — so first-observation
        tracking and emission-dedup are stable across all three. See
        ``_identity``."""
        return json.dumps(
            {"kind": self.kind, "agent_id": self.agent_id, "identity": self._identity()},
            sort_keys=True,
            default=str,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "agent_id": self.agent_id,
            "confirmation": self.confirmation,
            "detail": self.detail,
            "declared": self.declared,
            "declaration_version": self.declaration_version,
        }
