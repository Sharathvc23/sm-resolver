"""The comparable-view contract — the one thing a layer must provide.

A view is any object that reduces itself to a set of named string fields via
``comparable()``. Those fields ARE what corroboration compares: each field whose
value differs across sources becomes a divergence finding named for that field;
a field value of ``None`` never participates (an unverifiable value is not a
disagreement). Omission (present vs confirmed-absent) is universal and needs no
field.

This is the whole contract an adapter author implements — return a view type
from a ``Resolver``, give it a ``comparable()``, and the generic diff does the
rest, identically across discovery, identity, capability, and evidence layers.
The discovery layer's ``RecordView`` is just the first implementation.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, TypeVar


@dataclass(frozen=True)
class Binding:
    """The renewable-lease position of one claim (SPEC.md §3b).

    A registry that issues subject-to-target bindings as leases stamps each with
    a ``sequence`` that increases within an authority ``scope`` whenever the
    target, publisher, or authority evidence changes. Two sources serving the
    same subject at different sequences are not disagreeing about the subject;
    one is behind. The diff uses this to attribute a superseded claim as
    ``stale_binding`` rather than as a field divergence against the current one.

    ``scope`` names the sequence space — typically the authority issuer. Sequences
    are comparable only within one scope; ``None`` is the single default scope
    for a layer whose sources share one. ``sequence`` is a non-negative integer.
    """

    sequence: int
    scope: str | None = None


class View(Protocol):
    """A claim reduced to named, comparable string fields.

    A view MAY additionally expose ``binding() -> Binding | None``. The kernel
    reads it by duck-typing, exactly as it reads a resolver's optional
    ``vantage``; a view without it, or returning ``None``, behaves as before.
    """

    def comparable(self) -> Mapping[str, str | None]: ...


ViewT = TypeVar("ViewT", bound=View)
