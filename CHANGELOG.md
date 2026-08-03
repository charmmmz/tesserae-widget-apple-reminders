# Changelog

All notable changes to this widget are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

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

[Unreleased]: https://github.com/charmmmz/tesserae-widget-apple-reminders/commits/main
