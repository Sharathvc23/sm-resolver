"""The pure diff — no I/O, generic over the view type. Given each source's view
of each id, find the disagreements. This is the whole idea; everything else is
plumbing to feed it, and it never learns what layer it is serving.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from .models import OMISSION, Finding
from .view import ViewT


def diff_views(
    views: Mapping[str, Mapping[str, ViewT | None]],
    watch_ids: Iterable[str],
) -> list[Finding]:
    """Compare what every source claims about each watched id.

    ``views[source][agent_id]`` is:
      - a view — the source served a claim;
      - ``None`` — the source POSITIVELY reports the id absent (a 404);
      - simply *missing from the inner mapping* — the source made no claim
        (unreachable). A silent source is never present or absent: a timeout is
        not evidence.

    Findings, per id:
      - ``omission``  — present on ≥1 source AND confirmed-absent on ≥1 other.
      - one per view field (``endpoint``, ``did``, ``key``, …) whose non-``None``
        values disagree across the sources that served it.

    Deterministic and side-effect free; never raises.
    """
    findings: list[Finding] = []
    for aid in sorted(set(watch_ids)):
        present: dict[str, Mapping[str, str | None]] = {}
        confirmed_absent: list[str] = []
        for source, per_source in views.items():
            if aid not in per_source:
                continue  # no claim — unreachable, not an omission
            claim = per_source[aid]
            if claim is None:
                confirmed_absent.append(source)
            else:
                present[source] = claim.comparable()

        if present and confirmed_absent:
            findings.append(
                Finding(
                    OMISSION,
                    aid,
                    {"present_on": sorted(present), "missing_from": sorted(confirmed_absent)},
                )
            )

        field_names: list[str] = []
        for comparable in present.values():
            for name in comparable:
                if name not in field_names:
                    field_names.append(name)

        for name in field_names:
            values: dict[str, str] = {}
            for source, comparable in present.items():
                value = comparable.get(name)
                if value is not None:
                    values[source] = value
            if len(set(values.values())) > 1:
                findings.append(Finding(name, aid, {"field": name, "values": dict(sorted(values.items()))}))

    return findings
