# Apple Reminders widget for Tesserae

A general Apple Reminders widget backed by Tesserae Companion's private,
expiring multi-list snapshot. Choose any list the iPhone has explicitly
published, then present it as Tasks, Food, Shopping, or a custom checklist.

This repository is derived from Kayden D'Mello's
[Reminders, Fridge](https://github.com/dmellok/tesserae-widget-reminders-fridge)
widget and keeps its framed, count-first visual language. The original Git
history is retained; see `NOTICE` for the exact attribution, source revision,
and modification date.

This is a separate widget rather than an in-place upgrade. It reads only the
generic `reminders` source, does not fall back to `reminders.fridge`, and does
not migrate existing Reminders, Fridge cells. The published fridge widget can
remain installed for servers that still carry the deprecated one-list source.

## Folder shipped

- `apple_reminders`

## Presentation presets

- **Tasks** — list title, “To do”, friendly due labels, quiet urgency.
- **Food** — `FOODIE`, “To eat”, relative dates such as `-2d`, `0d`, and `3d`,
  urgency colors, and automatic two-column layout after five visible items.
- **Shopping** — list title, “To buy”, friendly due labels.
- **Custom** — neutral defaults intended for title, label, date, urgency, and
  layout overrides.

All presets sort dated items first, then undated items. High-priority items use
a filled checkbox. Fresh, stale, expired, missing-snapshot, and missing-list
states are distinct, so a deleted or unshared list never silently changes to a
different one.

## Configuration

Per-cell options include:

- uploaded Reminders list;
- presentation preset;
- custom title and count label;
- maximum visible items;
- friendly, relative, or hidden due dates;
- color-coded or quiet urgency marks;
- automatic, one-column, or two-column layout;
- Tesserae accent color.

The dynamic list picker is populated from every paired Companion's latest
`reminders` snapshot. With more than one publisher, choices include the paired
client name (for example, `Alice iPhone · Groceries`) so household lists remain
distinguishable. If the picker is empty, the enabled source may currently
publish no lists. The widget keeps its configured list instead of silently
falling back and shows the selected-list-unavailable state until that list is
published again or another one is explicitly chosen.

On compatible servers, each placement can independently enable **Refresh when
this widget's data changes**. The dependency is narrowed to that placement's
selected list, so changing Grocery List does not refresh a dashboard showing a
different Reminders list, and the same widget on another dashboard remains off
unless explicitly enabled there too.

## Privacy and data flow

The widget is read-only and has no network access. The iPhone remains the data
authority and uploads only incomplete items from lists the user selected. Each
list uses an app-generated publication UUID rather than its EventKit calendar
identifier. The server derives an opaque publisher identity from each
authenticated pairing; the snapshot does not expose a new user identity field.
Tesserae retains only the latest raw snapshot per paired publisher until its
required expiry or that publisher explicitly deletes it; ordinary rendered
History thumbnails follow the server's existing render-cache lifetime.

Requires a Tesserae Server advertising `reminders` in
`personal_data.sources` and a paired Tesserae Companion build that can publish
it. The legacy `personal_data_reminders` feature flag alone is not sufficient.

## License

AGPL-3.0-or-later, matching Tesserae and the original widget.
