# Entity Reconfiguration Guide

This guide explains how to edit ADS entity properties after creation, similar to how Template entities work in Home Assistant.

## Overview

When you create ADS entities through the Home Assistant UI (not YAML), each entity can be reconfigured later to change its:
- ADS variable name
- Entity name
- Data types
- Device classes
- Units of measurement
- And other entity-specific properties

## How to Reconfigure an Entity

### Step 1: Navigate to the Entity

1. Go to **Settings** → **Devices & Services** → **Entities** tab
2. Find your ADS entity in the list (you can use the search box)
3. Click on the entity name to open its details page

### Step 2: Open Entity Settings

1. On the entity details page, click the **cogwheel icon** (⚙️) in the top right corner
2. This opens the entity settings menu

### Step 3: Access Reconfigure

1. In the entity settings menu, select **"Reconfigure"**
2. This opens the reconfiguration dialog for your entity type

### Step 4: Edit Properties

The reconfiguration form shows all editable properties for your entity type:

#### Switch Entities
- ADS Variable Name
- Entity Name

#### Sensor Entities
- ADS Variable Name
- Entity Name
- Data Type (int, real, bool, etc.)
- Unit of Measurement
- Device Class
- State Class

#### Binary Sensor Entities
- ADS Variable Name
- Entity Name
- Data Type (bool or real)
- Device Class

#### Light Entities
- ADS Variable Name (On/Off)
- Entity Name
- Brightness Variable (optional)
- Brightness Data Type (byte or uint)
- Brightness Scale (e.g., 255 or 100)

#### Cover Entities
- Closed State Variable
- Position Variable
- Set Position Variable
- Open Command Variable
- Close Command Variable
- Stop Command Variable
- Position Data Type
- Inverted Positioning
- Device Class

#### Valve Entities
- ADS Variable Name
- Entity Name
- Device Class

#### Select Entities
- ADS Variable Name
- Entity Name
- Options (comma-separated)

### Step 5: Save Changes

1. After editing the properties, click **"Submit"** or **"Save"**
2. The entity will be updated with the new configuration
3. The entity's state will automatically refresh with data from the new PLC variable

## Important Notes

### UI-Created Entities Only

**The reconfigure feature only works for entities created through the Home Assistant UI.**

Entities created via YAML configuration do NOT support reconfiguration. If you have YAML entities and want to edit them:

1. Remove the entity from your `configuration.yaml`
2. Restart Home Assistant
3. Recreate the entity using the UI (Settings → Devices & Services → ADS Custom → Add Entity)

### Home Assistant Version Requirements

This feature requires **Home Assistant 2025.7.0 or later**. The reconfigure option will not appear in older versions.

### Entity ID and Area

To change the **Entity ID** or assign the entity to an **Area**, use the standard entity settings (the same cogwheel menu, but select the entity ID/area fields instead of "Reconfigure").

### Device Registry

Each UI-created ADS entity is registered as its own device in Home Assistant's device registry. This allows for better organization and enables the reconfigure feature.

## Troubleshooting

### "Reconfigure" option doesn't appear

**Possible causes:**

1. **Entity was created from YAML**
   - Solution: Delete the YAML configuration and recreate the entity via UI

2. **Home Assistant version is too old**
   - Solution: Upgrade to Home Assistant 2025.7.0 or later

3. **Entity doesn't have a unique_id**
   - This shouldn't happen for UI-created entities, but if it does:
   - Solution: Delete and recreate the entity

4. **Integration needs to be reloaded**
   - Solution: Go to Settings → Devices & Services → ADS Custom → three-dot menu → Reload

### Changes don't take effect

After reconfiguring an entity:

1. The entity state should update automatically within a few seconds
2. If not, try reloading the integration
3. Check the Home Assistant logs for any connection errors to the PLC

### Can't change entity type

You cannot change an entity's type (e.g., switch to sensor) through reconfiguration. To change the type:

1. Delete the existing entity
2. Create a new entity with the desired type

## Alternative: Managing Entities from Integration Page

You can also access entity management from the integration configuration page:

1. Go to **Settings** → **Devices & Services**
2. Find the **ADS Custom** integration
3. Click on it to see all subentries (entities)
4. Click on any entity subentry to reconfigure it
5. Or click **"Add Entity"** to create new entities

Both methods (entity settings or integration page) provide the same reconfigure functionality.

## Examples

### Example 1: Changing Variable Name

You've renamed a PLC variable from `GVL.oldPump` to `GVL.newPump`:

1. Find the entity in the Entities list
2. Click cogwheel → Reconfigure
3. Change "ADS Variable Name" from `GVL.oldPump` to `GVL.newPump`
4. Click Submit
5. The entity now reads from the new variable

### Example 2: Adding a Unit to a Sensor

You initially created a sensor without a unit, and now want to add "°C":

1. Find the sensor in the Entities list
2. Click cogwheel → Reconfigure
3. In "Unit of Measurement", enter `°C`
4. Click Submit
5. The sensor now displays temperature with the unit

### Example 3: Changing Device Class

You want to change a binary sensor from "door" to "window":

1. Find the binary sensor in the Entities list
2. Click cogwheel → Reconfigure
3. In "Device Class", select "window"
4. Click Submit
5. The icon and behavior now reflect a window sensor

## See Also

- [Entity Parameters Reference](../ENTITY_PARAMETERS.md) - Complete list of all entity parameters
- [Example Configuration](../example_configuration.yaml) - YAML configuration examples
- [Testing Guide](../TESTING_GUIDE.md) - How to test the integration
