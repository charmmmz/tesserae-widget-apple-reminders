"""Smoke tests for the generic multi-list Reminders snapshot widget.

Derived from Reminders, Fridge by Kayden D'Mello at revision 89edb0e;
modified by Charm beginning 2026-08-03. AGPL-3.0-or-later.
"""

from __future__ import annotations

import json
import time
from datetime import date, timedelta
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


def test_manifest_declares_list_scoped_change_updates() -> None:
    manifest = json.loads((Path(__file__).parents[1] / "plugin.json").read_text())
    assert manifest["updates"]["on_change"] == [
        {
            "source": "personal_data.reminders",
            "selector_option": "list_id",
        }
    ]
    assert manifest["updates"]["on_schedule"] == [
        {"kind": "daily", "suggested_at": "07:00"}
    ]


def test_choices_are_loaded_from_snapshot(app: Flask) -> None:
    _seed(app, [_list("weekend", "Weekend", []), _list("food", "Grocery List", [])])
    with app.app_context():
        assert reminders.choices("lists") == [
            {"value": "food", "label": "Grocery List"},
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
            {"value": "bob-food", "label": "Bob iPhone · Groceries"},
        ]
        expected_updated = reminders._timestamp_label(alice_generated)

    data = _fetch(app, {"list_id": "alice-food"})

    assert [item["title"] for item in data["items"]] == ["Milk"]
    assert data["updated_label"] == expected_updated


def test_sync_label_is_an_absolute_timestamp() -> None:
    assert reminders._timestamp_label(0, ZoneInfo("Asia/Shanghai")) == "01-01 08:00"


def test_food_preset_uses_foodie_relative_dates_and_two_columns(app: Flask) -> None:
    today = date.today()
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
