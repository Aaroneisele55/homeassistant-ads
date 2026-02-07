# ADS Custom - Entity Parameters Documentation

This document provides a comprehensive reference for all configuration parameters available for each entity type in the ADS Custom integration.

## Table of Contents

- [Connection Configuration](#connection-configuration)
- [Binary Sensor](#binary-sensor)
- [Cover](#cover)
- [Light](#light)
- [Select](#select)
- [Sensor](#sensor)
- [Switch](#switch)
- [Valve](#valve)

---

## Connection Configuration

The ADS connection must be configured before any entities can be added.

### Configuration

```yaml
ads_custom:
  device: '<AMS_NET_ID>'      # Required
  ip_address: '<IP_ADDRESS>'  # Optional
  port: <PORT>                # Optional, default: 48898
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `device` | string | **Yes** | - | AMS Net ID of your ADS device (e.g., `192.168.1.100.1.1`) |
| `ip_address` | string | No | - | IP address of your ADS device |
| `port` | integer | No | `48898` | AMS port number |

---

## Binary Sensor

Binary sensors read a boolean value from the PLC and represent it as an on/off state.

### Configuration

```yaml
binary_sensor:
  - platform: ads_custom
    adsvar: GVL.door_open
    name: Front Door
    device_class: door
    unique_id: ads_front_door
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `adsvar` | string | **Yes** | - | The name of the ADS boolean variable to monitor |
| `name` | string | No | `ADS binary sensor` | Friendly name for the entity |
| `device_class` | string | No | `moving` | The [device class](https://www.home-assistant.io/integrations/binary_sensor/#device-class) (e.g., `door`, `motion`, `window`) |
| `unique_id` | string | No | - | Unique identifier for the entity |

### Supported Device Classes

Common device classes include: `battery`, `battery_charging`, `carbon_monoxide`, `cold`, `connectivity`, `door`, `garage_door`, `gas`, `heat`, `light`, `lock`, `moisture`, `motion`, `moving`, `occupancy`, `opening`, `plug`, `power`, `presence`, `problem`, `running`, `safety`, `smoke`, `sound`, `tamper`, `update`, `vibration`, `window`

---

## Cover

Covers represent devices like blinds, shutters, or garage doors that can be opened and closed.

### Configuration Examples

#### Traditional Cover with Closed State Sensor

```yaml
cover:
  - platform: ads_custom
    adsvar: GVL.cover_closed
    name: Living Room Blinds
    adsvar_position: GVL.cover_position
    adsvar_set_position: GVL.cover_set_position
    adsvar_open: GVL.cover_open
    adsvar_close: GVL.cover_close
    adsvar_stop: GVL.cover_stop
    device_class: blind
    unique_id: ads_living_room_blinds
```

#### Cover with Position Feedback Only (UINT)

This configuration is ideal for covers where:
- Position is read-only (status feedback from PLC)
- Open/close are write-only command triggers
- No separate closed state sensor is available

```yaml
cover:
  - platform: ads_custom
    name: Garage Door
    adsvar_position: GVL.garage_position        # Read-only: current position (UINT)
    adsvar_position_type: uint
    adsvar_open: GVL.garage_open                # Write-only: set to TRUE to open
    adsvar_close: GVL.garage_close              # Write-only: set to TRUE to close
    device_class: garage
    unique_id: ads_garage_door
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `adsvar` | string | No* | - | Boolean variable indicating if the cover is closed (read-only status feedback) |
| `adsvar_position` | string | No* | - | Variable for reading the current position 0-100 (read-only status feedback) |
| `adsvar_position_type` | string | No | `byte` | Data type for position variables: `byte` (0-255) or `uint` (0-65535). Home Assistant will scale to 0-100. |
| `adsvar_set_position` | string | No | - | Variable for setting the target position 0-100 (write-only command) |
| `adsvar_open` | string | No | - | Boolean variable to trigger open command (write-only, set to TRUE to open) |
| `adsvar_close` | string | No | - | Boolean variable to trigger close command (write-only, set to TRUE to close) |
| `adsvar_stop` | string | No | - | Boolean variable to trigger stop command (write-only, set to TRUE to stop) |
| `name` | string | No | `ADS Cover` | Friendly name for the entity |
| `device_class` | string | No | - | The [device class](https://www.home-assistant.io/integrations/cover/#device-class) (e.g., `blind`, `curtain`, `garage`, `shutter`) |
| `unique_id` | string | No | - | Unique identifier for the entity |

**Note:** Either `adsvar` or `adsvar_position` must be provided. If only `adsvar_position` is provided, the closed state will be derived from the position (position == 0 means closed).

### Supported Device Classes

Common device classes include: `awning`, `blind`, `curtain`, `damper`, `door`, `garage`, `gate`, `shade`, `shutter`, `window`

### Features

The following features are automatically enabled based on configuration:

- **OPEN/CLOSE**: Always available if `adsvar_open` or `adsvar_close` are configured, or if `adsvar_set_position` is configured
- **STOP**: Available if `adsvar_stop` is configured
- **SET_POSITION**: Available if `adsvar_set_position` is configured

### Read/Write Behavior

- **Read-only (status feedback)**: `adsvar`, `adsvar_position` - These variables are only read to get the current state
- **Write-only (commands)**: `adsvar_open`, `adsvar_close`, `adsvar_stop` - Home Assistant writes TRUE to these to trigger actions
- **Read/Write**: `adsvar_set_position` - Can be both read and written (if the PLC supports reading back the target position)

---

## Light

Lights support simple on/off control or dimmable control with brightness.

### Configuration Examples

#### Simple On/Off Light

```yaml
light:
  - platform: ads_custom
    adsvar: GVL.light_enable
    name: Room Light
    unique_id: ads_room_light
```

#### Dimmable Light with BYTE Brightness (0-255)

```yaml
light:
  - platform: ads_custom
    adsvar: GVL.light_enable
    adsvar_brightness: GVL.light_brightness
    name: Dimmable Light
    unique_id: ads_dimmable_light
```

#### Beckhoff Light with BYTE Brightness (0-100 scale)

```yaml
light:
  - platform: ads_custom
    adsvar: GVL.beckhoff_light_enable
    adsvar_brightness: GVL.beckhoff_light_brightness
    adsvar_brightness_scale: 100
    adsvar_brightness_type: byte
    name: Beckhoff Light
    unique_id: ads_beckhoff_light
```

#### Light with UINT Brightness

```yaml
light:
  - platform: ads_custom
    adsvar: GVL.light_enable
    adsvar_brightness: GVL.light_brightness
    adsvar_brightness_type: uint
    name: Light with UINT
    unique_id: ads_light_uint
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `adsvar` | string | **Yes** | - | Boolean variable for the light's on/off state |
| `adsvar_brightness` | string | No | - | Variable for the light's brightness level |
| `adsvar_brightness_type` | string | No | `byte` | Data type for brightness: `byte` (0-255) or `uint` (0-65535) |
| `adsvar_brightness_scale` | integer | No | `255` | Maximum brightness value in the PLC (e.g., `100` for 0-100 range, `255` for 0-255 range) |
| `name` | string | No | `ADS Light` | Friendly name for the entity |
| `unique_id` | string | No | - | Unique identifier for the entity |

### Notes

- If `adsvar_brightness` is not provided, the light will be a simple on/off light
- Home Assistant always uses 0-255 internally for brightness, and the integration handles conversion based on `adsvar_brightness_scale`
- For Beckhoff systems using 0-100 brightness, set `adsvar_brightness_scale: 100`

---

## Select

Select entities allow choosing from a predefined list of options. The selected option index is stored as an integer in the PLC.

### Configuration

```yaml
select:
  - platform: ads_custom
    adsvar: GVL.mode_select
    name: System Mode
    options:
      - "Off"
      - "Auto"
      - "Manual"
      - "Service"
    unique_id: ads_system_mode
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `adsvar` | string | **Yes** | - | Integer variable storing the selected option index (0-based) |
| `options` | list | **Yes** | - | List of available options (strings) |
| `name` | string | No | `ADS select` | Friendly name for the entity |
| `unique_id` | string | No | - | Unique identifier for the entity |

### Notes

- The PLC variable stores the index of the selected option (0 for first option, 1 for second, etc.)
- The options list must contain at least one option

---

## Sensor

Sensors read numeric or string values from the PLC and display them in Home Assistant.

### Configuration Examples

#### Temperature Sensor

```yaml
sensor:
  - platform: ads_custom
    adsvar: GVL.temperature
    name: Room Temperature
    adstype: real
    unit_of_measurement: '°C'
    device_class: temperature
    state_class: measurement
    unique_id: ads_room_temp
```

#### Integer Counter with Scaling

```yaml
sensor:
  - platform: ads_custom
    adsvar: GVL.counter
    name: Production Count
    adstype: dint
    adsfactor: 100
    unit_of_measurement: 'items'
    state_class: total_increasing
    unique_id: ads_prod_count
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `adsvar` | string | **Yes** | - | The name of the ADS variable to monitor |
| `adstype` | string | No | `int` | The PLC data type of the variable (see [Supported Data Types](#supported-data-types)) |
| `adsfactor` | integer | No | - | Factor to divide the raw value by (for scaling) |
| `name` | string | No | `ADS sensor` | Friendly name for the entity |
| `unit_of_measurement` | string | No | - | Unit of measurement (e.g., `°C`, `%`, `kWh`) |
| `device_class` | string | No | - | The [device class](https://www.home-assistant.io/integrations/sensor/#device-class) (e.g., `temperature`, `humidity`, `power`) |
| `state_class` | string | No | - | The [state class](https://www.home-assistant.io/integrations/sensor/#state-class) (e.g., `measurement`, `total`, `total_increasing`) |
| `unique_id` | string | No | - | Unique identifier for the entity |

### Supported Data Types

The following ADS/PLC data types are supported for sensors:

- `bool` - Boolean (True/False)
- `byte` - Byte (0-255)
- `int` - Integer (16-bit, -32768 to 32767)
- `uint` - Unsigned Integer (16-bit, 0 to 65535)
- `sint` - Short Integer (8-bit, -128 to 127)
- `usint` - Unsigned Short Integer (8-bit, 0 to 255)
- `dint` - Double Integer (32-bit, -2147483648 to 2147483647)
- `udint` - Unsigned Double Integer (32-bit, 0 to 4294967295)
- `word` - Word (16-bit, 0 to 65535)
- `dword` - Double Word (32-bit, 0 to 4294967295)
- `real` - Real (32-bit float)
- `lreal` - Long Real (64-bit float)

### Supported Device Classes

Common device classes include: `apparent_power`, `aqi`, `atmospheric_pressure`, `battery`, `carbon_dioxide`, `carbon_monoxide`, `current`, `data_rate`, `data_size`, `date`, `distance`, `duration`, `energy`, `energy_storage`, `enum`, `frequency`, `gas`, `humidity`, `illuminance`, `irradiance`, `moisture`, `monetary`, `nitrogen_dioxide`, `nitrogen_monoxide`, `nitrous_oxide`, `ozone`, `ph`, `pm1`, `pm10`, `pm25`, `power`, `power_factor`, `precipitation`, `precipitation_intensity`, `pressure`, `reactive_power`, `signal_strength`, `sound_pressure`, `speed`, `sulphur_dioxide`, `temperature`, `timestamp`, `volatile_organic_compounds`, `volatile_organic_compounds_parts`, `voltage`, `volume`, `volume_flow_rate`, `volume_storage`, `water`, `weight`, `wind_speed`

### Supported State Classes

- `measurement` - For sensors that measure values that can go up and down
- `total` - For sensors that represent cumulative totals that can reset
- `total_increasing` - For sensors that represent monotonically increasing totals

---

## Switch

Switches represent boolean on/off controls in the PLC.

### Configuration

```yaml
switch:
  - platform: ads_custom
    adsvar: GVL.pump
    name: Water Pump
    unique_id: ads_water_pump
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `adsvar` | string | **Yes** | - | Boolean variable for the switch's on/off state |
| `name` | string | No | `ADS Switch` | Friendly name for the entity |
| `unique_id` | string | No | - | Unique identifier for the entity |

---

## Valve

Valves represent devices that can be opened and closed, typically for fluid control.

### Configuration

```yaml
valve:
  - platform: ads_custom
    adsvar: GVL.valve_open
    name: Water Valve
    device_class: water
    unique_id: ads_water_valve
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `adsvar` | string | **Yes** | - | Boolean variable indicating if the valve is open |
| `name` | string | No | `ADS valve` | Friendly name for the entity |
| `device_class` | string | No | - | The [device class](https://www.home-assistant.io/integrations/valve/#device-class) (e.g., `water`, `gas`) |
| `unique_id` | string | No | - | Unique identifier for the entity |

### Supported Device Classes

Common device classes include: `gas`, `water`

---

## General Notes

### Unique IDs

- Unique IDs are optional but highly recommended
- They enable entity customization in the UI and persist entity settings across restarts
- Each entity should have a globally unique identifier

### Variable Names

- ADS variable names are case-sensitive
- Variables can use dot notation for structured types (e.g., `GVL.MyStruct.MyVariable`)
- The `GVL` prefix is common in TwinCAT but not required

### Data Type Matching

- Ensure the configured data type matches the PLC variable type
- Mismatched types may cause errors or incorrect values
- UINT is now fully supported for position values in covers

### Push Notifications

- All entities use push notifications from the PLC for real-time updates
- There is no polling involved, ensuring minimal network traffic
- Entities will show as unavailable until the first update is received

### Service Calls

You can write to any ADS variable using the `ads_custom.write_data_by_name` service:

```yaml
service: ads_custom.write_data_by_name
data:
  adsvar: 'GVL.setpoint'
  adstype: 'int'
  value: 100
```

This is useful for writing to variables that don't have a corresponding entity or for advanced automation scenarios.
