# Migration Guide: From Template Workaround to Native ADS Lights

This guide explains how to migrate your YAML configuration from using the template workaround to native ADS lights with BYTE brightness support (0-100 range).

## What Changed?

The `ads_custom` integration now natively supports:
- **BYTE brightness values** (0-100 range) in addition to UINT (0-255 range)
- **Custom brightness scaling** via `adsvar_brightness_scale` parameter
- **Direct brightness control** without needing template lights

## Key Benefits

1. **Simpler Configuration**: No need for separate sensors, binary sensors, switches, and template lights
2. **Native Support**: Direct ADS light entities with proper brightness handling
3. **Better Performance**: No template evaluation overhead
4. **Cleaner UI**: Fewer entities to manage

## Migration Steps

### Step 1: Update Platform Names

Change all instances of `platform: ads` to `platform: ads_custom`:

**Before:**
```yaml
sensor:
  - platform: ads
    name: "My Sensor"
```

**After:**
```yaml
sensor:
  - platform: ads_custom
    name: "My Sensor"
```

### Step 2: Replace Template Lights with Native ADS Lights

The old workaround required:
- 1 ADS sensor for brightness
- 1 ADS binary sensor for state
- 1 ADS switch for control
- 1 Template light to combine them

Now you only need **1 native ADS light**!

**Before (Template Workaround):**
```yaml
sensor:
  - platform: ads
    name: "EGWohnzimmerLicht1_Brightness"
    adsvar: ".EGWohnzimmerLicht1.Wert"
    adstype: "byte"

binary_sensor:
  - platform: ads
    name: "EGWohnzimmerLicht1_State"
    adsvar: ".EGWohnzimmerLicht1.EIN"
    device_class: light

switch:
  - platform: ads
    name: "EGWohnzimmerLicht1_Switch"
    adsvar: ".EGWohnzimmerLicht1.EIN"

template:
  - light:
      - name: "Vorne"
        unique_id: "7a1c9148-c2e9-492b-8321-3b6bab24d928"
        state: "{{ is_state('binary_sensor.EGWohnzimmerLicht1_State', 'on') }}"
        level: "{{ (states('sensor.EGWohnzimmerLicht1_Brightness') | int * 255 / 100) | int }}"
        turn_on:
          - service: switch.turn_on
            target: { entity_id: switch.EGWohnzimmerLicht1_Switch }
        turn_off:
          - service: switch.turn_off
            target: { entity_id: switch.EGWohnzimmerLicht1_Switch }
        set_level:
          - service: switch.turn_on
            target: { entity_id: switch.EGWohnzimmerLicht1_Switch }
          - service: ads.write_data_by_name
            data:
              adsvar: ".EGWohnzimmerLicht1.Wert"
              value: "{{ (brightness * 100 / 255) | int }}"
              adstype: byte
```

**After (Native ADS Light):**
```yaml
light:
  - platform: ads_custom
    name: "Vorne"
    adsvar: ".EGWohnzimmerLicht1.EIN"
    adsvar_brightness: ".EGWohnzimmerLicht1.Wert"
    adsvar_brightness_scale: 100
    adsvar_brightness_type: byte
    unique_id: "7a1c9148-c2e9-492b-8321-3b6bab24d928"
```

### Step 3: Configuration Parameters for Native ADS Lights

#### Required Parameters:
- `platform: ads_custom` - The platform identifier
- `adsvar: ".path.to.enable"` - PLC variable for ON/OFF control (BOOL)
- `name: "Light Name"` - Friendly name for the light

#### Optional Parameters for Dimmable Lights:
- `adsvar_brightness: ".path.to.brightness"` - PLC variable for brightness value
- `adsvar_brightness_scale: 100` - Maximum brightness value in PLC (default: 255)
  - Use `100` for Beckhoff lights with 0-100 range
  - Use `255` for lights with 0-255 range (default)
- `adsvar_brightness_type: byte` - PLC data type for brightness (default: "byte")
  - Use `"byte"` for BYTE (8-bit) variables
  - Use `"uint"` for UINT (16-bit) variables
- `unique_id: "unique-id-here"` - Unique identifier for the entity

#### Examples:

**Simple ON/OFF Light:**
```yaml
light:
  - platform: ads_custom
    name: "Simple Light"
    adsvar: ".MyLight.Enable"
    unique_id: "simple_light_001"
```

**Dimmable Light with BYTE (0-100):**
```yaml
light:
  - platform: ads_custom
    name: "Dimmable Light"
    adsvar: ".MyLight.Enable"
    adsvar_brightness: ".MyLight.Brightness"
    adsvar_brightness_scale: 100
    adsvar_brightness_type: byte
    unique_id: "dimmable_light_001"
```

**Dimmable Light with UINT (0-255):**
```yaml
light:
  - platform: ads_custom
    name: "Standard Dimmable"
    adsvar: ".MyLight.Enable"
    adsvar_brightness: ".MyLight.Brightness"
    adsvar_brightness_scale: 255
    adsvar_brightness_type: uint
    unique_id: "standard_light_001"
```

### Step 4: Remove Old Helper Entities

After migrating to native ADS lights, you can **safely remove**:
- The brightness sensors (e.g., `sensor.EGWohnzimmerLicht1_Brightness`)
- The state binary sensors (e.g., `binary_sensor.EGWohnzimmerLicht1_State`)
- The control switches (e.g., `switch.EGWohnzimmerLicht1_Switch`)
- The template lights (from the `template:` section)

**Important:** Keep any switches that control other functions (not lights), like:
- `switch.freigabe_system_aaron`
- `switch.rolladen_terassentur_hoch`
- `switch.rolladen_terassentur_runter`

### Step 5: Update Entity References

If you have automations or scripts that reference the old entity IDs, update them:

**Before:**
```yaml
automation:
  - alias: "Turn on light"
    action:
      - service: light.turn_on
        target:
          entity_id: light.vorne  # Template light
```

**After:**
```yaml
automation:
  - alias: "Turn on light"
    action:
      - service: light.turn_on
        target:
          entity_id: light.vorne  # Native ADS light (same entity_id!)
```

Since we kept the same `unique_id`, the entity ID should remain the same.

## Understanding the Brightness Scaling

The integration handles brightness conversion automatically:

1. **Home Assistant** uses 0-255 range for brightness (0% to 100%)
2. **Your PLC** uses 0-100 range (BYTE)
3. **The integration** converts between them:
   - When reading: PLC value (0-100) → HA value (0-255)
   - When writing: HA value (0-255) → PLC value (0-100)

Example: If you set brightness to 50% in HA:
- HA sends brightness = 127 (50% of 255)
- Integration converts: 127 × 100 / 255 = 49.8 ≈ 50
- PLC receives brightness = 50 (50% of 100)

## Complete Migration Example

See the `CONVERTED_USER_CONFIG.yaml` file for a complete working example of the converted configuration.

## Troubleshooting

### Problem: Lights don't respond to brightness changes

**Check:**
1. Verify `adsvar_brightness` points to the correct PLC variable
2. Confirm `adsvar_brightness_scale` matches your PLC range (100 or 255)
3. Ensure `adsvar_brightness_type` matches your PLC data type (byte or uint)

### Problem: Brightness values seem wrong

**Solution:**
- If brightness appears doubled/halved, check your `adsvar_brightness_scale` value
- For 0-100 PLC range, use `adsvar_brightness_scale: 100`
- For 0-255 PLC range, use `adsvar_brightness_scale: 255` (or omit, as it's the default)

### Problem: Entities not appearing

**Check:**
1. Platform name is `ads_custom` (not `ads`)
2. YAML syntax is correct (proper indentation)
3. Home Assistant logs for error messages
4. Restart Home Assistant after configuration changes

## Testing Your Migration

1. **Backup** your current `configuration.yaml`
2. **Update** to the new configuration
3. **Restart** Home Assistant
4. **Test** each light:
   - Turn on/off
   - Adjust brightness (if dimmable)
   - Verify PLC values change correctly
5. **Update** any automations/scripts if needed

## Rollback Plan

If you need to revert:
1. Restore your backed-up `configuration.yaml`
2. Restart Home Assistant
3. Your old template lights will work again

## Questions?

If you encounter issues:
1. Check Home Assistant logs: `Settings > System > Logs`
2. Review the README.md for additional examples
3. Verify your PLC variable names are correct
4. Ensure your ADS connection is working (test with a simple switch/sensor)
