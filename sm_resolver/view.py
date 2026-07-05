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
from typing import Protocol, TypeVar


class View(Protocol):
    """A claim reduced to named, comparable string fields."""

    def comparable(self) -> Mapping[str, str | None]: ...


ViewT = TypeVar("ViewT", bound=View)
