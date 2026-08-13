"""Tests for the SQLite call log."""

from __future__ import annotations

from pathlib import Path

from kural.telephony import store


def test_init_db_is_idempotent(tmp_path: Path) -> None:
    db_path = str(tmp_path / "calls.db")

    store.init_db(db_path)
    store.init_db(db_path)  # must not raise on a table that already exists

    assert store.list_calls(db_path) == []


def test_record_call_start_and_get(tmp_path: Path) -> None:
    db_path = str(tmp_path / "calls.db")
    store.init_db(db_path)

    store.record_call_start(
        db_path, sid="CA1", direction="inbound", from_number="+1555", to_number="+1666"
    )

    record = store.get_call(db_path, "CA1")

    assert record is not None
    assert record.sid == "CA1"
    assert record.direction == "inbound"
    assert record.from_number == "+1555"
    assert record.to_number == "+1666"
    assert record.status == "in-progress"
    assert record.ended_at is None


def test_record_call_start_custom_status(tmp_path: Path) -> None:
    db_path = str(tmp_path / "calls.db")
    store.init_db(db_path)

    store.record_call_start(
        db_path,
        sid="CA1",
        direction="outbound",
        from_number="+1555",
        to_number="+1666",
        status="dialing",
    )

    assert store.get_call(db_path, "CA1").status == "dialing"  # type: ignore[union-attr]


def test_record_call_end_updates_status_and_timestamp(tmp_path: Path) -> None:
    db_path = str(tmp_path / "calls.db")
    store.init_db(db_path)
    store.record_call_start(
        db_path, sid="CA1", direction="inbound", from_number=None, to_number=None
    )

    store.record_call_end(db_path, "CA1", status="completed")

    record = store.get_call(db_path, "CA1")
    assert record is not None
    assert record.status == "completed"
    assert record.ended_at is not None


def test_get_call_missing_returns_none(tmp_path: Path) -> None:
    db_path = str(tmp_path / "calls.db")
    store.init_db(db_path)

    assert store.get_call(db_path, "nope") is None


def test_list_calls_returns_all_calls(tmp_path: Path) -> None:
    db_path = str(tmp_path / "calls.db")
    store.init_db(db_path)
    store.record_call_start(
        db_path, sid="CA1", direction="inbound", from_number=None, to_number=None
    )
    store.record_call_start(
        db_path, sid="CA2", direction="outbound", from_number=None, to_number=None
    )

    calls = store.list_calls(db_path)

    assert {c.sid for c in calls} == {"CA1", "CA2"}
