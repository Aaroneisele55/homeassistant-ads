# UI Configuration Support

## Overview

This integration now supports **full UI-based configuration**, allowing you to configure both the ADS connection AND entities through the Home Assistant interface. You can also choose the traditional YAML approach if you prefer.

- **UI Configuration**: Easy, guided setup through the Home Assistant interface for connection AND entities
- **YAML Configuration**: Traditional configuration file approach for power users

**You can choose:** Configure everything via UI, everything via YAML, or mix both methods (UI for connection, YAML for entities, or vice versa).

## UI Configuration

### Step 1: Adding the ADS Connection via UI

1. Navigate to **Settings** → **Devices & Services**
2. Click the **+ Add Integration** button
3. Search for **ADS Custom**
4. Fill in the configuration form:
   - **AMS Net ID**: The AMS Net ID of your ADS device (e.g., `192.168.1.100.1.1`)
   - **IP Address (optional)**: The IP address of your ADS device (can be omitted if routing is configured)
   - **AMS Port**: The AMS port number (default: `48898`)
5. Click **Submit**
6. The integration will test the connection and add the device if successful

### Step 2: Adding Entities via UI

After setting up the connection, you can add entities:

1. Go to **Settings** → **Devices & Services**
2. Find your **ADS Custom** integration
3. Click **Configure** or the three-dot menu → **Options**
4. Select **Add Entity**
5. Choose the entity type (Switch, Sensor, Binary Sensor, or Light)
6. Fill in the entity configuration:
   - **ADS Variable Name**: The PLC variable (e.g., `GVL.pump`)
   - **Entity Name**: Friendly name for Home Assistant
   - Additional parameters specific to the entity type
7. Click **Submit**
8. The entity will be created immediately (no restart required)

### Supported Entity Types in UI

- ✅ **Switch** - On/off controls for boolean PLC variables
- ✅ **Sensor** - Read numeric or string values from PLC
- ✅ **Binary Sensor** - On/off states from boolean or REAL variables
- ✅ **Light** - On/off and dimmable lights with brightness control
- ⏳ **Cover, Valve, Select** - Coming soon (use YAML for now)

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

### Use Full UI Configuration If:
- ✅ You prefer a fully guided setup experience
- ✅ You want immediate connection validation
- ✅ You're less comfortable editing YAML files
- ✅ You want to manage everything through the Home Assistant interface
- ✅ You want to add/modify entities without restarting Home Assistant

### Use Full YAML Configuration If:
- ✅ You prefer infrastructure-as-code approach
- ✅ You want version control for your entire configuration
- ✅ You're managing multiple Home Assistant instances
- ✅ You're comfortable with YAML syntax
- ✅ You need advanced entity types (Cover, Valve, Select)

### Mix Both Methods:
- ✅ UI for connection, YAML for entities (simple connection setup, advanced entity control)
- ✅ YAML for connection, UI for entities (version-controlled connection, easy entity management)

**All methods are equally supported and functional!**

## Configuration Examples

### Example 1: Full UI Configuration

1. **Add connection via UI:**
   - Settings → Devices & Services → Add Integration → ADS Custom
   - Enter Net ID: `192.168.1.100.1.1`, IP: `192.168.1.100`

2. **Add entities via UI:**
   - Configure → Add Entity → Sensor
   - Variable: `GVL.temperature`, Name: `Room Temperature`
   - Data Type: `real`, Unit: `°C`, Device Class: `temperature`

No YAML configuration needed!

### Example 2: Full YAML Configuration

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

### Example 3: Mixed Configuration (UI Connection + YAML Entities)

1. **Add connection via UI** (Settings → Devices & Services)

2. **Add entities in configuration.yaml:**

```yaml
sensor:
  - platform: ads_custom
    adsvar: GVL.temperature
    name: Room Temperature
    adstype: real
    unit_of_measurement: '°C'

switch:
  - platform: ads_custom
    adsvar: GVL.pump
    name: Water Pump
```

### Example 4: Mixed Configuration (YAML Connection + UI Entities)

1. **Add connection in configuration.yaml:**

```yaml
ads_custom:
  device: '192.168.1.100.1.1'
  ip_address: '192.168.1.100'
```

2. **Add entities via UI** (Configure → Add Entity)

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

### Full UI Configuration Benefits
- ✅ **No YAML editing** - Everything through the interface
- ✅ **No restarts needed** - Add/modify entities on the fly
- ✅ **Connection validation** - Immediate feedback
- ✅ **Guided experience** - Step-by-step for each entity type
- ✅ **User-friendly** - Perfect for beginners

### Full YAML Configuration Benefits
- ✅ **Version control** - Track all changes with git
- ✅ **Infrastructure as code** - Declarative configuration
- ✅ **Backup and restore** - Easy to copy entire setup
- ✅ **Documentation** - Self-documenting configuration
- ✅ **Advanced entities** - Access to all entity types and parameters

### Mixed Configuration Benefits
- ✅ **Best of both worlds** - Simple connection setup + flexible entity management
- ✅ **Flexibility** - Choose the best method for each task
- ✅ **Migration path** - Gradually move between methods

## Backward Compatibility

- ✅ Existing YAML configurations continue to work without any changes
- ✅ No breaking changes to the integration
- ✅ All entity types work with both configuration methods
- ✅ Services work with both configuration methods
- ✅ You can switch between methods at any time
