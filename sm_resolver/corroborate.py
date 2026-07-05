"""Generic orchestration: resolve every watched id against every source, diff,
and hand new findings to a callback. Layer-agnostic — a thin adapter for any
source set (e.g. two NANDA Indexes, or a NEST + an Index) drives this directly
with its own ``Resolver`` instances; no discovery internals required.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Generic

from .diff import diff_views
from .models import Finding
from .resolver import Resolver
from .view import ViewT

OnFinding = Callable[[Finding], None]


class Corroborator(Generic[ViewT]):
    """Corroborate a set of sources for a watch set.

    Give it two or more ``Resolver`` instances; each ``check`` asks all of them
    the same by-id questions and reports any disagreement. Fewer than two
    sources → nothing to corroborate → no-op. Sources are deduped by ``label``.

    ``on_finding`` fires once per distinct finding across the corroborator's
    lifetime (deduped by fingerprint); ``check`` always returns ALL current
    findings. Never raises.
    """

    def __init__(self, resolvers: Iterable[Resolver[ViewT]], *, on_finding: OnFinding | None = None) -> None:
        deduped: list[Resolver[ViewT]] = []
        seen: set[str] = set()
        for r in resolvers:
            if r.label in seen:
                continue
            seen.add(r.label)
            deduped.append(r)
        self.resolvers = deduped
        self.on_finding = on_finding
        self._emitted: set[str] = set()

    @property
    def labels(self) -> list[str]:
        return [r.label for r in self.resolvers]

    async def check(self, watch_ids: Iterable[str]) -> list[Finding]:
        ids = sorted(set(watch_ids))
        if len(self.resolvers) < 2 or not ids:
            return []

        views: dict[str, dict[str, ViewT | None]] = {}
        for resolver in self.resolvers:
            per_source: dict[str, ViewT | None] = {}
            for aid in ids:
                try:
                    status, view = await resolver.resolve(aid)
                except Exception:
                    status, view = "error", None
                if status == "error":
                    continue  # unreachable is not a claim
                per_source[aid] = view
            views[resolver.label] = per_source

        findings = diff_views(views, ids)
        if self.on_finding is not None:
            for f in findings:
                fp = f.fingerprint()
                if fp in self._emitted:
                    continue
                self._emitted.add(fp)
                try:
                    self.on_finding(f)
                except Exception:
                    pass
        return findings
