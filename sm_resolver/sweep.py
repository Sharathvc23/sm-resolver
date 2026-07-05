"""The sweep result — the corroboration outcome for one subject in one sweep.

Plain, unsigned data: the verdict, the claims (including ``error`` claims,
preserved for audit), and the findings. A consumer that needs a signed,
content-addressed Corroboration Record seals this (digest + signature) in a
layer with crypto; the kernel stays dependency-free.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, Literal

from .claim import Claim
from .models import Finding
from .view import ViewT

# AGREE     — two or more decisive (present/absent) claims, no findings.
# DIVERGENT — one or more findings.
# INSUFFICIENT — fewer than two decisive claims; nothing to corroborate.
Verdict = Literal["AGREE", "DIVERGENT", "INSUFFICIENT"]


@dataclass(frozen=True)
class SweepResult(Generic[ViewT]):
    """The result of corroborating one agent in one sweep."""

    agent_id: str
    verdict: Verdict
    observed_at: float
    staleness_window_s: float
    claims: list[Claim[ViewT]] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
