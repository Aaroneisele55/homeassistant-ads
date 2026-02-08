# Copilot Instructions for ADS Custom Integration

## Project Overview

This is a **Home Assistant custom integration** for the **Beckhoff ADS (Automation Device Specification)** protocol. It enables real-time push notifications from TwinCAT PLCs and other Beckhoff automation devices. The integration domain is `ads_custom` and all source code lives under `custom_components/ads_custom/`.

## Tech Stack

- **Language**: Python 3 with `from __future__ import annotations`
- **Framework**: Home Assistant (2024.1.0+)
- **Key dependency**: `pyads==3.4.0` for ADS communication
- **Validation**: `voluptuous` for YAML schema validation
- **Installation**: HACS-compatible custom component

## Code Structure

```
custom_components/ads_custom/
├── __init__.py         # Integration setup, YAML platform loading, service registration
├── config_flow.py      # UI-based configuration and options flows
├── const.py            # Constants (DOMAIN, CONF_* keys) and AdsType enum
├── entity.py           # Base AdsEntity class with device notification registration
├── hub.py              # AdsHub — manages ADS connection, thread-safe read/write
├── manifest.json       # Integration metadata, requirements, version
├── services.yaml       # Service definitions (write_data_by_name)
├── strings.json        # UI localization strings
├── icons.json          # Icon mappings
├── binary_sensor.py    # Binary sensor platform
├── sensor.py           # Sensor platform
├── switch.py           # Switch platform
├── light.py            # Light platform
├── cover.py            # Cover platform (YAML-only)
├── valve.py            # Valve platform (YAML-only)
├── select.py           # Select platform (YAML-only)
└── translations/
    └── en.json         # English translations
```

## Architecture & Patterns

### Entity Pattern

All entity types inherit from `AdsEntity` (in `entity.py`), which itself extends `homeassistant.helpers.entity.Entity`. The base class:

- Manages a `_state_dict` for storing state values
- Registers ADS device notifications via `async_initialize_device()`
- Uses `_attr_should_poll = False` (push-based updates from the PLC)
- Supports optional `unique_id` and `device_info` for device registry integration

### Platform Pattern

Each platform file (e.g., `switch.py`, `sensor.py`) provides:

- `setup_platform()` — for YAML-based configuration
- `async_setup_entry()` — for UI config entry-based setup
- A concrete entity class inheriting from both `AdsEntity` and the HA platform entity (e.g., `AdsSwitch(AdsEntity, SwitchEntity)`)
- A `PLATFORM_SCHEMA` using `voluptuous` for YAML validation

### Hub Pattern

`AdsHub` in `hub.py` wraps the `pyads` client. It is thread-safe (uses `threading.Lock()`) and manages:

- ADS connection lifecycle (`open`/`close`)
- Device notification registration and callbacks
- Data parsing for all supported PLC data types via `struct.unpack`

### Config Flow

`config_flow.py` implements both `ConfigFlow` (initial connection setup) and `OptionsFlowHandler` (entity management). It uses a menu-driven interface for adding, editing, and listing entities.

### Three Configuration Methods

The integration supports three configuration approaches:

1. **Full UI** — Settings → Devices & Services (no YAML)
2. **Full YAML** — Traditional `configuration.yaml`
3. **Mixed** — UI connection + YAML entities or vice versa

## Coding Conventions

- **Always** use `from __future__ import annotations` at the top of every Python file
- Use modern Python type hints: `str | None`, `dict[str, Any]`, etc.
- Use `_LOGGER = logging.getLogger(__name__)` for logging in every module
- Add docstrings to all classes and public methods
- Follow PEP 8 style guidelines
- Keep `const.py` as the single source of truth for constants and configuration keys
- Use `StrEnum` for enumerated types (see `AdsType` in `const.py`)

## ADS Data Types

The `AdsType` enum in `const.py` defines supported PLC data types: `BOOL`, `BYTE`, `INT`, `UINT`, `SINT`, `USINT`, `DINT`, `UDINT`, `WORD`, `DWORD`, `LREAL`, `REAL`, `STRING`, `TIME`, `DATE`, `DATE_AND_TIME`, `TOD`. When adding new types, update both `const.py` and the `unpack_formats` dict in `hub.py`.

## Adding a New Entity Platform

1. Create a new file (e.g., `number.py`) under `custom_components/ads_custom/`
2. Define a `PLATFORM_SCHEMA` with `voluptuous` for YAML support
3. Implement `setup_platform()` for YAML and `async_setup_entry()` for UI config flow
4. Create an entity class inheriting from `AdsEntity` and the relevant HA platform entity
5. Call `async_initialize_device()` in `async_added_to_hass()` with the correct `pyads.PLCTYPE_*`
6. Register the platform in `__init__.py` under the `PLATFORMS` list
7. Add UI strings to `strings.json` and `translations/en.json`
8. Update `config_flow.py` if the platform should be configurable via UI

## Testing

There is no automated test suite. Changes are tested manually against a real Home Assistant instance with a Beckhoff PLC. When making changes:

- Test with a real PLC if possible
- Verify all entity types still work
- Check Home Assistant logs for errors
- Test both new installations and upgrades

## Documentation

When making user-facing changes, update:

- `docs/index.md` — main documentation
- `ENTITY_PARAMETERS.md` — entity parameter reference
- `example_configuration.yaml` — YAML configuration examples
- `README.md` — if the change affects the project overview
