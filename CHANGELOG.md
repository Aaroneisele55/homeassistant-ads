# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
