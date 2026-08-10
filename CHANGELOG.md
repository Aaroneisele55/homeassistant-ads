# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.26] - 2026-08-10

### Changed
- Aktualisieren von en.json
## [1.2.25] - 2026-08-10

### Changed
- Aktualisieren von de.json
## [1.2.24] - 2026-08-10

### Changed
- Aktualisieren von de.json
## [1.2.23] - 2026-08-10

### Changed
- Show list of empty devices instead pf just number of them
## [1.2.22] - 2026-08-09

### Changed
- Change main config options flow to show tree view of devices+entities and offer "delete all empty devices" option
## [1.2.21] - 2026-08-09

### Changed
- add_delete_all_empty_devices
## [1.2.20] - 2026-08-09

### Changed
- update
## [1.2.19] - 2026-08-06

### Changed
- Added an explicit grouped-device "Add entity" action to the hub options flow and made entity migration walk nested grouped subentry data so existing installs keep their device assignments during upgrade.

## [1.2.18] - 2026-08-06

### Fixed
- Restructured ADS entity device handling for Home Assistant 2026.8's single-config-entry
  device registry model. Each entity subentry now owns its own registry device ID, and the
  config flow no longer offers the shared-device move workflow that would recreate an invalid
  multi-subentry device.

## [1.2.17] - 2026-08-06

### Changed
- Adapted device-registry interactions for Home Assistant 2026.8's single-config-entry
  device model (devices now belong to exactly one config entry and at most one
  subentry). Added `device_registry_compat.py`, which transparently supports both
  the pre-2026.8 and 2026.8+ device registry APIs, so the integration keeps working
  unmodified on older HA Core versions too. See
  https://developers.home-assistant.io/blog/2026/07/21/device-registry-single-config-entry/

## [1.2.16] - 2026-05-31

### Changed
- Merge pull request #95 from Aaroneisele55/copilot/implement-umlaut-handling
## [1.2.15] - 2026-05-24

### Changed
- bump version to remove non-working feature added in 1.2.13/14
## [1.2.12] - 2026-05-23

### Changed
- Merge branch 'main' of https://github.com/Aaroneisele55/homeassistant-ads
## [1.2.11] - 2026-05-23

### Added
- Hub options flow action to delete all empty ADS devices that no longer have entities assigned.

## [1.2.10] - 2026-05-22

### Changed
- Update config_flow.py
## [1.2.9] - 2026-05-22

### Changed
- Refactor config flow and improve input validation
## [1.2.8] - 2026-05-22

### Changed
- Refactor config flow by removing config_entry assignment
## [1.2.7] - 2026-05-22

### Fixed
- Fix device association reset logic in init.py
## [1.2.6] - 2026-05-22

### Changed
- Refactor device registry updates for hub entries
## [1.2.5] - 2026-05-22

### Fixed
- fix crash
## [1.2.4] - 2026-05-22

### Fixed
- fix error with subentry id
## [1.2.3] - 2026-05-21



### Added
- Hub-level options flow for device-centric management: select device, then either select an assigned entity to edit, rename the device, or delete an empty device (with confirmation).

### Changed
- New entity creation now requires explicit device assignment (existing device or create new device).
- Legacy entities without explicit device assignment are migrated to a shared default device per hub.

## [1.2.2] - 2026-05-20



### Added
- Config-flow support to assign entities to an existing ADS device, or create a new shared device entry during add/edit.

### Changed
- Entity setup now uses persisted `entity_device_id` assignments so multiple entities can appear under one device instead of always creating one device per entity.

## [1.2.1] - 2026-05-20

### Changed
- Merge pull request #89 from Aaroneisele55/copilot/update-changelog-generation
## [1.2.0] - 2026-03-05



### Added
- Documented and finalized branding file layout: existing `custom_components/ads_custom/icon.png` and `logo.png` are kept for older Home Assistant / HACS behavior, and duplicated copies are now provided under `custom_components/ads_custom/brand/icon.png` and `logo.png` for the Home Assistant 2026.3+ brands proxy API; docs/ATTRIBUTION.md has been updated so that all shipped branding asset paths are covered consistently by the same attribution and licensing terms.

## [1.1.14] - 2026-02-12

## [1.1.13] - 2026-02-12

## [1.1.12] - 2026-02-12

## [1.1.11] - 2026-02-12

### Changed
- Internal version bump (no user-facing changes)

## [1.1.10] - 2026-02-12

### Changed
- Internal version bump (no user-facing changes)

## [1.1.9] - 2026-02-12

### Changed
- Internal version bump (no user-facing changes)

## [1.1.8] - 2026-02-12

### Changed
- Internal version bump (no user-facing changes)

## [1.1.7] - 2026-02-12

### Changed
- Internal version bump (no user-facing changes)

## [1.1.6] - 2026-02-12

### Changed
- Internal version bump (no user-facing changes)

## [1.1.5] - 2026-02-12

### Changed
- Internal version bump (no user-facing changes)

## [1.1.4] - 2026-02-11

### Fixed
- Cover state stuck on "opening"/"closing" after reaching fully open/closed position
- Cover state stuck on "opening"/"closing" after stopping at intermediate position (via stop command or external stop)
- HACS version detection - automated workflow now creates GitHub Releases (not just git tags) so HACS can properly detect and display available versions

## [1.1.3] - 2026-02-11

## [1.1.2] - 2026-02-11

### Added
- Icon and logo setup guide (docs/ICON_SETUP.md) with detailed instructions for displaying branding in Home Assistant and HACS
- ATTRIBUTION.md file with proper attribution and licensing information for branding assets

### Fixed
- Documented why icons may not display and how to properly configure them for both Home Assistant and HACS

## [1.1.1] - 2026-02-11

### Added
- Integration icon and logo derived from the Home Assistant core ADS integration branding (see https://github.com/home-assistant/brands) for improved branding in Home Assistant UI and HACS
- Attribution and licensing note for ADS branding assets (see ATTRIBUTION.md for details; these assets are subject to their own license and trademark terms and are not covered by this project's Apache-2.0 license)

## [1.1.0] - 2026-02-11

### Added
- Automated version management system with bump_version.py script
- GitHub Actions workflow for automatic version bumping on pushes to main
- VERSION_MANAGEMENT.md documentation for AI agents and developers
- Support for version bump detection via commit messages, PR labels, and conventional commits
- Automatic CHANGELOG.md updates with version sections

## [1.0.0] - 2026-02-08

### Added
- Initial versioned release with HACS changelog support
- Full UI configuration support for connection and all entity types
- Seven entity types: Binary Sensor, Cover, Light, Select, Sensor, Switch, Valve
- Real-time push notifications from PLC using ADS device notifications
- Support for all PLC data types (BOOL, INT, UINT, SINT, USINT, DINT, UDINT, WORD, DWORD, LREAL, REAL, STRING, TIME, DATE, DATE_AND_TIME, TOD)
- Custom brightness scaling for lights (0-100 or 0-255)
- Unique ID support for all entities
- Service calls to write PLC variables (write_data_by_name)
- Three configuration methods: Full UI, Full YAML, or Mixed
- Device registry integration for proper device grouping

### Changed
- Simplified hub options menu - entities are now managed through their individual device pages
- Entity editing now handled through each entity's own options flow instead of hub menu

### Removed
- "List Entities" option from hub menu (entities visible in device pages)
- "Edit Entity" option from hub menu (edit through individual entity config entries)

### Fixed
- Improved thread safety in ADS hub operations
- Better error handling for ADS connection failures
### Added
- replace brand/logo.png with official ADS logo from brands CDN
- Add brand/ directory with icon and logo for HA 2026.3 brands proxy API

### Changed

### Fixed

### Removed

### Security
### Added
- finalize shared device assignment flow and tests
- add configurable entity device assignment in config flow and platforms

### Changed

### Fixed

### Removed

### Security
### Added
- add hub device-management options flow and legacy default-device migration

### Changed

### Fixed

### Removed

### Security

