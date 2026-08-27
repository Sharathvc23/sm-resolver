"""The pure diff — no I/O, generic over the view type. Given the claims of one
sweep for one agent, find the disagreements. It never learns what layer it serves.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from .claim import Claim
from .models import OMISSION, SOURCE_EQUIVOCATION, Finding
from .resolver import Status
from .view import ViewT


@dataclass(frozen=True)
class Declaration:
    """One source's already-verified declaration that one field varies along one
    vantage class, at a given version.

    The kernel neither fetches nor verifies declarations — it has no crypto and
    no I/O. A layer above supplies these as inert data, exactly as it supplies
    the ``present``/``absent`` classification the kernel already trusts.
    """

    vantage_class: str
    version: str


def _vantage_class(vantage: str | None) -> str | None:
    """The class half of a ``class:value`` vantage (SPEC.md §3a.1), or None for
    ``null`` and for anything not of that form."""
    if vantage is None:
        return None
    head, sep, _ = vantage.partition(":")
    return head if sep else None


def diff_claims(
    agent_id: str,
    claims: Iterable[Claim[ViewT]],
    *,
    declared: Mapping[tuple[str, str], Declaration] | None = None,
) -> list[Finding]:
    """Diff the claims of one sweep for one agent.

    Findings carry ``confirmation = suspected``; the caller (Corroborator)
    upgrades to ``confirmed`` per observation time. Emitted:

      - ``omission``  — present on ≥1 source AND positively absent on ≥1 other.
      - ``source_equivocation`` — one source's vantages disagree on a field's
        non-``None`` value; that source then contributes no agreed value to the
        cross-source comparison for that field.
      - one per view field (``endpoint``, ``did``, ``key``, …) whose per-source
        agreed non-``None`` values disagree across sources.

    ``declared`` maps ``(source, field)`` to an already-verified ``Declaration``.
    Where one applies — the source's vantages for that field are all on the
    declared class — two things change, and only two:

      - its ``source_equivocation`` finding is **annotated** ``declared=True``
        with the declaration's version. It is still emitted, and the verdict is
        still ``DIVERGENT`` (SPEC.md §4b: annotate, never withdraw).
      - the source is **not excluded** from cross-source comparison. Instead its
        per-vantage values are compared against other sources' values *for the
        same vantage*.

    That second part is the whole point, and the reason a naive implementation is
    dangerous. Suppressing the finding while leaving the exclusion in place lets a
    source that declares variation serve one vantage an attacker's value and be
    reported as ``AGREE``, because nothing is left to compare it against. **A
    declaration redirects comparison into a cohort; it never removes comparison.**

    With ``declared`` unset — or where no declaration applies — every source
    contributes at most one value, so a single cohort covers everything and the
    result is identical to the undeclared diff.

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

    declarations = declared or {}

    by_source: dict[str, list[Claim[ViewT]]] = {}
    for c in present:
        by_source.setdefault(c.source, []).append(c)

    def per_vantage_values(source: str, name: str) -> dict[str | None, str]:
        out: dict[str | None, str] = {}
        for c in by_source[source]:
            assert c.view is not None
            value = c.view.comparable().get(name)
            if value is not None:
                out[c.vantage] = value
        return out

    # source_equivocation: a source whose vantages disagree on a field's value.
    # A source with an applicable declaration is annotated rather than excluded.
    equivocating: set[tuple[str, str]] = set()
    varying: dict[tuple[str, str], dict[str | None, str]] = {}
    for name in field_names:
        for source in sorted(by_source):
            per_vantage = per_vantage_values(source, name)
            if len(set(per_vantage.values())) <= 1:
                continue
            decl = declarations.get((source, name))
            applies = decl is not None and all(_vantage_class(v) == decl.vantage_class for v in per_vantage)
            if applies:
                assert decl is not None
                varying[(source, name)] = per_vantage
            else:
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
                    declared=applies,
                    declaration_version=decl.version if applies and decl is not None else None,
                )
            )

    # cross-source field divergence, per cohort. A source with one agreed value
    # joins every cohort; a declared-varying source contributes per vantage. With
    # no declared-varying source there is exactly one cohort, which is the
    # undeclared comparison unchanged.
    for name in field_names:
        agreed: dict[str, str] = {}
        for source in sorted(by_source):
            if (source, name) in equivocating or (source, name) in varying:
                continue
            values = set(per_vantage_values(source, name).values())
            if len(values) == 1:
                agreed[source] = next(iter(values))

        cohorts: list[str | None] = []
        for (_, field), per_vantage in varying.items():
            if field != name:
                continue
            for vantage in per_vantage:
                if vantage not in cohorts:
                    cohorts.append(vantage)
        cohorts.sort(key=str)

        # With no declared-varying source for this field, `cohorts` is empty and
        # the single `None` cohort IS the undeclared comparison — which is how
        # back-compat is obtained, structurally rather than by special-casing.
        for cohort in cohorts or [None]:
            values_here = dict(agreed)
            for (source, field), per_vantage in varying.items():
                if field == name and cohort in per_vantage:
                    values_here[source] = per_vantage[cohort]
            if len(set(values_here.values())) > 1:
                findings.append(Finding(name, agent_id, {"field": name, "values": dict(sorted(values_here.items()))}))

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
