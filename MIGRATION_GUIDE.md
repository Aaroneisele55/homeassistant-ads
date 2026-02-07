# Migration Guide: Version 1.x to 2.0

## Overview

Version 2.0 of the ADS Custom integration is a **major breaking change** that removes all UI configuration in favor of a pure YAML-based approach. This guide will help you migrate from version 1.x to 2.0.

## What Changed?

### Version 1.x (Old)
- UI-based entity configuration through Settings → Devices & Services
- Optional YAML configuration for entities
- Config flow for both connection and entity management
- Mixed configuration approach

### Version 2.0 (New)
- **100% YAML-based** configuration
- No UI configuration at all
- All entities defined in `configuration.yaml`
- Pure configuration-as-code approach

## Migration Steps

### Step 1: Document Your Current Configuration

Before upgrading, document all your entities configured through the UI:

1. Go to Settings → Devices & Services
2. Find your ADS Custom integration
3. Click "Configure"
4. For each entity, note down:
   - Entity type (sensor, switch, light, etc.)
   - Entity name
   - ADS variable (adsvar)
   - Any additional settings (brightness variables, device class, etc.)

### Step 2: Prepare Your YAML Configuration

Create your YAML configuration based on your documented entities.

**Basic Template:**

```yaml
ads_custom:
  device: 'YOUR_AMS_NET_ID'     # e.g., '192.168.1.100.1.1'
  ip_address: 'YOUR_IP'          # e.g., '192.168.1.100'
  port: 48898                    # Optional, default is 48898

# Add your entities below
sensor:
  - platform: ads_custom
    adsvar: GVL.your_variable
    name: Your Sensor Name
    unique_id: ads_your_sensor

switch:
  - platform: ads_custom
    adsvar: GVL.your_switch
    name: Your Switch Name
    unique_id: ads_your_switch

# Add more entities as needed
```

### Step 3: Install Version 2.0

1. **Backup your Home Assistant configuration** before proceeding
2. Update the ADS Custom integration to version 2.0 via HACS or manual installation
3. **Do not restart yet**

### Step 4: Add YAML Configuration

1. Open your `configuration.yaml` file
2. Add the `ads_custom:` connection block at the top level
3. Add all your entity configurations under their respective platforms
4. Save the file
5. Check configuration validity: Developer Tools → YAML → Check Configuration

### Step 5: Remove Old Integration Instance

1. Go to Settings → Devices & Services
2. Find the old ADS Custom integration instance (if it exists)
3. Click the three dots → Delete
4. Confirm deletion

### Step 6: Restart Home Assistant

Restart Home Assistant to load the new YAML configuration.

### Step 7: Verify Everything Works

1. Check that all entities are present in Home Assistant
2. Verify entity states are updating correctly
3. Test controlling entities (switches, lights, etc.)
4. Check the logs for any errors

## Example Migration

### Before (UI Configuration in Version 1.x)

You had these entities configured through the UI:
- Temperature sensor reading from `GVL.temperature`
- Light switch controlling `GVL.room_light`
- Dimmable light with brightness at `GVL.dimmer_brightness`

### After (YAML Configuration in Version 2.0)

```yaml
ads_custom:
  device: '192.168.1.100.1.1'
  ip_address: '192.168.1.100'
  port: 48898

sensor:
  - platform: ads_custom
    adsvar: GVL.temperature
    name: Temperature Sensor
    adstype: real
    unit_of_measurement: '°C'
    device_class: temperature
    state_class: measurement
    unique_id: ads_temperature_sensor

switch:
  - platform: ads_custom
    adsvar: GVL.room_light
    name: Room Light
    unique_id: ads_room_light

light:
  - platform: ads_custom
    adsvar: GVL.room_light
    adsvar_brightness: GVL.dimmer_brightness
    adsvar_brightness_scale: 255
    adsvar_brightness_type: byte
    name: Dimmable Light
    unique_id: ads_dimmable_light
```

## Common Issues and Solutions

### Issue: Integration doesn't load after upgrade

**Solution:** Make sure you have added the `ads_custom:` block to your `configuration.yaml`. Check the Home Assistant logs for specific error messages.

### Issue: Entities are missing

**Solution:** Verify that all entities are properly defined in YAML with correct platform names and syntax. Use the example configuration as a template.

### Issue: Cannot connect to PLC

**Solution:** Verify that your `device`, `ip_address`, and `port` settings are correct in the `ads_custom:` block.

### Issue: Unique IDs conflict

**Solution:** If you had entities with the same unique_id in the UI configuration, you may need to manually remove them from `.storage/core.entity_registry` or use the Home Assistant UI to remove old entities.

### Issue: Entity states not updating

**Solution:** 
1. Check that the ADS variable names (`adsvar`) are correct
2. Verify the PLC is running and reachable
3. Check Home Assistant logs for connection errors

## Rollback (If Needed)

If you need to rollback to version 1.x:

1. **Stop Home Assistant**
2. Restore your backup configuration
3. Downgrade the integration to version 1.x via HACS or manual installation
4. Restart Home Assistant
5. Reconfigure entities through the UI

**Note:** It's highly recommended to test version 2.0 in a non-production environment first.

## Benefits of Version 2.0

Despite being a breaking change, version 2.0 offers several advantages:

1. **Version Control** - Your entire ADS configuration can be tracked in Git
2. **Transparency** - All entities visible at a glance in YAML
3. **Bulk Management** - Easy to add/modify many entities at once
4. **Automation** - Configuration can be generated programmatically
5. **Portability** - Easy to backup and restore
6. **Simplicity** - Simpler codebase, fewer bugs
7. **Professional** - Industry-standard configuration-as-code approach

## Getting Help

If you encounter issues during migration:

1. Check the Home Assistant logs (`configuration.yaml` → Check Configuration)
2. Review the [example_configuration.yaml](example_configuration.yaml) file
3. Consult the [README.md](README.md) for detailed configuration examples
4. Open an issue on GitHub with:
   - Your sanitized YAML configuration
   - Relevant log entries
   - Description of the problem

## Conclusion

While version 2.0 requires a one-time migration effort, the benefits of a pure YAML-based configuration far outweigh the initial setup cost. The configuration is now clearer, more maintainable, and better suited for version control and professional deployments.

**Remember to backup before upgrading!**
