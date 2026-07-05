"""sm-resolver — the source-agnostic corroboration kernel.

A tiny, dependency-free kernel for detecting when independent sources disagree
about the same subject. It is the machinery under cross-registry / cross-method
divergence detection, factored out so any layer can reuse it:

- ``View`` — the contract a claim implements (``comparable() → named fields``).
- ``Resolver[T]`` — a per-source adapter: canonical id → ``(Status, View)``. A
  resolver MAY also expose a ``vantage`` (a network perspective).
- ``Claim`` — one source's answer from one vantage at one instant.
- ``diff_claims`` — the pure diff: claims → ``Finding`` list (``omission``,
  ``source_equivocation``, and per-field divergence). It never learns its layer.
- ``Corroborator`` — resolve every (source, vantage), diff, apply confirmation
  (``suspected`` / ``confirmed``), and return a ``SweepResult`` per subject with
  a verdict (``AGREE`` / ``DIVERGENT`` / ``INSUFFICIENT``).

A consumer supplies a view type and thin per-source resolvers; the kernel does
the rest, identically across discovery, identity, capability, or evidence layers.
See ``sm-divergence`` for the reference layers built on this.

Zero runtime dependencies.
"""

from .claim import Claim
from .corroborate import Corroborator, OnFinding
from .diff import diff_claims, diff_views
from .models import CONFIRMED, OMISSION, SOURCE_EQUIVOCATION, SUSPECTED, Finding
from .resolver import Resolver, Status
from .sweep import SweepResult, Verdict
from .view import View, ViewT

__version__ = "0.2.0"

__all__ = [
    "CONFIRMED",
    "OMISSION",
    "SOURCE_EQUIVOCATION",
    "SUSPECTED",
    "Claim",
    "Corroborator",
    "Finding",
    "OnFinding",
    "Resolver",
    "Status",
    "SweepResult",
    "Verdict",
    "View",
    "ViewT",
    "diff_claims",
    "diff_views",
]
