# ADS Custom - Automation Device Specification Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

This is a custom Home Assistant integration for Beckhoff's ADS (Automation Device Specification) protocol, which allows communication with TwinCAT PLCs and other Beckhoff automation devices.

**Note:** This is a custom integration with a different domain (`ads_custom`) to prevent conflicts with Home Assistant's core ADS integration. This version is **completely YAML-based** for maximum transparency and version control.

## Features

- **100% YAML-based configuration** - No UI, pure configuration.yaml
- Connect to ADS/AMS devices over the network
- Support for multiple entity types:
  - Binary Sensors
  - Covers
  - Lights (with BYTE/UINT brightness support and custom scaling)
  - Select entities
  - Sensors
  - Switches
  - Valves
- Write data to ADS variables via service calls
- Real-time push notifications from PLC to Home Assistant
- Support for all common PLC data types
- Unique ID support for all entity types
- Perfect for version control and automation

## Migrating from Core ADS or Template Lights

If you're currently using the core Home Assistant ADS integration or a template-based workaround for dimmable lights with BYTE brightness (0-100 range), this integration provides **native support** that eliminates the need for multiple helper entities.

### What's Different?

✅ **Native BYTE brightness support** - Direct support for Beckhoff lights using 0-100 brightness range
✅ **No template workarounds needed** - One light entity instead of 4 (sensor + binary_sensor + switch + template)
✅ **Simpler configuration** - Up to 80% fewer lines of YAML configuration
✅ **Better performance** - No template evaluation overhead

### Migration Resources

- **[USER_MIGRATION_GUIDE.md](USER_MIGRATION_GUIDE.md)** - Complete step-by-step migration guide
- **[OLD_VS_NEW_COMPARISON.md](OLD_VS_NEW_COMPARISON.md)** - Side-by-side comparison of old vs new approach
- **[CONVERTED_USER_CONFIG.yaml](CONVERTED_USER_CONFIG.yaml)** - Real-world example of a converted configuration

### Quick Example

**Old approach (4 entities per dimmable light):**
```yaml
sensor:
  - platform: ads
    name: "Light_Brightness"
    adsvar: ".Light.Brightness"
binary_sensor:
  - platform: ads
    name: "Light_State"
    adsvar: ".Light.Enable"
switch:
  - platform: ads
    name: "Light_Switch"
    adsvar: ".Light.Enable"
template:
  - light:
      name: "My Light"
      state: "{{ is_state('binary_sensor.Light_State', 'on') }}"
      # ... complex template code ...
```

**New approach (1 entity per light):**
```yaml
light:
  - platform: ads_custom
    name: "My Light"
    adsvar: ".Light.Enable"
    adsvar_brightness: ".Light.Brightness"
    adsvar_brightness_scale: 100
    adsvar_brightness_type: byte
```

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL and select "Integration" as the category
6. Click "Install"
7. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/ads_custom` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

### Complete YAML Configuration

All configuration must be done in your `configuration.yaml` file. There is no UI configuration available.

**Step 1: Configure the ADS Connection**

Add the ADS connection to your `configuration.yaml`:

```yaml
ads_custom:
  device: '192.168.1.100.1.1'  # AMS Net ID of your ADS device (required)
  ip_address: '192.168.1.100'  # IP address of your ADS device (optional)
  port: 48898                  # AMS port number (optional, default: 48898)
```

**Step 2: Add Entities**

Configure your ADS entities in your `configuration.yaml` or in separate platform configuration files.

### Example Sensor Configuration

```yaml
sensor:
  - platform: ads_custom
    adsvar: GVL.temperature
    name: Room Temperature
    adstype: int
    unit_of_measurement: '°C'
    unique_id: ads_room_temp
```

### Example Switch Configuration

```yaml
switch:
  - platform: ads_custom
    adsvar: GVL.light_switch
    name: Room Light
    unique_id: ads_room_light
```

### Example Light Configuration

```yaml
light:
  - platform: ads_custom
    adsvar: GVL.light_enable
    adsvar_brightness: GVL.light_brightness
    name: Dimmable Light
    unique_id: ads_dimmable_light
```

For Beckhoff lights that use 0-100 range instead of 0-255:

```yaml
light:
  - platform: ads_custom
    adsvar: GVL.light_enable
    adsvar_brightness: GVL.light_brightness
    adsvar_brightness_scale: 100
    name: Beckhoff Light
    unique_id: ads_beckhoff_light
```

For lights using BYTE data type (default) or UINT:

```yaml
light:
  - platform: ads_custom
    adsvar: GVL.light_enable
    adsvar_brightness: GVL.light_brightness
    adsvar_brightness_type: byte  # or "uint" - defaults to "byte"
    adsvar_brightness_scale: 100
    name: Beckhoff Light BYTE
    unique_id: ads_beckhoff_light_byte
```

### Example Binary Sensor Configuration

```yaml
binary_sensor:
  - platform: ads_custom
    adsvar: GVL.door_open
    name: Front Door
    device_class: door
    unique_id: ads_front_door
```

### Example Cover Configuration

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

### Example Valve Configuration

```yaml
valve:
  - platform: ads_custom
    adsvar: GVL.valve_open
    name: Water Valve
    device_class: water
    unique_id: ads_water_valve
```

### Example Select Configuration

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

## Services

### `ads_custom.write_data_by_name`

Write a value to an ADS variable.

**Service Data:**

| Field | Description | Example |
|-------|-------------|---------|
| `adsvar` | The name of the ADS variable | `GVL.setpoint` |
| `adstype` | The data type of the variable | `int`, `bool`, `real`, etc. |
| `value` | The value to write | `100` |

**Example:**

```yaml
service: ads_custom.write_data_by_name
data:
  adsvar: 'GVL.setpoint'
  adstype: 'int'
  value: 100
```

## Supported Data Types

The integration supports the following ADS/PLC data types:

- `bool` - Boolean
- `byte` - Byte
- `int` - Integer (16-bit)
- `uint` - Unsigned Integer (16-bit)
- `sint` - Short Integer (8-bit)
- `usint` - Unsigned Short Integer (8-bit)
- `dint` - Double Integer (32-bit)
- `udint` - Unsigned Double Integer (32-bit)
- `word` - Word (16-bit)
- `dword` - Double Word (32-bit)
- `real` - Real (32-bit float)
- `lreal` - Long Real (64-bit float)
- `string` - String
- `time` - Time
- `date` - Date
- `dt` - Date and Time
- `tod` - Time of Day

## Requirements

- Home Assistant 2024.1.0 or newer
- TwinCAT 2 or TwinCAT 3 PLC
- Network access to the ADS device
- Properly configured AMS routes on the PLC

## Setup Notes

1. **AMS Net ID**: This is a unique identifier for each ADS device, typically in the format `x.x.x.x.x.x` (e.g., `192.168.1.100.1.1`)
2. **AMS Routes**: You may need to add a route on your PLC to allow Home Assistant to connect
3. **Firewall**: Ensure UDP port 48899 and the configured AMS port (default 48898) are open

## Troubleshooting

### Cannot Connect

- Verify the AMS Net ID is correct
- Check that the IP address is reachable
- Ensure AMS routes are properly configured on the PLC
- Check firewall settings

### Connection Drops

- Check network stability
- Verify PLC is not overloaded
- Check TwinCAT system status

### Entities don't appear

- Check your YAML configuration for syntax errors
- Verify the ADS variable names are correct
- Check the Home Assistant logs for error messages
- Restart Home Assistant after making YAML changes

## Contributing

This integration is part of the Home Assistant core. Contributions are welcome!

## License

This integration is released under the Apache License 2.0.

## Credits

- Original integration by [@mrpasztoradam](https://github.com/mrpasztoradam)
- Uses the [pyads](https://github.com/stlehmann/pyads) library

## Support

For issues and questions:
- [Home Assistant Community Forum](https://community.home-assistant.io/)
- [GitHub Issues](https://github.com/home-assistant/core/issues)
