"""sm-resolver — the source-agnostic corroboration kernel.

A tiny, dependency-free kernel for detecting when independent sources disagree
about the same subject. It is the machinery under cross-registry / cross-method
divergence detection, factored out so any layer can reuse it:

- ``View`` — the contract a claim implements (``comparable() → named fields``).
- ``Resolver[T]`` — a per-source adapter: canonical id → ``(Status, View)``.
- ``diff_views`` — the pure diff: per-source claims → ``Finding`` list
  (``omission`` + one per disagreeing field). It never learns its layer.
- ``Corroborator`` — resolve every source, diff, emit (deduped).

A consumer supplies a view type (its fields are what gets compared) and thin
per-source resolvers; the kernel does the rest, identically across discovery,
identity, capability, or evidence layers. See ``sm-divergence`` for the reference
layers (registries, DID methods) built on this.

Zero runtime dependencies.
"""

from .corroborate import Corroborator, OnFinding
from .diff import diff_views
from .models import OMISSION, Finding
from .resolver import Resolver, Status
from .view import View, ViewT

__version__ = "0.1.0"

__all__ = [
    "OMISSION",
    "Corroborator",
    "Finding",
    "OnFinding",
    "Resolver",
    "Status",
    "View",
    "ViewT",
    "diff_views",
]
