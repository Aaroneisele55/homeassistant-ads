# Quick Start: Native ADS Lights

## Your Question Answered ✅

**Q: How do I create ADS lights that use BYTE (0-100 range) instead of the template workaround?**

**A: Your integration already supports this natively!** Use the configuration below.

## Configuration Example

For Beckhoff lights with BYTE brightness (0-100 range):

```yaml
light:
  - platform: ads_custom
    name: "My Dimmable Light"
    adsvar: ".MyLight.Enable"              # BOOL variable for ON/OFF
    adsvar_brightness: ".MyLight.Value"    # BYTE variable for brightness (0-100)
    adsvar_brightness_scale: 100           # Max value in PLC (100 for 0-100 range)
    adsvar_brightness_type: byte           # Data type (byte or uint)
    unique_id: "my_light_001"
```

## Replace Template Workaround

**REMOVE this (old template workaround):**
```yaml
sensor:
  - platform: ads
    name: "Light_Brightness"
    adsvar: ".Light.Value"
    adstype: "byte"

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
      - name: "My Light"
        state: "{{ is_state('binary_sensor.Light_State', 'on') }}"
        level: "{{ (states('sensor.Light_Brightness') | int * 255 / 100) | int }}"
        # ... more template code ...
```

**ADD this (native ADS light):**
```yaml
light:
  - platform: ads_custom
    name: "My Light"
    adsvar: ".Light.Enable"
    adsvar_brightness: ".Light.Value"
    adsvar_brightness_scale: 100
    adsvar_brightness_type: byte
    unique_id: "my_light_001"
```

## Your Configuration Converted

I've converted your entire configuration. See these files:

1. **MIGRATION_SUMMARY.md** ← **START HERE** - Overview and quick steps
2. **CONVERTED_USER_CONFIG.yaml** - Your complete converted configuration
3. **USER_MIGRATION_GUIDE.md** - Detailed step-by-step guide
4. **OLD_VS_NEW_COMPARISON.md** - Side-by-side comparison

## Parameters Explained

| Parameter | Description | Your Value |
|-----------|-------------|------------|
| `platform` | Integration name | `ads_custom` |
| `adsvar` | PLC ON/OFF variable (BOOL) | `.MyLight.EIN` |
| `adsvar_brightness` | PLC brightness variable | `.MyLight.Wert` |
| `adsvar_brightness_scale` | Max PLC brightness value | `100` (for 0-100 range) |
| `adsvar_brightness_type` | PLC data type | `byte` (or `uint`) |
| `unique_id` | Unique identifier | Any unique string |

## Benefits

- **1 entity** instead of 4 (sensor + binary_sensor + switch + template)
- **8 lines** instead of 29 lines per light
- **No templates** - native support
- **Automatic conversion** between HA (0-255) and PLC (0-100)

## Next Steps

1. Read **MIGRATION_SUMMARY.md** for overview
2. Review **CONVERTED_USER_CONFIG.yaml** (your config, already converted!)
3. Follow **USER_MIGRATION_GUIDE.md** for step-by-step instructions
4. Check **OLD_VS_NEW_COMPARISON.md** to see exact changes

---

**Result:** Your 6 dimmable lights go from **24 entities** to **6 entities**, and from **~246 lines** to **~48 lines** of configuration! 🎉
