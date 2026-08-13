"""Tests for the in-memory active-call registry."""

from __future__ import annotations

from unittest.mock import MagicMock

from kural.telephony.registry import CallHandle, CallRegistry


def test_add_and_get() -> None:
    registry = CallRegistry()
    handle = CallHandle(sid="CA1", direction="inbound", worker=MagicMock())

    registry.add(handle)

    assert registry.get("CA1") is handle


def test_get_missing_returns_none() -> None:
    assert CallRegistry().get("nope") is None


def test_remove() -> None:
    registry = CallRegistry()
    registry.add(CallHandle(sid="CA1", direction="inbound", worker=MagicMock()))

    registry.remove("CA1")

    assert registry.get("CA1") is None


def test_remove_missing_is_noop() -> None:
    CallRegistry().remove("nope")  # must not raise


def test_concurrent_calls_are_isolated() -> None:
    registry = CallRegistry()
    inbound = CallHandle(sid="CA1", direction="inbound", worker=MagicMock())
    outbound = CallHandle(sid="CA2", direction="outbound", worker=MagicMock())

    registry.add(inbound)
    registry.add(outbound)

    assert len(registry) == 2
    assert registry.get("CA1") is inbound
    assert registry.get("CA2") is outbound

    registry.remove("CA1")

    assert len(registry) == 1
    assert registry.get("CA1") is None
    assert registry.get("CA2") is outbound


def test_list_active() -> None:
    registry = CallRegistry()
    handle = CallHandle(sid="CA1", direction="inbound", worker=MagicMock())

    registry.add(handle)

    assert registry.list_active() == [handle]
