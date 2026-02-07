# SUMMARY: Your Configuration Migration

## Good News! 🎉

Your integration **already supports** BYTE brightness with 0-100 range natively! You don't need the template workaround anymore.

## What I've Created for You

I've prepared three documents to help you migrate your configuration:

### 1. 📋 CONVERTED_USER_CONFIG.yaml
**Your complete configuration, converted to use native ADS lights**

This file contains your entire configuration rewritten to use:
- `ads_custom` platform instead of `ads`
- Native ADS lights with BYTE brightness (0-100) instead of templates
- All your existing unique IDs preserved

### 2. 📖 USER_MIGRATION_GUIDE.md
**Complete step-by-step migration instructions**

This guide explains:
- What changed and why
- How to migrate step-by-step
- Configuration parameters explained
- Troubleshooting common issues
- Rollback plan if needed

### 3. 🔍 OLD_VS_NEW_COMPARISON.md
**Side-by-side comparison of old vs new approach**

Shows:
- Exactly what changed for each light
- Lines of configuration: **246 → 48 lines** (80% reduction!)
- Entity count: **24 → 6 entities** (75% fewer!)
- Feature comparison table

## Quick Migration Steps

1. **Backup** your current `configuration.yaml`
2. **Review** `CONVERTED_USER_CONFIG.yaml` - this is your new configuration
3. **Copy** the relevant sections to your `configuration.yaml`:
   - Replace `ads:` with `ads_custom:`
   - Replace `platform: ads` with `platform: ads_custom`
   - Replace the template lights section with native ADS lights
   - Remove helper sensors, binary sensors, and switches for lights
4. **Restart** Home Assistant
5. **Test** your lights (on/off and brightness)

## Key Changes Summary

### Before (Template Workaround)
For each dimmable light, you needed:
- ✗ 1 Sensor (brightness value)
- ✗ 1 Binary Sensor (on/off state)
- ✗ 1 Switch (control)
- ✗ 1 Template Light (combines all three)

**Total: 4 entities per light**

### After (Native ADS Light)
For each dimmable light, you only need:
- ✓ 1 Native ADS Light (handles everything)

**Total: 1 entity per light**

### Example: One Light Conversion

**OLD (29 lines):**
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

switch:
  - platform: ads
    name: "EGWohnzimmerLicht1_Switch"
    adsvar: ".EGWohnzimmerLicht1.EIN"

template:
  - light:
      - name: "Vorne"
        state: "{{ is_state('binary_sensor.EGWohnzimmerLicht1_State', 'on') }}"
        level: "{{ (states('sensor.EGWohnzimmerLicht1_Brightness') | int * 255 / 100) | int }}"
        turn_on:
          - service: switch.turn_on
            target: { entity_id: switch.EGWohnzimmerLicht1_Switch }
        turn_off:
          - service: switch.turn_off
            target: { entity_id: switch.EGWohnzimmerLicht1_Switch }
        set_level:
          # ... more template code ...
```

**NEW (8 lines):**
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

## How Native BYTE Brightness Works

The integration automatically converts between Home Assistant's 0-255 range and your PLC's 0-100 range:

- **From PLC to HA**: PLC value 100 → HA brightness 255 (100%)
- **From HA to PLC**: HA brightness 128 → PLC value 50 (50%)

You don't need to do any conversion yourself - it's all handled by the integration!

## Configuration Parameters

For your Beckhoff lights with BYTE 0-100 brightness:

```yaml
light:
  - platform: ads_custom                        # Required: Platform
    name: "My Light"                            # Required: Friendly name
    adsvar: ".MyLight.Enable"                   # Required: ON/OFF variable (BOOL)
    adsvar_brightness: ".MyLight.Brightness"    # Optional: Brightness variable
    adsvar_brightness_scale: 100                # Optional: Max PLC value (default: 255)
    adsvar_brightness_type: byte                # Optional: PLC data type (default: "byte")
    unique_id: "unique-id-here"                 # Optional: Unique ID
```

## Benefits of Migration

✅ **Simpler** - 198 fewer lines of configuration (80% reduction)
✅ **Cleaner** - 18 fewer entities (75% reduction)
✅ **Faster** - No template evaluation overhead
✅ **Native** - Built-in BYTE brightness support
✅ **Maintainable** - One entity per light instead of four

## What to Keep

Keep these entities as-is (they're not lights):
- `sensor.windgeschwindigkeit`
- `sensor.lufttemperatur`
- `sensor.niederschlagsstatus`
- `sensor.rolladen_*` (position sensors)
- `switch.freigabe_system_aaron`
- `switch.rolladen_*` (blind controls)
- Template sensors (wind, temperature)
- Template binary sensors (Niederschlag)
- Template covers (Rollladen)

## What to Remove

After migrating, you can safely remove:
- Light brightness sensors (e.g., `sensor.EGWohnzimmerLicht1_Brightness`)
- Light state binary sensors (e.g., `binary_sensor.EGWohnzimmerLicht1_State`)
- Light control switches (e.g., `switch.EGWohnzimmerLicht1_Switch`)
- Template lights (the 6 dimmable lights in the `template:` section)

## Need Help?

1. **Read the guides** - USER_MIGRATION_GUIDE.md has detailed troubleshooting
2. **Check the comparison** - OLD_VS_NEW_COMPARISON.md shows exactly what changed
3. **Use the example** - CONVERTED_USER_CONFIG.yaml is ready to use
4. **Test incrementally** - Migrate one light first, verify it works, then do the rest

## Verification Checklist

After migration, verify:
- [ ] All lights appear in Home Assistant
- [ ] Lights turn on/off correctly
- [ ] Brightness control works (0-100%)
- [ ] Real-time updates from PLC work
- [ ] Automations still work (update entity IDs if needed)
- [ ] Template sensors/binary sensors/covers still work

## Rollback

If something goes wrong:
1. Restore your backed-up `configuration.yaml`
2. Restart Home Assistant
3. Everything will work as before

---

**Ready to migrate?** Start with the CONVERTED_USER_CONFIG.yaml file and follow the USER_MIGRATION_GUIDE.md for detailed instructions.

Your configuration will be **simpler, cleaner, and faster** after migration! 🚀
