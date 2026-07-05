"""The pure diff — no I/O, generic over the view type. Given the claims of one
sweep for one agent, find the disagreements. It never learns what layer it serves.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from .claim import Claim
from .models import OMISSION, SOURCE_EQUIVOCATION, Finding
from .resolver import Status
from .view import ViewT


def diff_claims(agent_id: str, claims: Iterable[Claim[ViewT]]) -> list[Finding]:
    """Diff the claims of one sweep for one agent.

    Findings carry ``confirmation = suspected``; the caller (Corroborator)
    upgrades to ``confirmed`` per observation time. Emitted:

      - ``omission``  — present on ≥1 source AND positively absent on ≥1 other.
      - ``source_equivocation`` — one source's vantages disagree on a field's
        non-``None`` value; that source then contributes no agreed value to the
        cross-source comparison for that field.
      - one per view field (``endpoint``, ``did``, ``key``, …) whose per-source
        agreed non-``None`` values disagree across sources.

    ``error`` claims contribute nothing. Deterministic; never raises.
    """
    claim_list = list(claims)
    present = [c for c in claim_list if c.status == "present" and c.view is not None]
    present_sources = sorted({c.source for c in present})
    absent_sources = sorted({c.source for c in claim_list if c.status == "absent"})

    findings: list[Finding] = []
    if present_sources and absent_sources:
        findings.append(Finding(OMISSION, agent_id, {"present_on": present_sources, "missing_from": absent_sources}))

    # Fields, in first-seen order across present views.
    field_names: list[str] = []
    for c in present:
        assert c.view is not None
        for name in c.view.comparable():
            if name not in field_names:
                field_names.append(name)

    by_source: dict[str, list[Claim[ViewT]]] = {}
    for c in present:
        by_source.setdefault(c.source, []).append(c)

    # source_equivocation: a source whose vantages disagree on a field's value.
    equivocating: set[tuple[str, str]] = set()
    for name in field_names:
        for source in sorted(by_source):
            per_vantage: dict[str | None, str] = {}
            for c in by_source[source]:
                assert c.view is not None
                value = c.view.comparable().get(name)
                if value is not None:
                    per_vantage[c.vantage] = value
            if len(set(per_vantage.values())) > 1:
                equivocating.add((source, name))
                findings.append(
                    Finding(
                        SOURCE_EQUIVOCATION,
                        agent_id,
                        {
                            "source": source,
                            "field": name,
                            "values": {str(v): per_vantage[v] for v in sorted(per_vantage, key=str)},
                        },
                    )
                )

    # cross-source field divergence, using each source's agreed value.
    for name in field_names:
        agreed: dict[str, str] = {}
        for source in sorted(by_source):
            if (source, name) in equivocating:
                continue
            values: set[str] = set()
            for c in by_source[source]:
                assert c.view is not None
                value = c.view.comparable().get(name)
                if value is not None:
                    values.add(value)
            if len(values) == 1:
                agreed[source] = next(iter(values))
        if len(set(agreed.values())) > 1:
            findings.append(Finding(name, agent_id, {"field": name, "values": dict(sorted(agreed.items()))}))

    return findings


def diff_views(
    views: Mapping[str, Mapping[str, ViewT | None]],
    watch_ids: Iterable[str],
) -> list[Finding]:
    """Single-vantage convenience over ``diff_claims``: a ``{source: {id: view |
    None}}`` mapping (view = present, ``None`` = absent, missing = no claim) is
    reduced to single-vantage claims and diffed. Returns findings for all ids."""
    findings: list[Finding] = []
    for aid in sorted(set(watch_ids)):
        claims: list[Claim[ViewT]] = []
        for source, per_source in views.items():
            if aid not in per_source:
                continue
            view = per_source[aid]
            status: Status = "absent" if view is None else "present"
            claims.append(Claim(source, None, status, view, 0.0, status))
        findings.extend(diff_claims(aid, claims))
    return findings
