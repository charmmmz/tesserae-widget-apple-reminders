# Apple Reminders widget for Tesserae

A general Apple Reminders widget backed by Tesserae Companion's private,
expiring multi-list snapshot. Choose any list the iPhone has explicitly
published, or choose **Today (all synced lists)** for one Companion's due-today
and overdue tasks. Present either view as Tasks, Food, Shopping, or a custom
checklist.

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

- uploaded Reminders list or a Companion's Today view;
- presentation preset;
- custom title and count label;
- maximum visible items;
- friendly, relative, or hidden due dates;
- optional placement-level daily refreshes on compatible Tesserae servers, so
  relative day labels can advance without requiring a new Companion snapshot;
- color-coded or quiet urgency marks;
- automatic, one-column, or two-column layout;
- Tesserae accent color.

The dynamic list picker is populated from every paired Companion's latest
`reminders` snapshot. With more than one publisher, choices include the paired
client name (for example, `Alice iPhone · Groceries`) so household lists remain
distinguishable. Each publisher with synced lists also has a **Today (all
synced lists)** choice. If the picker is empty, the enabled source may currently
publish no lists. The widget keeps its configured list instead of silently
falling back and shows the selected-list-unavailable state until that list is
published again or another one is explicitly chosen.

### Today

Select **Today (all synced lists)** in **Reminders list / view**. With several
paired phones, choose the entry bearing the intended phone's name. Today
combines only that publisher's synced lists and includes incomplete items
whose valid due date is today or earlier; future, undated, invalid-date, and
completed items are excluded. The count and item limit apply after filtering.
Renaming or removing an individual list does not change the selected publisher.
If that publisher's synced source is deleted, the widget reports it as
unavailable instead of switching to another phone. A snapshot that explicitly
publishes no lists produces an empty Today view.

Today and all due labels use **Settings → App → Timezone**, including when the
host/container runs in UTC. Date-only snapshot values are interpreted as
calendar dates in that zone. They are not shifted through UTC. The snapshot
does not carry the phone's timezone or exact due times, so use the intended
timezone in Tesserae when comparing with the iPhone's Today view.

On compatible servers, enable these host-owned options for the placement:

- **Refresh when this widget's data changes** to refresh after Companion
  publishes changes. The dependency covers the entire `personal_data.reminders`
  source so edits, completions, newly synced lists, and removed lists all reach
  Today. This also means an ordinary-list placement with the option enabled
  can refresh for changes to another list or publisher: the current host
  contract cannot express a publisher's dynamic set of list dependencies.
- **Daily refresh** with the default local day boundary to update at midnight
  without another Companion upload. If selecting a custom time, use `00:00`
  for the same behavior; an existing custom time is not overwritten.

Current servers also consume the widget's `next_change_at` hint at the next
local midnight (accounting for daylight-saving changes), or earlier if the
snapshot becomes stale or expires. Older hosts may ignore that hint; the
placement's daily refresh remains the fallback. Scheduling follows the host's
normal quiet-hours, device polling, and server-restart behavior; it is not a
guarantee that every physical display updates at exactly midnight. Each
placement's opt-ins remain independent and off by default.

Today is derived from the latest uploaded snapshot, not a live read of the
iPhone's built-in Smart List. Only lists explicitly selected in Companion
participate, with the existing maximum of 20 lists and 200 incomplete items per
snapshot. Unsynced or truncated items cannot appear, and completions made on
the phone require a new Companion sync. Fresh, stale, expired, and unavailable
states continue to reflect the selected publisher's own snapshot.

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
