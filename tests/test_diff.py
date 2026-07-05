"""The pure diff — generic over the view type, no I/O."""

from __future__ import annotations

from _helpers import StubView

from sm_resolver import diff_views
from sm_resolver.view import ViewT  # noqa: F401 - re-export presence check

A = "src-a"
B = "src-b"


def test_agreement_yields_nothing() -> None:
    views = {A: {"x": StubView(endpoint="https://x")}, B: {"x": StubView(endpoint="https://x")}}
    assert diff_views(views, ["x"]) == []


def test_field_divergence_named_after_the_field() -> None:
    views = {A: {"x": StubView(endpoint="https://real")}, B: {"x": StubView(endpoint="https://evil")}}
    findings = diff_views(views, ["x"])
    assert [f.kind for f in findings] == ["endpoint"]
    assert findings[0].detail == {"field": "endpoint", "values": {A: "https://real", B: "https://evil"}}


def test_multiple_fields_diverge_independently() -> None:
    views = {
        A: {"x": StubView(endpoint="https://a", key="z6MkA")},
        B: {"x": StubView(endpoint="https://b", key="z6MkB")},
    }
    assert sorted(f.kind for f in diff_views(views, ["x"])) == ["endpoint", "key"]


def test_omission() -> None:
    views: dict[str, dict[str, StubView | None]] = {A: {"x": StubView(endpoint="https://x")}, B: {"x": None}}
    findings = diff_views(views, ["x"])
    assert [f.kind for f in findings] == ["omission"]
    assert findings[0].detail == {"present_on": [A], "missing_from": [B]}


def test_unreachable_is_not_omission() -> None:
    views: dict[str, dict[str, StubView | None]] = {A: {"x": StubView(endpoint="https://x")}, B: {}}
    assert diff_views(views, ["x"]) == []


def test_none_field_never_participates() -> None:
    views = {A: {"x": StubView(endpoint="https://x", key="z6MkA")}, B: {"x": StubView(endpoint="https://x", key=None)}}
    assert diff_views(views, ["x"]) == []


def test_ids_outside_watch_set_ignored() -> None:
    views: dict[str, dict[str, StubView | None]] = {A: {"y": StubView(endpoint="https://y")}, B: {"y": None}}
    assert diff_views(views, ["x"]) == []


def test_omission_and_field_divergence_together() -> None:
    views: dict[str, dict[str, StubView | None]] = {
        A: {"x": StubView(endpoint="https://a")},
        B: {"x": StubView(endpoint="https://b")},
        "src-c": {"x": None},
    }
    assert sorted(f.kind for f in diff_views(views, ["x"])) == ["endpoint", "omission"]
