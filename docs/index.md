# ADS Custom — Full Documentation

## Overview

The **ADS Custom** integration (`ads_custom`) connects Home Assistant to Beckhoff TwinCAT PLCs through the ADS (Automation Device Specification) protocol. Variable changes on the PLC are pushed to Home Assistant in real time, so no polling is required.

The integration supports seven entity types — Binary Sensor, Cover, Light, Select, Sensor, Switch, and Valve — and can be set up entirely through the **Home Assistant UI**, entirely through **YAML**, or with a **combination** of both.

---

## Differences from the core ADS integration

Home Assistant includes a built-in `ads` integration. This custom integration uses the separate domain `ads_custom`, so both can coexist in the same instance. The table below highlights the main differences.

| Area | Core `ads` | `ads_custom` |
|------|-----------|-------------|
| **Configuration** | YAML only | UI, YAML, or mixed |
| **Dimmable lights** | Requires a sensor + binary sensor + switch + template light | Single `light` entity with a brightness variable |
| **Brightness data type** | No direct byte support | BYTE or UINT with configurable 0-*n* scale |
| **Cover entities** | Basic open/close | Position feedback (BYTE or UINT), set-position, open/close/stop triggers, inverted logic |
| **Select entities** | Not available | Map a PLC integer index to a list of options |
| **Valve entities** | Not available | Open/close with device-class support |
| **Supported platforms** | Binary Sensor, Light, Sensor, Switch | Binary Sensor, Cover, Light, Select, Sensor, Switch, Valve |

### Dimmable light — before and after

With the core integration you typically need four entities plus a template:

```yaml
# Core ADS — 4 entities + template
sensor:
  - platform: ads
    adsvar: .Light.Brightness
binary_sensor:
  - platform: ads
    adsvar: .Light.Enable
switch:
  - platform: ads
    adsvar: .Light.Enable
template:
  - light:
      name: My Light
      # … template mapping brightness …
```

With ADS Custom the same result is a single entity:

```yaml
# ADS Custom — 1 entity
light:
  - platform: ads_custom
    adsvar: .Light.Enable
    adsvar_brightness: .Light.Brightness
    adsvar_brightness_scale: 100
    name: My Light
```

---

## Installation

### HACS (recommended)

1. In Home Assistant open **HACS → Integrations**.
2. Three-dot menu → **Custom repositories** → paste this repository URL → category **Integration**.
3. Click **Install** and restart Home Assistant.

### Manual

Copy `custom_components/ads_custom` into your Home Assistant `custom_components/` directory and restart.

---

## Setting up the connection

Before any entities can communicate with the PLC you need to configure the ADS connection. You can do this through the UI or through YAML.

### Prerequisites

* A Beckhoff TwinCAT 2 or 3 PLC reachable on the local network.
* An AMS route on the PLC that points to the Home Assistant host.
* Firewall rules allowing UDP 48899 and the AMS port (default 48898).

### UI setup

1. **Settings → Devices & Services → Add Integration**.
2. Search for **ADS Custom**.
3. Enter the connection parameters (see table below) and click **Submit**.
4. The integration tests the connection before accepting it.

### YAML setup

Add the following to `configuration.yaml` and restart Home Assistant:

```yaml
ads_custom:
  device: "192.168.1.100.1.1"
  ip_address: "192.168.1.100"
  port: 48898
```

### Connection parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `device` | string | **Yes** | — | AMS Net ID of the PLC (e.g. `192.168.1.100.1.1`) |
| `ip_address` | string | No | — | IP address of the PLC. Can be omitted when AMS routing is configured on the network. |
| `port` | integer | No | `48898` | AMS port number. Common values: 48898 (TwinCAT 2), 851 (TwinCAT 3 Runtime 1). |

---

## Adding entities

Entities can be added through the **UI** or through **YAML**. You can also mix both methods — for example, set up the connection in the UI and define entities in YAML.

### UI entity setup

After the connection is configured:

1. Go to **Settings → Devices & Services → ADS Custom**.
2. Click **Configure** (or the three-dot menu → **Options**).
3. Choose **Add Entity** and select the entity type.
4. Fill in the PLC variable name, a friendly name, and any type-specific options.
5. Click **Submit** — the entity appears immediately without a restart.

Entity types currently available in the UI: **Switch, Sensor, Binary Sensor, Light**.
Cover, Valve, and Select can be added via YAML.

### YAML entity setup

Define entities under the matching platform key in `configuration.yaml`. A restart is required after changes.

The sections below document every entity type and its parameters.

---

## Binary Sensor

Reads a boolean (or floating-point) value from the PLC and exposes it as on/off.

```yaml
binary_sensor:
  - platform: ads_custom
    adsvar: GVL.door_open
    name: Front Door
    device_class: door
    unique_id: ads_front_door
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `adsvar` | string | **Yes** | — | PLC variable to monitor |
| `adstype` | string | No | `bool` | `bool` or `real`. When set to `real`, any non-zero value is treated as *on*. |
| `name` | string | No | `ADS binary sensor` | Friendly name |
| `device_class` | string | No | — | [Binary sensor device class](https://www.home-assistant.io/integrations/binary_sensor/#device-class) (e.g. `door`, `motion`, `window`) |
| `unique_id` | string | No | — | Unique identifier for UI customisation |

---

## Cover

Controls blinds, shutters, garage doors, or similar position-aware devices.

```yaml
cover:
  - platform: ads_custom
    name: Living Room Blinds
    adsvar_position: GVL.cover_position
    adsvar_set_position: GVL.cover_set_position
    adsvar_open: GVL.cover_open
    adsvar_close: GVL.cover_close
    adsvar_stop: GVL.cover_stop
    device_class: blind
    unique_id: ads_living_room_blinds
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `adsvar` | string | No\* | — | Boolean variable that is `TRUE` when the cover is closed (read-only) |
| `adsvar_position` | string | No\* | — | Current position 0–100 (read-only). 0 = closed, 100 = open. |
| `adsvar_position_type` | string | No | `byte` | Data type of the position variable: `byte` or `uint` |
| `adsvar_set_position` | string | No | — | Target position 0–100 (write) |
| `adsvar_open` | string | No | — | Boolean trigger for opening (write-only, set to `TRUE`) |
| `adsvar_close` | string | No | — | Boolean trigger for closing (write-only, set to `TRUE`) |
| `adsvar_stop` | string | No | — | Boolean trigger for stopping (write-only, set to `TRUE`) |
| `inverted` | boolean | No | `false` | When `true`, position 0 = open and 100 = closed |
| `name` | string | No | `ADS Cover` | Friendly name |
| `device_class` | string | No | — | [Cover device class](https://www.home-assistant.io/integrations/cover/#device-class) (e.g. `blind`, `garage`, `shutter`) |
| `unique_id` | string | No | — | Unique identifier |

\* Either `adsvar` or `adsvar_position` must be provided. If only `adsvar_position` is given, the cover is considered closed when the position equals 0.

**Feature flags** are set automatically:

* **OPEN / CLOSE** — enabled when `adsvar_open`, `adsvar_close`, or `adsvar_set_position` is configured.
* **STOP** — enabled when `adsvar_stop` is configured.
* **SET_POSITION** — enabled when `adsvar_set_position` is configured.

---

## Light

On/off control with optional brightness dimming.

### Simple on/off

```yaml
light:
  - platform: ads_custom
    adsvar: GVL.light_enable
    name: Room Light
    unique_id: ads_room_light
```

### Dimmable light (Beckhoff 0-100 scale)

```yaml
light:
  - platform: ads_custom
    adsvar: GVL.light_enable
    adsvar_brightness: GVL.light_brightness
    adsvar_brightness_scale: 100
    name: Dimmable Light
    unique_id: ads_dimmable_light
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `adsvar` | string | **Yes** | — | Boolean variable for on/off state |
| `adsvar_brightness` | string | No | — | Variable for brightness level. Omit for a simple on/off light. |
| `adsvar_brightness_type` | string | No | `byte` | `byte` (0–255) or `uint` (0–65535) |
| `adsvar_brightness_scale` | integer | No | `255` | Maximum brightness value on the PLC side (e.g. `100` for Beckhoff 0-100 range) |
| `name` | string | No | `ADS Light` | Friendly name |
| `unique_id` | string | No | — | Unique identifier |

Home Assistant internally uses 0–255 for brightness. The integration converts automatically based on `adsvar_brightness_scale`.

---

## Select

Maps a PLC integer to a list of human-readable options.

```yaml
select:
  - platform: ads_custom
    adsvar: GVL.mode_select
    name: System Mode
    options:
      - "Off"
      - "Auto"
      - "Manual"
    unique_id: ads_system_mode
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `adsvar` | string | **Yes** | — | Integer variable storing the selected index (0-based) |
| `options` | list | **Yes** | — | Ordered list of option labels |
| `name` | string | No | `ADS select` | Friendly name |
| `unique_id` | string | No | — | Unique identifier |

The PLC stores `0` for the first option, `1` for the second, and so on.

---

## Sensor

Reads numeric or string values from the PLC.

```yaml
sensor:
  - platform: ads_custom
    adsvar: GVL.temperature
    name: Room Temperature
    adstype: real
    unit_of_measurement: "°C"
    device_class: temperature
    state_class: measurement
    unique_id: ads_room_temp
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `adsvar` | string | **Yes** | — | PLC variable to monitor |
| `adstype` | string | No | `int` | PLC data type — see [Supported data types](#supported-data-types) |
| `adsfactor` | integer | No | — | Divides the raw value by this factor (for scaling) |
| `name` | string | No | `ADS sensor` | Friendly name |
| `unit_of_measurement` | string | No | — | Unit string shown in the UI (e.g. `°C`, `%`, `kWh`) |
| `device_class` | string | No | — | [Sensor device class](https://www.home-assistant.io/integrations/sensor/#device-class) (e.g. `temperature`, `humidity`, `power`) |
| `state_class` | string | No | — | `measurement`, `total`, or `total_increasing` |
| `unique_id` | string | No | — | Unique identifier |

---

## Switch

Boolean on/off control.

```yaml
switch:
  - platform: ads_custom
    adsvar: GVL.pump
    name: Water Pump
    unique_id: ads_water_pump
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `adsvar` | string | **Yes** | — | Boolean variable for on/off state |
| `name` | string | No | `ADS Switch` | Friendly name |
| `unique_id` | string | No | — | Unique identifier |

---

## Valve

Open/close control for fluid valves.

```yaml
valve:
  - platform: ads_custom
    adsvar: GVL.valve_open
    name: Water Valve
    device_class: water
    unique_id: ads_water_valve
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `adsvar` | string | **Yes** | — | Boolean variable indicating whether the valve is open |
| `name` | string | No | `ADS valve` | Friendly name |
| `device_class` | string | No | — | `water` or `gas` |
| `unique_id` | string | No | — | Unique identifier |

---

## Services

### `ads_custom.write_data_by_name`

Write a value to any ADS variable, even one that does not have a corresponding entity.

```yaml
service: ads_custom.write_data_by_name
data:
  adsvar: "GVL.setpoint"
  adstype: "int"
  value: 100
```

| Attribute | Required | Description |
|-----------|----------|-------------|
| `adsvar` | Yes | PLC variable name (e.g. `GVL.setpoint`) |
| `adstype` | Yes | Data type (e.g. `int`, `bool`, `real`) |
| `value` | Yes | Value to write |

---

## Supported data types

These types can be used with the `adstype` parameter on sensors and with the `write_data_by_name` service.

| Type | Description | Size |
|------|-------------|------|
| `bool` | Boolean | 1 bit |
| `byte` | Unsigned byte | 8 bits |
| `sint` | Signed short integer | 8 bits |
| `usint` | Unsigned short integer | 8 bits |
| `int` | Signed integer | 16 bits |
| `uint` | Unsigned integer | 16 bits |
| `word` | Unsigned word | 16 bits |
| `dint` | Signed double integer | 32 bits |
| `udint` | Unsigned double integer | 32 bits |
| `dword` | Unsigned double word | 32 bits |
| `real` | IEEE 754 float | 32 bits |
| `lreal` | IEEE 754 double | 64 bits |
| `string` | Variable-length string | — |
| `time` | Time duration | 32 bits |
| `date` | Date | 32 bits |
| `date_and_time` | Date and time | 32 bits |
| `tod` | Time of day | 32 bits |

---

## Unique IDs

All entity types accept an optional `unique_id`. Setting one allows you to:

* Rename, re-icon, or disable the entity from the Home Assistant UI.
* Change the device class without editing YAML.
* Keep entity history if you later change the friendly name.

When using UI-created entities, a unique ID is assigned automatically.

---

## Troubleshooting

### Cannot connect

* Verify the AMS Net ID format (`x.x.x.x.x.x`).
* Confirm the PLC IP address is reachable (`ping`).
* Check that an AMS route from the PLC to Home Assistant exists.
* Ensure UDP 48899 and the AMS port (default 48898) are open in the firewall.

### Entities do not appear

* Double-check variable names — they are **case-sensitive**.
* YAML entities require a Home Assistant restart after changes.
* Look for errors in **Settings → System → Logs**.

### Values stop updating

* Confirm the PLC variable still exists and is accessible.
* Make sure the configured `adstype` matches the actual PLC type.
* Verify AMS routes are bidirectional.
* Check Home Assistant logs for notification errors.

### Connection drops

* Investigate network stability between Home Assistant and the PLC.
* Check the TwinCAT system status on the PLC.
* Ensure the PLC is not overloaded with too many ADS clients.

---

## Further reading

* [Entity parameter reference](../ENTITY_PARAMETERS.md) — full parameter tables for every entity type.
* [Example `configuration.yaml`](../example_configuration.yaml) — copy-paste YAML for all entity types.
* [CONTRIBUTING.md](../CONTRIBUTING.md) — how to report issues or submit pull requests.
