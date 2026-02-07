# ADS Custom - Automation Device Specification Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

This is a custom Home Assistant integration for Beckhoff's ADS (Automation Device Specification) protocol, which allows communication with TwinCAT PLCs and other Beckhoff automation devices.

**Note:** This is a custom integration with a different domain (`ads_custom`) to prevent conflicts with Home Assistant's core ADS integration. Use this version if you need UI-based configuration or additional features.

## Features

- UI-based configuration (no YAML required for connection setup)
- Connect to ADS/AMS devices over the network
- Support for multiple entity types:
  - Binary Sensors
  - Covers
  - Lights
  - Select entities
  - Sensors
  - Switches
  - Valves
- Write data to ADS variables via service calls
- Real-time push notifications from PLC to Home Assistant
- Support for all common PLC data types
- Unique ID support for all entity types

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

### Step 1: Set up the ADS Connection (UI Only)

1. Go to Settings → Devices & Services
2. Click "+ ADD INTEGRATION"
3. Search for "ADS Custom"
4. Enter your ADS device information:
   - **AMS Net ID**: The AMS Net ID of your ADS device (e.g., `192.168.1.100.1.1`)
   - **IP Address**: (Optional) The IP address of your ADS device
   - **AMS Port**: The AMS port number (default: `48898`)

### Step 2: Configure Entities (YAML)

After setting up the ADS connection via UI, configure individual entities for each platform in your `configuration.yaml`:

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
