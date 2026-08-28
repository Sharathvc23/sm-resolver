"""sm-resolver — the source-agnostic corroboration kernel.

A tiny, dependency-free kernel for detecting when independent sources disagree
about the same subject. It is the machinery under cross-registry / cross-method
divergence detection, factored out so any layer can reuse it:

- ``View`` — the contract a claim implements (``comparable() → named fields``).
- ``Resolver[T]`` — a per-source adapter: canonical id → ``(Status, View)``. A
  resolver MAY also expose a ``vantage`` — an observation context, ``class:value``
  from a controlled vocabulary (SPEC.md §3a).
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

from importlib.metadata import PackageNotFoundError as _PackageNotFoundError
from importlib.metadata import version as _dist_version

from .claim import Claim
from .corroborate import Corroborator, OnFinding
from .diff import Declaration, diff_claims, diff_views
from .models import CONFIRMED, OMISSION, SCOPE_VIOLATION, SOURCE_EQUIVOCATION, SUSPECTED, Finding
from .resolver import (
    OUTCOME_REFUSED,
    OUTCOME_TIMEOUT,
    OUTCOME_UNPARSEABLE,
    OUTCOME_UNREACHABLE,
    OUTCOME_UNVERIFIABLE,
    Resolver,
    Status,
)
from .sweep import SweepResult, Verdict
from .view import View, ViewT

# Derived from installed distribution metadata, never hand-maintained. A literal
# here is a second copy of pyproject's ``version`` with nothing comparing them —
# the shape that shipped sm-provision 0.1.0 reporting "0.0.1" and sm-authority
# 0.1.0 reporting the same wrong value from the same template. Correct today is
# not the test; it drifts at the next bump.
try:  # pragma: no cover - trivial branch, both sides asserted in tests
    __version__ = _dist_version("sm-resolver")
except _PackageNotFoundError:  # running from a source tree, not installed
    __version__ = "0.0.0.dev0"

__all__ = [
    "CONFIRMED",
    "Declaration",
    "OMISSION",
    "OUTCOME_REFUSED",
    "OUTCOME_TIMEOUT",
    "OUTCOME_UNPARSEABLE",
    "OUTCOME_UNREACHABLE",
    "OUTCOME_UNVERIFIABLE",
    "SCOPE_VIOLATION",
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
