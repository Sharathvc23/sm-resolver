"""The Resolver protocol — one registry/source, one way of being asked.

Sources do not share a wire format: a NEST server answers ``GET /api/agents/{id}``;
a NANDA Index answers a two-hop resolve; a DID method resolves a document; a
DNS-AID zone answers a TXT lookup. A ``Resolver`` hides that difference: given a
canonical agent id it performs *that* source's query, applies *that* source's
native verification, and normalizes the answer to ``(Status, View)`` — so the
diff downstream is untouched by format heterogeneity. This is the seam a thin
per-source adapter (e.g. a NANDA Index adapter) implements.
"""

from __future__ import annotations

from typing import Literal, Protocol, TypeVar

from .view import View

# One source's claim about one id: served / positively-absent / no-claim.
Status = Literal["present", "absent", "error"]

# Why a resolve ended as it did. `status` says whether the source made a claim;
# `outcome` says how that came about, which matters most for `error` — a timeout,
# a persistently unreachable host, an explicit refusal and an unreadable body are
# different signals about a source, and the diff excludes all of them equally.
#
# Bare names are reserved for values seeded here. A deployment introducing its own
# MUST namespace it with a reverse-DNS or URI prefix, as finding kinds do, so two
# implementations do not mint incomparable strings for the same condition.
OUTCOME_TIMEOUT = "timeout"  # no answer within the deadline
OUTCOME_UNREACHABLE = "unreachable"  # transport failed
OUTCOME_REFUSED = "refused"  # the source declined to answer
OUTCOME_UNPARSEABLE = "unparseable"  # answered, body could not be read
OUTCOME_UNVERIFIABLE = "unverifiable"  # answered, the source's own verification failed

# Covariant: a Resolver only ever PRODUCES its view type, so Resolver[Sub] is
# usable where Resolver[Base] is expected.
T_co = TypeVar("T_co", bound=View, covariant=True)


class Resolver(Protocol[T_co]):
    """Resolves a canonical agent id to one source's normalized claim.

    ``label`` names the source in findings. ``resolve`` MUST NOT raise — an
    unreachable or unparseable source is the ``"error"`` claim (no claim),
    never a false ``"absent"``.

    ``resolve`` MAY return a third element, an outcome string saying *why* the
    resolve ended as it did (see the ``OUTCOME_*`` values above). Only the
    resolver knows; the kernel cannot infer it. Omitting it is supported and
    keeps the status as the outcome, which is the least specific honest answer.
    """

    @property
    def label(self) -> str: ...

    async def resolve(self, agent_id: str) -> tuple[Status, T_co | None] | tuple[Status, T_co | None, str]: ...
