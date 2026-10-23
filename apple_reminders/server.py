"""Read-only Apple Reminders widget for Companion multi-list snapshots.

Derived from Reminders, Fridge by Kayden D'Mello at revision 89edb0e;
modified by Charm beginning 2026-08-03. AGPL-3.0-or-later.
"""

from __future__ import annotations

import time
from datetime import date, datetime, timedelta, tzinfo
from typing import Any

from flask import current_app

from app.tz_resolve import app_timezone

STALE_SECONDS = 86_400
SOURCE_ID = "reminders"
SOON_DAYS = 3
TODAY_PREFIX = "today:"

_PRESETS: dict[str, dict[str, Any]] = {
    "tasks": {
        "title": None,
        "count_label": "To do",
        "due_style": "friendly",
        "urgency_style": "quiet",
    },
    "food": {
        "title": "FOODIE",
        "count_label": "To eat",
        "due_style": "relative",
        "urgency_style": "color",
    },
    "shopping": {
        "title": None,
        "count_label": "To buy",
        "due_style": "friendly",
        "urgency_style": "quiet",
    },
    "custom": {
        "title": None,
        "count_label": "Items",
        "due_style": "friendly",
        "urgency_style": "quiet",
    },
}


def _records() -> list[dict[str, Any]]:
    store = current_app.config.get("PERSONAL_DATA_STORE")
    if store is None:
        return []
    publications = getattr(store, "publications", None)
    if callable(publications):
        records = publications(SOURCE_ID)
        if isinstance(records, list):
            return [record for record in records if isinstance(record, dict)]
    record = store.get(SOURCE_ID)
    return [record] if isinstance(record, dict) else []


def _newest_record(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not records:
        return None

    def sort_epoch(record: dict[str, Any]) -> float:
        stored = record.get("stored_at")
        if isinstance(stored, (int, float)):
            return float(stored)
        generated = record.get("generated_epoch")
        return float(generated) if isinstance(generated, (int, float)) else 0.0

    return max(records, key=sort_epoch)


def _snapshot_lists(record: dict[str, Any] | None) -> list[dict[str, Any]]:
    if record is None:
        return []
    snapshot = record.get("snapshot")
    if not isinstance(snapshot, dict):
        return []
    data = snapshot.get("data")
    if not isinstance(data, dict):
        return []
    lists = data.get("lists")
    return [entry for entry in lists if isinstance(entry, dict)] if isinstance(lists, list) else []


def _today_id(record: dict[str, Any]) -> str:
    # Published list IDs are UUIDs; this namespace cannot collide with one.
    return TODAY_PREFIX + str(record.get("publisher_id") or "legacy")


def choices(name: str) -> list[dict[str, str]]:
    """Offer ordinary lists and one stable Today view per paired publisher."""
    if name != "lists":
        return []
    records = _records()
    publishers_with_lists = {
        str(record.get("publisher_id") or "legacy") for record in records if _snapshot_lists(record)
    }
    show_publisher = len(publishers_with_lists) > 1
    choices_out: list[dict[str, str]] = []
    for record in records:
        publisher = str(record.get("publisher_name") or "Companion").strip()
        if _snapshot_lists(record):
            title = "Today (all synced lists)"
            choices_out.append(
                {
                    "value": _today_id(record),
                    "label": f"{publisher} · {title}" if show_publisher else title,
                }
            )
        for entry in _snapshot_lists(record):
            list_id = str(entry.get("id") or "").strip()
            title = str(entry.get("title") or "").strip()
            if list_id and title:
                label = f"{publisher} · {title}" if show_publisher else title
                choices_out.append({"value": list_id, "label": label})
    return sorted(choices_out, key=lambda item: (item["label"].casefold(), item["value"]))


def _timestamp_label(generated_epoch: float | None, zone: tzinfo | None = None) -> str:
    if not isinstance(generated_epoch, (int, float)):
        return ""
    return datetime.fromtimestamp(generated_epoch, tz=zone or app_timezone()).strftime(
        "%m-%d %H:%M"
    )


def _due(due_str: Any, today: date, style: str) -> tuple[str, str, int | None]:
    if not isinstance(due_str, str) or not due_str:
        return "", "undated", None
    try:
        due = datetime.strptime(due_str[:10], "%Y-%m-%d").date()
    except ValueError:
        return "", "undated", None
    delta = (due - today).days
    status = (
        "overdue"
        if delta < 0
        else "today"
        if delta == 0
        else "soon"
        if delta <= SOON_DAYS
        else "later"
    )
    if style == "hidden":
        return "", status, delta
    if style == "relative":
        return f"{delta}d", status, delta
    if delta < 0:
        return "Overdue", status, delta
    if delta == 0:
        return "Today", status, delta
    if delta == 1:
        return "Tmrw", status, delta
    if delta < 7:
        return due.strftime("%a"), status, delta
    return due.strftime("%b ") + str(due.day), status, delta


def _int_option(value: Any, default: int = 0) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


def _next_change_at(now: float, zone: tzinfo, generated: Any, expires: Any) -> float:
    local_now = datetime.fromtimestamp(now, tz=zone)
    tomorrow = local_now.date() + timedelta(days=1)
    # Calendar-day arithmetic keeps the boundary correct on 23/25-hour DST days.
    deadlines = [datetime.combine(tomorrow, datetime.min.time(), tzinfo=zone).timestamp()]
    for deadline in (
        generated + STALE_SECONDS if isinstance(generated, (int, float)) else None,
        expires,
    ):
        if isinstance(deadline, (int, float)) and deadline > now:
            deadlines.append(float(deadline))
    return min(deadlines)


def fetch(
    options: dict[str, Any], settings: dict[str, Any], *, ctx: dict[str, Any]
) -> dict[str, Any]:
    del settings, ctx
    preset_name = str(options.get("preset") or "tasks")
    preset = _PRESETS.get(preset_name, _PRESETS["tasks"])
    due_style = str(options.get("due_style") or "preset")
    if due_style == "preset" or due_style not in {"friendly", "relative", "hidden"}:
        due_style = str(preset["due_style"])
    urgency_style = str(options.get("urgency_style") or "preset")
    if urgency_style == "preset" or urgency_style not in {"color", "quiet"}:
        urgency_style = str(preset["urgency_style"])
    columns_option = str(options.get("columns") or "auto")
    if columns_option not in {"auto", "one", "two"}:
        columns_option = "auto"

    records = _records()
    list_id = str(options.get("list_id") or "").strip()
    is_today = list_id.startswith(TODAY_PREFIX)
    selected_record: dict[str, Any] | None = None
    selected: dict[str, Any] | None = None
    for candidate in records:
        if is_today:
            if list_id == _today_id(candidate):
                selected_record = candidate
                break
            continue
        selected = next(
            (
                entry
                for entry in _snapshot_lists(candidate)
                if str(entry.get("id") or "") == list_id
            ),
            None,
        )
        if selected is not None:
            selected_record = candidate
            break
    record = selected_record if is_today else selected_record or _newest_record(records)
    now = time.time()
    zone = app_timezone()
    generated = record.get("generated_epoch") if record else None
    expires = record.get("expires_epoch") if record else None
    state = "empty"
    if record:
        if isinstance(expires, (int, float)) and now >= expires:
            state = "expired"
        elif isinstance(generated, (int, float)) and now >= generated + STALE_SECONDS:
            state = "stale"
        else:
            state = "fresh"

    list_title = str(selected.get("title") or "").strip() if selected else ""
    title = str(options.get("title") or "").strip() or str(
        "Today" if is_today else preset["title"] or list_title or "Reminders"
    )
    count_label = str(options.get("count_label") or "").strip() or str(preset["count_label"])
    accent = str(options.get("accent") or "accent-1")

    base: dict[str, Any] = {
        "title": title,
        "count_label": count_label,
        "accent": accent,
        "due_style": due_style,
        "urgency_colors": urgency_style == "color",
        "items": [],
        "count": 0,
        "shown": 0,
        "state": state,
        "updated_label": _timestamp_label(generated, zone),
        "columns": 1,
        "view": "today" if is_today else "list",
    }
    if is_today and selected_record is None:
        return {**base, "empty": True, "reason": "publisher_missing"}
    if state in {"empty", "expired"}:
        return {**base, "empty": state == "empty", "reason": "no_snapshot"}
    if not list_id:
        return {**base, "empty": True, "reason": "list_required"}
    if not is_today and selected is None:
        return {**base, "empty": True, "reason": "list_missing"}

    base["next_change_at"] = _next_change_at(now, zone, generated, expires)
    source_lists = _snapshot_lists(selected_record) if is_today else [selected]
    raw_items = [
        raw
        for entry in source_lists
        if isinstance(entry, dict) and isinstance(entry.get("items"), list)
        for raw in entry["items"]
    ]
    today = datetime.fromtimestamp(now, tz=zone).date()
    items: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_items):
        if not isinstance(raw, dict) or raw.get("completed") is True:
            continue
        item_title = str(raw.get("title") or "").strip()
        if not item_title:
            continue
        due_label, status, due_delta = _due(raw.get("due_date"), today, due_style)
        if is_today and (due_delta is None or due_delta > 0):
            continue
        items.append(
            {
                "title": item_title,
                "high": raw.get("priority") == "high",
                "due": due_label,
                "due_delta": due_delta,
                "status": status,
                "urgent": status in {"overdue", "today"},
                "source_index": index,
            }
        )
    items.sort(
        key=lambda item: (
            item["due_delta"] is None,
            item["due_delta"] if item["due_delta"] is not None else 0,
            not item["high"],
            item["source_index"],
        )
    )
    count = len(items)
    max_items = _int_option(options.get("max_items"))
    shown_items = items[:max_items] if max_items else items
    columns = (
        2 if columns_option == "two" or (columns_option == "auto" and len(shown_items) > 5) else 1
    )
    return {
        **base,
        "items": shown_items,
        "count": count,
        "shown": len(shown_items),
        "columns": columns,
        "empty": count == 0,
        "reason": ("empty_today" if is_today else "empty_list") if count == 0 else "",
    }
