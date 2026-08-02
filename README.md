# Reminders, Fridge widget for Tesserae

A fridge grocery list from your iPhone. The Tesserae Companion app publishes one
chosen Apple Reminders list (incomplete items only) to your server as a minimal,
expiring snapshot; this widget renders it as a framed checklist with the item
count as the hero.

Drop into [Tesserae](https://github.com/dmellok/tesserae) via Settings → Widgets
→ Browse community widgets.

## Folders shipped

- `reminders_fridge`

## What you see

- A bold **count block** (items left to buy) as the hero, in your chosen accent.
- The list **title** and a freshness badge (Fresh / Stale, with a relative
  "2h ago", or Expired).
- A **checkbox row** per item: high-priority items get a filled box, and each
  item shows a compact due tag (Today / Tmrw / a weekday / a date), with
  due-today and overdue tags picked out in the accent.
- Calm empty, stale (dimmed), and expired states when there is no live snapshot.
- On the Panels canvas, a `value` fragment renders just the count.

The layout adapts down to small cells: on tight cells the due tags and the "To
buy" label drop so the count and item names hold.

## Configuration

Per-cell options:

- `title` — list title (blank shows "Fridge")
- `max_items` — cap the rows shown; the count still reflects the full list
  (0 = show all)
- `accent` — Terracotta / Ochre / Teal / Slate blue / Plum

## How the data gets there

This widget is read-only. The **Companion app** owns the data: it publishes the
selected Apple Reminders list to your Tesserae server's personal-data bridge as
an expiring snapshot, and the widget reads the latest one. Nothing leaves the
phone except the selected list, and the snapshot is deleted when you turn the
source off or it expires.

Needs the Companion app paired, with the personal-data source enabled. No admin
page and no network access of its own: the data's authority is the phone.

## License

AGPL-3.0-or-later, matching Tesserae.
