# sm-resolver — the corroboration kernel

**A tiny, dependency-free kernel for detecting when independent sources disagree
about the same subject.** Point it at two or more sources, ask them the same
question, and it reports any disagreement. It is the machinery under
cross-registry / cross-method divergence detection, factored out so any layer can
reuse it.

Four pieces, and only the resolvers know a wire format:

- **`View`** — the contract a claim implements: `comparable() → {field: value}`.
  Those fields are what gets compared; a `None` value never participates.
- **`Resolver[T]`** — a per-source adapter: a canonical id → `(Status, View)`.
  It hides one source's format (an HTTP GET, a DID resolve, a DNS lookup) and
  MUST NOT raise — an unreachable source is `error` (no claim), never a false
  `absent`.
- **`diff_views`** — the pure diff: per-source claims → `Finding` list. It emits
  `omission` (present on one source, positively absent on another) and one
  finding per view field whose values disagree. It never learns its layer.
- **`Corroborator`** — resolve every source, diff, and emit new findings once
  (deduped). Fewer than two sources → no-op.

## Install

```bash
pip install sm-resolver        # zero runtime dependencies
```

## Use

Supply a view (its fields are what you compare) and a thin resolver per source:

```python
import asyncio
from collections.abc import Mapping
from dataclasses import dataclass
from sm_resolver import Corroborator, Status

@dataclass(frozen=True)
class RecordView:                       # your layer's view
    endpoint: str | None = None
    def comparable(self) -> Mapping[str, str | None]:
        return {"endpoint": self.endpoint}

class MyResolver:                       # your thin per-source adapter
    def __init__(self, label): self.label = label
    async def resolve(self, agent_id) -> tuple[Status, RecordView | None]:
        ...                             # query this source; normalize to RecordView

findings = asyncio.run(
    Corroborator([MyResolver("a"), MyResolver("b")]).check(["agent-1"])
)
for f in findings:
    print(f.kind, f.agent_id, f.detail)
    # endpoint agent-1 {'field': 'endpoint', 'values': {'a': 'https://real', 'b': 'https://evil'}}
```

Long-running? Pass `on_finding=` — it fires once per distinct finding across the
corroborator's lifetime.

## Who uses it

[`sm-divergence`](https://github.com/Sharathvc23/sm-divergence) builds the
reference layers on this kernel: a **discovery** layer (registries — NEST, the
NANDA Index) and an **identity** layer (DID methods — `did:key`, `did:web`,
Universal Resolver), each supplying its own view and thin resolvers. Capability
and evidence layers are the same shape.

## Design rules

- **A timeout is not a claim.** An unreachable or erroring source is excluded,
  never counted as an omission.
- **Only present, comparable values disagree.** A `None` field contributes
  nothing — an unverifiable value is not a disagreement.
- **The diff stays pure and generic** — deterministic, no I/O, never raises,
  never learns its layer. All I/O lives in the resolvers.

## Develop

```bash
make ci-local   # uv: sync → ruff → format → mypy --strict → pytest
```

## License

[MIT](LICENSE)

---

*First published: 2026-07-04 | Last modified: 2026-07-04*

*Personal research contributions aligned with [Project NANDA](https://projectnanda.org) standards. [Stellarminds.ai](https://stellarminds.ai)*
