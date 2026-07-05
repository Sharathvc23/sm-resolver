"""Orchestration: resolve every watched agent against every (source, vantage),
diff, apply confirmation, and produce a SweepResult per subject. Layer-agnostic —
a thin adapter for any source set drives this with its own ``Resolver`` instances.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from dataclasses import replace
from typing import Generic

from .claim import Claim
from .diff import diff_claims
from .models import CONFIRMED, SUSPECTED, Finding
from .resolver import Resolver
from .sweep import SweepResult, Verdict
from .view import ViewT

OnFinding = Callable[[Finding], None]


class Corroborator(Generic[ViewT]):
    """Corroborate a set of sources for a watch set.

    Give it two or more ``Resolver`` instances; each ``check`` resolves every
    watched agent against each and returns a ``SweepResult`` per subject. A
    resolver MAY expose a ``vantage`` (a network perspective) — resolvers are
    deduped by ``(label, vantage)``, and multiple vantages of one source enable
    ``source_equivocation`` detection.

    Findings are stamped with ``confirmation``: a disagreement is ``suspected``
    when first seen and ``confirmed`` once re-observed in a sweep whose
    ``observed_at`` exceeds the first observation by at least
    ``staleness_window_s``. ``on_finding`` fires once per distinct finding
    (deduped by fingerprint).
    """

    def __init__(
        self,
        resolvers: Iterable[Resolver[ViewT]],
        *,
        on_finding: OnFinding | None = None,
        staleness_window_s: float = 0.0,
    ) -> None:
        deduped: list[Resolver[ViewT]] = []
        seen: set[tuple[str, str | None]] = set()
        for r in resolvers:
            key = (r.label, getattr(r, "vantage", None))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(r)
        self.resolvers = deduped
        self.on_finding = on_finding
        self.staleness_window_s = staleness_window_s
        self._first_seen: dict[str, float] = {}
        self._emitted: set[str] = set()

    @property
    def labels(self) -> list[str]:
        return [r.label for r in self.resolvers]

    async def check(self, watch_ids: Iterable[str], *, observed_at: float | None = None) -> list[SweepResult[ViewT]]:
        """Resolve, diff, confirm, and return one SweepResult per subject.
        ``observed_at`` (epoch seconds) stamps this sweep's claims; defaults to
        wall-clock. Never raises."""
        ts = float(observed_at if observed_at is not None else time.time())
        results: list[SweepResult[ViewT]] = []

        for aid in sorted(set(watch_ids)):
            claims: list[Claim[ViewT]] = []
            for resolver in self.resolvers:
                try:
                    status, view = await resolver.resolve(aid)
                except Exception:
                    status, view = "error", None
                claims.append(Claim(resolver.label, getattr(resolver, "vantage", None), status, view, ts, status))

            findings = [self._confirm(f, ts) for f in diff_claims(aid, claims)]

            for f in findings:
                fp = f.fingerprint()
                if self.on_finding is not None and fp not in self._emitted:
                    self._emitted.add(fp)
                    try:
                        self.on_finding(f)
                    except Exception:
                        pass

            decisive = sum(1 for c in claims if c.status in ("present", "absent"))
            verdict: Verdict = "INSUFFICIENT" if decisive < 2 else ("DIVERGENT" if findings else "AGREE")
            results.append(SweepResult(aid, verdict, ts, self.staleness_window_s, claims, findings))

        return results

    def _confirm(self, finding: Finding, observed_at: float) -> Finding:
        fp = finding.fingerprint()
        first = self._first_seen.get(fp)
        if first is None:
            self._first_seen[fp] = observed_at
            return replace(finding, confirmation=SUSPECTED)
        if observed_at > first and observed_at - first >= self.staleness_window_s:
            return replace(finding, confirmation=CONFIRMED)
        return replace(finding, confirmation=SUSPECTED)
