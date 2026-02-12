# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.13] - 2026-02-12

## [1.1.12] - 2026-02-12

## [1.1.11] - 2026-02-12

## [1.1.10] - 2026-02-12

## [1.1.9] - 2026-02-12

## [1.1.8] - 2026-02-12

## [1.1.7] - 2026-02-12

## [1.1.6] - 2026-02-12

## [1.1.5] - 2026-02-12

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
