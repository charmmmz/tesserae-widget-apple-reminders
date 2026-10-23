"""Smoke tests for the generic multi-list Reminders snapshot widget.

Derived from Reminders, Fridge by Kayden D'Mello at revision 89edb0e;
modified by Charm beginning 2026-08-03. AGPL-3.0-or-later.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from flask import Flask
from flask.testing import FlaskClient

from plugins.apple_reminders import server as reminders


def _seed(
    app: Flask,
    lists: list[dict[str, Any]],
    *,
    generated_ago: float = 0,
    ttl_h: float = 47,
    publisher_id: str | None = None,
    publisher_name: str | None = None,
) -> float:
    now = time.time()
    generated_epoch = now - generated_ago
    publisher: dict[str, str] = {}
    store = app.config["PERSONAL_DATA_STORE"]
    if callable(getattr(store, "publications", None)):
        publisher["publisher_id"] = publisher_id or "test-publisher"
        publisher["publisher_name"] = publisher_name or "Test iPhone"
    elif publisher_id is not None or publisher_name is not None:
        pytest.skip("host server does not support multiple personal-data publishers")
    store.put(
        "reminders",
        snapshot={"data": {"lists": lists}},
        generated_epoch=generated_epoch,
        expires_epoch=generated_epoch + ttl_h * 3600,
        **publisher,
    )
    return generated_epoch


def _list(list_id: str, title: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    return {"id": list_id, "title": title, "items": items}


def _fetch(app: Flask, options: dict[str, Any] | None = None) -> dict[str, Any]:
    with app.app_context():
        return reminders.fetch(options or {}, {}, ctx={})


def test_manifest_declares_source_wide_changes_and_midnight_refresh() -> None:
    manifest = json.loads((Path(__file__).parents[1] / "plugin.json").read_text())
    assert manifest["updates"]["on_change"] == [
        {
            "source": "personal_data.reminders",
        }
    ]
    assert manifest["updates"]["on_schedule"] == [{"kind": "daily", "suggested_at": "00:00"}]


def test_choices_are_loaded_from_snapshot(app: Flask) -> None:
    _seed(app, [_list("weekend", "Weekend", []), _list("food", "Grocery List", [])])
    with app.app_context():
        assert reminders.choices("lists") == [
            {"value": "food", "label": "Grocery List"},
            {"value": "today:test-publisher", "label": "Today (all synced lists)"},
            {"value": "weekend", "label": "Weekend"},
        ]


def test_multiple_publishers_are_labeled_and_use_selected_freshness(app: Flask) -> None:
    alice_generated = _seed(
        app,
        [_list("alice-food", "Groceries", [{"title": "Milk", "completed": False}])],
        generated_ago=3600,
        publisher_id="alice",
        publisher_name="Alice iPhone",
    )
    _seed(
        app,
        [_list("bob-food", "Groceries", [{"title": "Bread", "completed": False}])],
        generated_ago=60,
        publisher_id="bob",
        publisher_name="Bob iPhone",
    )

    with app.app_context():
        assert reminders.choices("lists") == [
            {"value": "alice-food", "label": "Alice iPhone · Groceries"},
            {"value": "today:alice", "label": "Alice iPhone · Today (all synced lists)"},
            {"value": "bob-food", "label": "Bob iPhone · Groceries"},
            {"value": "today:bob", "label": "Bob iPhone · Today (all synced lists)"},
        ]
        expected_updated = reminders._timestamp_label(alice_generated)

    data = _fetch(app, {"list_id": "alice-food"})

    assert [item["title"] for item in data["items"]] == ["Milk"]
    assert data["updated_label"] == expected_updated


def test_sync_label_is_an_absolute_timestamp() -> None:
    assert reminders._timestamp_label(0, ZoneInfo("Asia/Shanghai")) == "01-01 08:00"


def test_food_preset_uses_foodie_relative_dates_and_two_columns(app: Flask) -> None:
    with app.app_context():
        today = datetime.fromtimestamp(time.time(), tz=reminders.app_timezone()).date()
    items = [
        {
            "title": f"Food {index}",
            "priority": "none",
            "completed": False,
            "due_date": (today + timedelta(days=index - 2)).isoformat(),
        }
        for index in range(6)
    ]
    _seed(app, [_list("food", "Grocery List", items)])

    data = _fetch(app, {"list_id": "food", "preset": "food"})

    assert data["title"] == "FOODIE"
    assert data["count_label"] == "To eat"
    assert data["due_style"] == "relative"
    assert data["urgency_colors"] is True
    assert data["columns"] == 2
    assert [(item["due"], item["status"]) for item in data["items"][:3]] == [
        ("-2d", "overdue"),
        ("-1d", "overdue"),
        ("0d", "today"),
    ]


def test_custom_options_override_preset_and_cap_items(app: Flask) -> None:
    _seed(
        app,
        [
            _list(
                "work",
                "Work",
                [
                    {"title": f"Task {index}", "priority": "none", "completed": False}
                    for index in range(7)
                ],
            )
        ],
    )
    data = _fetch(
        app,
        {
            "list_id": "work",
            "preset": "tasks",
            "title": "TODAY",
            "count_label": "Open",
            "due_style": "hidden",
            "urgency_style": "color",
            "columns": "one",
            "max_items": 3,
        },
    )

    assert data["title"] == "TODAY"
    assert data["count_label"] == "Open"
    assert data["shown"] == 3
    assert data["count"] == 7
    assert data["columns"] == 1


def test_missing_selected_list_is_explicit(app: Flask) -> None:
    _seed(app, [_list("food", "Grocery List", [])])
    data = _fetch(app, {"list_id": "deleted-list"})
    assert data["reason"] == "list_missing"
    assert data["empty"] is True


def test_empty_published_list_set_is_explicitly_unavailable(app: Flask) -> None:
    _seed(app, [])

    with app.app_context():
        assert reminders.choices("lists") == []
    data = _fetch(app, {"list_id": "previously-published"})

    assert data["state"] == "fresh"
    assert data["reason"] == "list_missing"
    assert data["empty"] is True


def test_stale_and_expired_states(app: Flask) -> None:
    lists = [_list("food", "Grocery List", [{"title": "Milk", "completed": False}])]
    _seed(app, lists, generated_ago=30 * 3600, ttl_h=47)
    assert _fetch(app, {"list_id": "food"})["state"] == "stale"
    _seed(app, lists, generated_ago=50 * 3600, ttl_h=47)
    assert _fetch(app, {"list_id": "food"})["state"] == "expired"


def test_expired_tombstone_does_not_require_raw_snapshot(app: Flask) -> None:
    _seed(
        app,
        [_list("food", "Grocery List", [])],
        generated_ago=50 * 3600,
        ttl_h=47,
    )
    record = app.config["PERSONAL_DATA_STORE"].get("reminders")
    assert record is not None
    assert "snapshot" not in record

    data = _fetch(app, {"list_id": "food"})

    assert data["state"] == "expired"
    assert data["items"] == []


def test_renders_from_gallery_sample(client: FlaskClient) -> None:
    response = client.get("/_test/render?plugin=apple_reminders&sample=1&size=md")
    assert response.status_code == 200
    assert 'data-plugin="apple_reminders"' in response.get_data(as_text=True)


def test_today_combines_only_selected_publishers_due_and_overdue_items(
    app: Flask, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = datetime.fromisoformat("2026-10-23T12:00:00+00:00").timestamp()
    monkeypatch.setattr(time, "time", lambda: now)
    app.config["SETTINGS_STORE"].update_section("app", {"timezone": "UTC"})
    alice_generated = _seed(
        app,
        [
            _list(
                "work",
                "Work",
                [
                    {"title": "Today", "due_date": "2026-10-23"},
                    {"title": "Future", "due_date": "2026-10-24"},
                    {"title": "Undated", "due_date": None},
                    {"title": "Invalid", "due_date": "invalid"},
                    {"title": "Completed", "due_date": "2026-10-22", "completed": True},
                ],
            ),
            _list(
                "home",
                "Home",
                [
                    {"title": "Overdue", "due_date": "2026-10-22"},
                    {"title": "High priority", "due_date": "2026-10-23", "priority": "high"},
                ],
            ),
        ],
        generated_ago=3600,
        publisher_id="alice",
    )
    _seed(
        app,
        [_list("bob", "Work", [{"title": "Bob's task", "due_date": "2026-10-23"}])],
        publisher_id="bob",
    )

    data = _fetch(app, {"list_id": "today:alice", "max_items": 2, "due_style": "hidden"})

    assert data["view"] == "today"
    assert data["title"] == "Today"
    assert data["count"] == 3
    assert data["shown"] == 2
    assert [(item["title"], item["status"]) for item in data["items"]] == [
        ("Overdue", "overdue"),
        ("High priority", "today"),
    ]
    assert all(item["due"] == "" for item in data["items"])
    assert data["updated_label"] == reminders._timestamp_label(alice_generated, ZoneInfo("UTC"))


@pytest.mark.parametrize(
    ("zone", "instant", "due_date", "midnight"),
    [
        ("Asia/Shanghai", "2026-10-22T16:00:00+00:00", "2026-10-23", "2026-10-23T16:00:00+00:00"),
        (
            "America/Los_Angeles",
            "2026-10-23T06:59:00+00:00",
            "2026-10-22",
            "2026-10-23T07:00:00+00:00",
        ),
        (
            "America/New_York",
            "2026-03-08T05:00:00+00:00",
            "2026-03-08",
            "2026-03-09T04:00:00+00:00",
        ),
        (
            "America/New_York",
            "2026-11-01T04:00:00+00:00",
            "2026-11-01",
            "2026-11-02T05:00:00+00:00",
        ),
    ],
)
def test_today_and_next_change_follow_configured_timezone_and_dst(
    app: Flask,
    monkeypatch: pytest.MonkeyPatch,
    zone: str,
    instant: str,
    due_date: str,
    midnight: str,
) -> None:
    now = datetime.fromisoformat(instant).timestamp()
    monkeypatch.setattr(time, "time", lambda: now)
    app.config["SETTINGS_STORE"].update_section("app", {"timezone": zone})
    _seed(
        app,
        [_list("work", "Work", [{"title": "Due today", "due_date": due_date}])],
        generated_ago=48 * 3600,
        ttl_h=120,
    )

    data = _fetch(app, {"list_id": "today:test-publisher"})

    assert data["items"][0]["status"] == "today"
    assert data["next_change_at"] == datetime.fromisoformat(midnight).timestamp()
    # The host can consume the hint without interpreting a naive local time.
    from app.widget_next_change import collect

    assert collect({0: data}) == [data["next_change_at"]]


def test_today_rolls_over_without_another_companion_upload(
    app: Flask, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = datetime.fromisoformat("2026-10-23T15:59:59+00:00").timestamp()
    monkeypatch.setattr(time, "time", lambda: now)
    app.config["SETTINGS_STORE"].update_section("app", {"timezone": "Asia/Shanghai"})
    _seed(app, [_list("work", "Work", [{"title": "Tomorrow", "due_date": "2026-10-24"}])], ttl_h=72)
    options = {"list_id": "today:test-publisher"}

    before = _fetch(app, options)
    assert before["reason"] == "empty_today"
    assert before["next_change_at"] == now + 1
    now += 1
    after = _fetch(app, options)
    assert after["count"] == 1
    assert after["items"][0]["status"] == "today"
    now += 86400
    assert _fetch(app, options)["items"][0]["status"] == "overdue"


def test_today_follows_list_replacements_without_switching_publishers(app: Flask) -> None:
    options = {"list_id": "today:alice"}
    _seed(app, [_list("old", "Old", [])], publisher_id="alice")
    assert _fetch(app, options)["reason"] == "empty_today"
    _seed(
        app,
        [_list("new", "New", [{"title": "New task", "due_date": "2000-01-01"}])],
        publisher_id="alice",
    )
    assert _fetch(app, options)["items"][0]["title"] == "New task"
    _seed(app, [], publisher_id="alice")
    assert _fetch(app, options)["reason"] == "empty_today"
    _seed(app, [_list("bob", "Bob", [])], publisher_id="bob")
    app.config["PERSONAL_DATA_STORE"].delete("reminders", publisher_id="alice")
    data = _fetch(app, options)
    assert data["reason"] == "publisher_missing"
    assert data["items"] == []
    assert data["updated_label"] == ""


def test_today_preserves_its_publishers_stale_and_expired_states(app: Flask) -> None:
    lists = [_list("work", "Work", [{"title": "Overdue", "due_date": "2000-01-01"}])]
    _seed(app, lists, generated_ago=30 * 3600, publisher_id="alice")
    _seed(app, lists, publisher_id="bob")
    options = {"list_id": "today:alice"}
    assert _fetch(app, options)["state"] == "stale"
    _seed(app, lists, generated_ago=50 * 3600, publisher_id="alice")
    data = _fetch(app, options)
    assert data["state"] == "expired"
    assert data["items"] == []


def test_today_change_events_match_opted_in_grid_and_canvas_placements(tmp_path: Path) -> None:
    from app.data_change_refresh import (
        matching_page_ids,
        personal_data_delete_event,
        personal_data_update_event,
    )
    from app.plugin_loader import Plugin, PluginRegistry
    from app.scheduled_refresh import scheduled_placements
    from app.state.page_store import Cell, Page
    from app.state.panel_store import CanvasLayout, Element
    from app.state.widget_update_schedule import WidgetUpdateSchedule

    path = Path(__file__).parents[1]
    manifest = json.loads((path / "plugin.json").read_text())
    registry = PluginRegistry(
        plugins={
            "apple_reminders": Plugin(
                id="apple_reminders",
                path=path,
                manifest=manifest,
                data_dir=tmp_path,
            )
        }
    )
    pages = [
        Page(
            id="grid",
            name="Grid",
            cells=[
                Cell(
                    id="today",
                    plugin="apple_reminders",
                    options={"list_id": "today:alice"},
                    update_on_change=True,
                    update_schedule=WidgetUpdateSchedule(),
                    x=0,
                    y=0,
                    w=100,
                    h=100,
                )
            ],
        ),
        Page(
            id="canvas",
            name="Canvas",
            mode="canvas",
            canvas=CanvasLayout(
                w=800,
                h=480,
                els=[
                    Element(
                        id="today",
                        widget="apple_reminders",
                        options={"list_id": "today:alice"},
                        update_on_change=True,
                        update_schedule=WidgetUpdateSchedule(),
                    )
                ],
            ),
        ),
        Page(
            id="off",
            name="Off",
            cells=[
                Cell(
                    id="today",
                    plugin="apple_reminders",
                    options={"list_id": "today:alice"},
                    x=0,
                    y=0,
                    w=100,
                    h=100,
                )
            ],
        ),
    ]
    before = {"data": {"lists": [_list("work", "Work", []), _list("home", "Home", [])]}}
    edited = {
        "data": {
            "lists": [
                _list("work", "Work", []),
                _list(
                    "home",
                    "Home",
                    [
                        {"title": "Task", "due_date": "2026-10-23"},
                    ],
                ),
            ]
        }
    }
    completed = {
        "data": {
            "lists": [
                _list("work", "Work", []),
                _list(
                    "home",
                    "Home",
                    [
                        {"title": "Task", "due_date": "2026-10-23", "completed": True},
                    ],
                ),
            ]
        }
    }
    replaced = {"data": {"lists": [_list("new", "New", [])]}}
    for previous, current in [(before, edited), (edited, completed), (completed, replaced)]:
        event = personal_data_update_event("reminders", previous, current)
        assert event is not None
        assert matching_page_ids(pages, registry, {event.source: event.selectors}) == {
            "grid",
            "canvas",
        }
    event = personal_data_delete_event("reminders", replaced)
    assert matching_page_ids(pages, registry, {event.source: event.selectors}) == {"grid", "canvas"}
    assert {p.page_id for p in scheduled_placements(pages, registry)} == {"grid", "canvas"}
