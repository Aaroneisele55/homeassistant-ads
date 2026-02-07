---
title: ADS Custom
description: Instructions on how to integrate Beckhoff ADS devices with Home Assistant.
ha_category: Hub
ha_iot_class: Local Push
ha_release: "2024.1"
ha_domain: ads_custom
---

The `ads_custom` integration allows you to connect Home Assistant to Beckhoff ADS (Automation Device Specification) devices, such as TwinCAT PLCs. This integration provides real-time communication with your PLC variables through push notifications.

This is a custom integration with a different domain (`ads_custom`) to prevent conflicts with Home Assistant's core ADS integration. It is completely YAML-based for maximum transparency and version control.

## Features

- **Real-time push notifications** from PLC to Home Assistant
- **Multiple entity types**: Binary Sensors, Covers, Lights, Sensors, Switches, Valves, Select
- **All PLC data types** supported (BOOL, INT, UINT, REAL, LREAL, etc.)
- **Custom brightness scaling** for lights (0-100 or 0-255)
- **Unique ID support** for all entities enabling UI customization
- **Service calls** to write data to PLC variables
- **100% YAML configuration** for version control

## Configuration

The ADS Custom integration is configured via YAML in your `configuration.yaml` file.

### Initial Setup

First, configure the ADS connection in your `configuration.yaml`:

```yaml
ads_custom:
  device: "192.168.1.100.1.1"  # AMS Net ID (required)
  ip_address: "192.168.1.100"  # IP address (optional)
  port: 48898                   # AMS port (optional, default: 48898)
```

{% configuration %}
device:
  description: The AMS Net ID of your ADS device.
  required: true
  type: string
ip_address:
  description: The IP address of your ADS device.
  required: false
  type: string
port:
  description: The AMS port number.
  required: false
  type: integer
  default: 48898
{% endconfiguration %}

### Setup Notes

1. **AMS Net ID**: Unique identifier for each ADS device, typically in the format `x.x.x.x.x.x` (e.g., `192.168.1.100.1.1`)
2. **AMS Routes**: You may need to add a route on your PLC to allow Home Assistant to connect
3. **Firewall**: Ensure UDP port 48899 and the configured AMS port (default 48898) are open

## Binary Sensor

Binary sensors represent boolean values from the PLC.

```yaml
binary_sensor:
  - platform: ads_custom
    adsvar: GVL.door_open
    name: Front Door
    device_class: door
    unique_id: ads_front_door
```

{% configuration %}
adsvar:
  description: The name of the ADS variable to monitor.
  required: true
  type: string
adstype:
  description: "The ADS variable type. Supported: `bool` (default), `real`."
  required: false
  type: string
  default: bool
name:
  description: Friendly name for the entity.
  required: false
  type: string
  default: "ADS binary sensor"
device_class:
  description: The device class for the binary sensor.
  required: false
  type: device_class
unique_id:
  description: Unique identifier for the entity.
  required: false
  type: string
{% endconfiguration %}

## Cover

Covers represent devices like blinds, shutters, or garage doors.

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

{% configuration %}
adsvar:
  description: Boolean variable indicating if the cover is closed.
  required: false
  type: string
adsvar_position:
  description: Variable for reading current position (0-100).
  required: false
  type: string
adsvar_position_type:
  description: "Data type for position variables: `byte` or `uint`."
  required: false
  type: string
  default: byte
adsvar_set_position:
  description: Variable for setting target position (0-100).
  required: false
  type: string
adsvar_open:
  description: Boolean variable to trigger open command.
  required: false
  type: string
adsvar_close:
  description: Boolean variable to trigger close command.
  required: false
  type: string
adsvar_stop:
  description: Boolean variable to trigger stop command.
  required: false
  type: string
inverted:
  description: Invert positioning logic (0=open, 100=closed).
  required: false
  type: boolean
  default: false
name:
  description: Friendly name for the entity.
  required: false
  type: string
  default: "ADS Cover"
device_class:
  description: The device class for the cover.
  required: false
  type: device_class
unique_id:
  description: Unique identifier for the entity.
  required: false
  type: string
{% endconfiguration %}

Note: Either `adsvar` or `adsvar_position` must be provided.

## Light

Lights support on/off control and optional brightness dimming.

### Simple On/Off Light

```yaml
light:
  - platform: ads_custom
    adsvar: GVL.light_enable
    name: Room Light
    unique_id: ads_room_light
```

### Dimmable Light

```yaml
light:
  - platform: ads_custom
    adsvar: GVL.light_enable
    adsvar_brightness: GVL.light_brightness
    adsvar_brightness_scale: 100
    name: Dimmable Light
    unique_id: ads_dimmable_light
```

{% configuration %}
adsvar:
  description: Boolean variable for the light's on/off state.
  required: true
  type: string
adsvar_brightness:
  description: Variable for the light's brightness level.
  required: false
  type: string
adsvar_brightness_type:
  description: "Data type for brightness: `byte` (0-255) or `uint` (0-65535)."
  required: false
  type: string
  default: byte
adsvar_brightness_scale:
  description: Maximum brightness value in PLC (e.g., 100 or 255).
  required: false
  type: integer
  default: 255
name:
  description: Friendly name for the entity.
  required: false
  type: string
  default: "ADS Light"
unique_id:
  description: Unique identifier for the entity.
  required: false
  type: string
{% endconfiguration %}

## Select

Select entities allow choosing from a predefined list of options.

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

{% configuration %}
adsvar:
  description: Integer variable storing the selected option index (0-based).
  required: true
  type: string
options:
  description: List of available options.
  required: true
  type: list
name:
  description: Friendly name for the entity.
  required: false
  type: string
  default: "ADS select"
unique_id:
  description: Unique identifier for the entity.
  required: false
  type: string
{% endconfiguration %}

## Sensor

Sensors read numeric or string values from the PLC.

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

{% configuration %}
adsvar:
  description: The name of the ADS variable to monitor.
  required: true
  type: string
adstype:
  description: "The PLC data type: `bool`, `byte`, `int`, `uint`, `sint`, `usint`, `dint`, `udint`, `word`, `dword`, `real`, `lreal`."
  required: false
  type: string
  default: int
adsfactor:
  description: Factor to divide the raw value by (for scaling).
  required: false
  type: integer
name:
  description: Friendly name for the entity.
  required: false
  type: string
  default: "ADS sensor"
unit_of_measurement:
  description: Unit of measurement (e.g., °C, %, kWh).
  required: false
  type: string
device_class:
  description: The device class for the sensor.
  required: false
  type: device_class
state_class:
  description: "The state class: `measurement`, `total`, `total_increasing`."
  required: false
  type: string
unique_id:
  description: Unique identifier for the entity.
  required: false
  type: string
{% endconfiguration %}

## Switch

Switches represent boolean on/off controls in the PLC.

```yaml
switch:
  - platform: ads_custom
    adsvar: GVL.pump
    name: Water Pump
    unique_id: ads_water_pump
```

{% configuration %}
adsvar:
  description: Boolean variable for the switch's on/off state.
  required: true
  type: string
name:
  description: Friendly name for the entity.
  required: false
  type: string
  default: "ADS Switch"
unique_id:
  description: Unique identifier for the entity.
  required: false
  type: string
{% endconfiguration %}

## Valve

Valves represent devices that can be opened and closed.

```yaml
valve:
  - platform: ads_custom
    adsvar: GVL.valve_open
    name: Water Valve
    device_class: water
    unique_id: ads_water_valve
```

{% configuration %}
adsvar:
  description: Boolean variable indicating if the valve is open.
  required: true
  type: string
name:
  description: Friendly name for the entity.
  required: false
  type: string
  default: "ADS valve"
device_class:
  description: The device class for the valve.
  required: false
  type: device_class
unique_id:
  description: Unique identifier for the entity.
  required: false
  type: string
{% endconfiguration %}

## Services

### Service `ads_custom.write_data_by_name`

Write a value to an ADS variable.

| Service Data Attribute | Optional | Description |
| ---------------------- | -------- | ----------- |
| `adsvar` | no | Name of the ADS variable (e.g., `GVL.setpoint`) |
| `adstype` | no | Data type of the variable (e.g., `int`, `bool`, `real`) |
| `value` | no | Value to write |

#### Example

```yaml
service: ads_custom.write_data_by_name
data:
  adsvar: "GVL.setpoint"
  adstype: "int"
  value: 100
```

## Unique IDs and UI Customization

All entity types support the `unique_id` parameter. When a unique ID is configured, you can:

- Customize the entity from the Home Assistant UI
- Change the device class without editing YAML
- Modify the entity ID
- Disable/enable entities
- Customize icons and other properties

To enable UI customization, simply add a `unique_id` to your entity configuration:

```yaml
sensor:
  - platform: ads_custom
    adsvar: GVL.temperature
    name: Room Temperature
    unique_id: ads_room_temp  # Enables UI customization
```

## Supported Data Types

The integration supports the following ADS/PLC data types:

| Type | Description | Size |
| ---- | ----------- | ---- |
| `bool` | Boolean | 1 bit |
| `byte` | Byte | 8 bits |
| `int` | Integer | 16 bits |
| `uint` | Unsigned Integer | 16 bits |
| `sint` | Short Integer | 8 bits |
| `usint` | Unsigned Short Integer | 8 bits |
| `dint` | Double Integer | 32 bits |
| `udint` | Unsigned Double Integer | 32 bits |
| `word` | Word | 16 bits |
| `dword` | Double Word | 32 bits |
| `real` | Real | 32-bit float |
| `lreal` | Long Real | 64-bit float |

## Examples

For complete working examples, see the [example configuration file](https://github.com/Aaroneisele55/homeassistant-ads/blob/main/example_configuration.yaml) in the repository.

For detailed parameter documentation, see the [Entity Parameters Reference](https://github.com/Aaroneisele55/homeassistant-ads/blob/main/ENTITY_PARAMETERS.md).

## Troubleshooting

### Cannot Connect

- Verify the AMS Net ID is correct
- Check that the IP address is reachable
- Ensure AMS routes are properly configured on the PLC
- Check firewall settings (UDP port 48899 and AMS port)

### Connection Drops

- Check network stability
- Verify PLC is not overloaded
- Check TwinCAT system status

### Entities Don't Appear

- Check your YAML configuration for syntax errors
- Verify the ADS variable names are correct (case-sensitive)
- Check the Home Assistant logs for error messages
- Restart Home Assistant after making YAML changes

### Variables Not Updating

- Verify the PLC variable exists and is accessible
- Check that the data type matches the PLC variable type
- Ensure AMS routes are bidirectional
- Check Home Assistant logs for notification errors
