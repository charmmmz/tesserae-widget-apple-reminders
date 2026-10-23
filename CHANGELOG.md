# Changelog

All notable changes to this widget are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.4.1] - 2026-10-23

### Added

- Today view for each paired Companion, combining incomplete due-today and
  overdue items from that publisher's explicitly synced lists. Other phones,
  future dates, undated items, and completed items are excluded. Addresses
  [#2](https://github.com/charmmmz/tesserae-widget-apple-reminders/issues/2).
- Next-change hints for local midnight and snapshot freshness/expiry boundaries
  on compatible hosts. Calendar-day arithmetic handles daylight-saving changes.
- Explicit empty-Today and unavailable-Companion messages, while retaining
  per-publisher freshness and never falling back to another phone.

### Changed

- Due-date calculations now use Tesserae's configured app timezone instead of
  the host/container's implicit local date. The daily custom-time prefill is
  now `00:00`; existing placement schedules and opt-ins remain unchanged.
- Change-driven refresh now subscribes to the complete Reminders source so
  Today responds to changes in any synced list, including list additions and
  removals. Enabled ordinary-list placements can consequently also refresh
  after unrelated Reminders changes; the host's current selector contract
  cannot describe dynamic publisher-wide dependencies.

## [0.4.0] - 2026-08-12

### Added

- Placement-level daily refresh support on compatible Tesserae servers keeps
  relative due-day labels current even when the Reminders snapshot itself has
  not changed. The default follows the server's local day boundary; `07:00` is
  offered only as an optional custom-time prefill.

### Fixed

- Lists published by different paired Companion installations are all
  available instead of one phone hiding another. When several publishers are
  present, picker labels include the paired client name, and each selection
  uses its own snapshot freshness.

## [0.3.0] - 2026-08-05

### Added

- Opt-in change-driven refresh support for each widget placement, narrowed to
  its selected Reminders `list_id` on compatible Tesserae servers.

## [0.2.0] - 2026-08-03

### Added

- Dynamic selection of any Apple Reminders list uploaded in Companion's latest
  generic `reminders` snapshot.
- Tasks, Food, Shopping, and Custom presentation presets.
- Configurable title, count label, item limit, due-date style, urgency marks,
  accent, and one-, two-, or auto-column layout.
- Explicit fresh, stale, expired, missing-snapshot, and missing-list states.
- Food presentation with `FOODIE`, “To eat”, relative-day labels, urgency
  colors, due-first ordering, and automatic two-column layout after five items.

### Changed

- Overdue and due-today rows now use only the left urgency bar, without an
  additional red inset outline around the full row.
- Snapshot freshness now shows the absolute local sync timestamp as
  `MM-DD HH:mm` instead of a relative “minutes ago” label that becomes
  ambiguous on an intermittently refreshed e-ink display.
- This widget is distributed separately from Reminders, Fridge and reads only
  the generic `reminders` source. It neither falls back to
  `reminders.fridge` nor migrates existing fridge-widget cells.
- A fresh snapshot with an empty published list set now has explicit test and
  documentation coverage: the widget preserves its configured selection and
  shows it as unavailable rather than switching lists.

[Unreleased]: https://github.com/charmmmz/tesserae-widget-apple-reminders/compare/v0.4.1...HEAD
[0.4.1]: https://github.com/charmmmz/tesserae-widget-apple-reminders/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/charmmmz/tesserae-widget-apple-reminders/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/charmmmz/tesserae-widget-apple-reminders/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/charmmmz/tesserae-widget-apple-reminders/releases/tag/v0.2.0
