# ADS Custom - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A custom Home Assistant integration for Beckhoff's **ADS (Automation Device Specification)** protocol, enabling real-time communication with TwinCAT PLCs and other Beckhoff automation devices.

> **Note:** This is a custom integration with domain `ads_custom` to prevent conflicts with Home Assistant's core ADS integration. You can configure it fully via **UI** (connection + entities) or **YAML** - your choice!

## Documentation

📖 **[Complete Integration Documentation](docs/index.md)** - Full documentation in official Home Assistant style

📋 **[Entity Parameters Reference](ENTITY_PARAMETERS.md)** - Detailed parameter reference for all entity types

💡 **[Example Configuration](example_configuration.yaml)** - Working YAML examples

🖥️ **[UI Configuration Guide](docs/UI_CONFIGURATION.md)** - Setup via Home Assistant UI

## Features

- ✅ **Real-time push notifications** from PLC to Home Assistant
- ✅ **Seven entity types**: Binary Sensor, Cover, Light, Select, Sensor, Switch, Valve
- ✅ **All PLC data types** supported (BOOL, INT, REAL, etc.)
- ✅ **Custom brightness scaling** for lights (0-100 or 0-255)
- ✅ **Unique ID support** for UI customization
- ✅ **Service calls** to write PLC variables
- ✅ **Full UI or YAML configuration** - connection AND entities!

## Quick Start

### Installation

#### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots menu → "Custom repositories"
4. Add this repository URL and select "Integration" as category
5. Click "Install"
6. Restart Home Assistant

#### Manual Installation

1. Copy `custom_components/ads_custom` to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

### Configuration

You have **three options** for configuring the ADS integration:

#### Option 1: Full UI Configuration (Easiest)

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **ADS Custom**
4. Follow the setup wizard for the connection
5. Click **Configure** → **Add Entity** to add sensors, switches, lights, etc.
6. No YAML editing or restarts needed!

#### Option 2: Full YAML Configuration (Power Users)

Add everything to your `configuration.yaml`:

```yaml
# ADS connection
ads_custom:
  device: "192.168.1.100.1.1"  # AMS Net ID
  ip_address: "192.168.1.100"  # IP address

# Entities
sensor:
  - platform: ads_custom
    adsvar: GVL.temperature
    name: Room Temperature
    adstype: real
    unit_of_measurement: "°C"
    device_class: temperature

switch:
  - platform: ads_custom
    adsvar: GVL.pump
    name: Water Pump
```

#### Option 3: Mixed Configuration (Flexible)

- **UI for connection** + **YAML for entities**, OR
- **YAML for connection** + **UI for entities**

Choose the best method for each part!

See [complete documentation](docs/index.md) for all configuration options and entity types.

## Supported Entity Types

| Entity Type | Description | Example Use Case |
|------------|-------------|------------------|
| **Binary Sensor** | Boolean states | Doors, motion detectors, limit switches |
| **Cover** | Position-controllable devices | Blinds, shutters, garage doors |
| **Light** | On/off and dimmable lights | Room lights with brightness control |
| **Select** | Multiple choice options | Operation modes, preset selections |
| **Sensor** | Numeric/string values | Temperature, pressure, counters |
| **Switch** | Boolean controls | Pumps, fans, relays |
| **Valve** | Open/close valves | Water valves, gas valves |

## Why Use ADS Custom?

### vs. Core ADS Integration

- **Native BYTE brightness** support for Beckhoff lights (0-100 range)
- **No template workarounds** needed (one entity instead of 4)
- **Simpler configuration** (up to 80% fewer lines)
- **Better performance** (no template evaluation overhead)

### Example: Dimmable Light

**Core ADS + Templates (4 entities):**
```yaml
sensor:
  - platform: ads
    name: Light_Brightness
    adsvar: .Light.Brightness
binary_sensor:
  - platform: ads
    name: Light_State
    adsvar: .Light.Enable
switch:
  - platform: ads
    name: Light_Switch
    adsvar: .Light.Enable
template:
  - light:
      name: My Light
      # ... complex template code ...
```

**ADS Custom (1 entity):**
```yaml
light:
  - platform: ads_custom
    name: My Light
    adsvar: .Light.Enable
    adsvar_brightness: .Light.Brightness
    adsvar_brightness_scale: 100
```

## Requirements

- Home Assistant 2024.1.0 or newer
- TwinCAT 2 or TwinCAT 3 PLC
- Network access to the ADS device
- Properly configured AMS routes on the PLC

## Support

- 📖 [Documentation](docs/index.md)
- 🐛 [Report Issues](https://github.com/Aaroneisele55/homeassistant-ads/issues)
- 💬 [Home Assistant Community](https://community.home-assistant.io/)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This integration is released under the Apache License 2.0.

## Credits

- Original integration by [@mrpasztoradam](https://github.com/mrpasztoradam)
- Uses the [pyads](https://github.com/stlehmann/pyads) library for ADS communication
