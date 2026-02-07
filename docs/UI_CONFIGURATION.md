# UI Configuration Support

## Overview

This integration now supports **both UI and YAML-based configuration**. You can choose to configure your ADS connection using **either method** - whichever you prefer!

- **UI Configuration**: Easy, guided setup through the Home Assistant interface
- **YAML Configuration**: Traditional configuration file approach for power users

**Important**: Choose one method for your connection configuration. You don't need to use both.

## UI Configuration

### Adding an ADS Integration via UI

1. Navigate to **Settings** → **Devices & Services**
2. Click the **+ Add Integration** button
3. Search for **ADS Custom**
4. Fill in the configuration form:
   - **AMS Net ID**: The AMS Net ID of your ADS device (e.g., `192.168.1.100.1.1`)
   - **IP Address (optional)**: The IP address of your ADS device (can be omitted if routing is configured)
   - **AMS Port**: The AMS port number (default: `48898`)
5. Click **Submit**
6. The integration will test the connection and add the device if successful

### Configuration Fields

#### AMS Net ID (Required)
The AMS Net ID uniquely identifies your TwinCAT device on the network. Format: `xxx.xxx.xxx.xxx.x.x`

**Example:** `192.168.1.100.1.1`

#### IP Address (Optional)
The IP address of your ADS device. This can be omitted if you have AMS routing configured on your network.

**Example:** `192.168.1.100`

#### AMS Port (Optional)
The AMS port number used for communication. Default is `48898` (standard TwinCAT runtime port).

**Common ports:**
- `48898` - TwinCAT 2 Runtime
- `851` - TwinCAT 3 Runtime (Port 1)

### Error Messages

- **Cannot connect**: The integration could not establish a connection to the ADS device. Check:
  - The AMS Net ID is correct
  - The IP address is reachable
  - The device is running and ADS is enabled
  - Firewall rules allow ADS communication (port 48898)
  
- **Already configured**: This device is already configured in Home Assistant

## YAML Configuration (Alternative Method)

If you prefer the traditional YAML approach, you can configure the connection in your `configuration.yaml` instead of using the UI:

```yaml
ads_custom:
  device: '192.168.1.100.1.1'
  ip_address: '192.168.1.100'  # Optional
  port: 48898                   # Optional, default: 48898
```

**Note**: If you configure via YAML, you don't need to add the integration via UI. Choose one method or the other.

## Which Method Should I Use?

### Use UI Configuration If:
- ✅ You prefer a guided setup experience
- ✅ You want immediate connection validation
- ✅ You're less comfortable editing YAML files
- ✅ You want to manage configuration through the Home Assistant interface

### Use YAML Configuration If:
- ✅ You prefer infrastructure-as-code approach
- ✅ You want version control for your configuration
- ✅ You're managing multiple Home Assistant instances
- ✅ You're comfortable with YAML syntax

**Both methods are equally supported and functional!**

## Entity Configuration

**Important Note**: Regardless of which connection method you choose (UI or YAML), all **entity configurations** (sensors, switches, lights, etc.) must still be defined in YAML. The UI configuration only handles the ADS connection itself.

### Example: Complete Setup

#### Option 1: UI Connection
1. Add connection via UI (Settings → Devices & Services → Add Integration → ADS Custom)
2. Configure entities in `configuration.yaml`:

```yaml
sensor:
  - platform: ads_custom
    adsvar: GVL.temperature
    name: Room Temperature
    adstype: real
    unit_of_measurement: '°C'
    device_class: temperature

switch:
  - platform: ads_custom
    adsvar: GVL.pump
    name: Water Pump
```

#### Option 2: YAML Connection
Configure everything in `configuration.yaml`:

```yaml
# Connection
ads_custom:
  device: '192.168.1.100.1.1'
  ip_address: '192.168.1.100'
  port: 48898

# Entities
sensor:
  - platform: ads_custom
    adsvar: GVL.temperature
    name: Room Temperature
    adstype: real
    unit_of_measurement: '°C'
    device_class: temperature

switch:
  - platform: ads_custom
    adsvar: GVL.pump
    name: Water Pump
```

## Switching Between Methods

If you want to switch from one method to another:

### From YAML to UI

1. **Remove** the `ads_custom:` section from your `configuration.yaml`
2. **Keep** all entity configurations (sensors, switches, etc.)
3. **Restart** Home Assistant
4. **Add** the integration via UI (Settings → Devices & Services)
5. Entities will automatically connect to the new UI-configured connection

### From UI to YAML

1. **Remove** the integration from UI (Settings → Devices & Services → ADS Custom → Delete)
2. **Add** the `ads_custom:` section to your `configuration.yaml`
3. **Keep** all entity configurations (sensors, switches, etc.)
4. **Restart** Home Assistant
5. Entities will automatically connect to the YAML-configured connection

## Benefits of Each Method

### UI Configuration Benefits
- ✅ **Easier setup** - No need to edit YAML files
- ✅ **Connection validation** - Immediate feedback if connection fails
- ✅ **Guided experience** - Step-by-step configuration
- ✅ **User-friendly** - Perfect for beginners

### YAML Configuration Benefits
- ✅ **Version control** - Track changes with git
- ✅ **Infrastructure as code** - Declarative configuration
- ✅ **Backup and restore** - Easy to copy configuration
- ✅ **Documentation** - Self-documenting setup

## Backward Compatibility

- ✅ Existing YAML configurations continue to work without any changes
- ✅ No breaking changes to the integration
- ✅ All entity types work with both configuration methods
- ✅ Services work with both configuration methods
- ✅ You can switch between methods at any time
