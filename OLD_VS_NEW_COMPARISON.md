# Side-by-Side Comparison: Old vs New Configuration

This document shows the differences between the old template-based approach and the new native ADS light approach.

## Configuration Complexity Comparison

### Old Approach: Template Workaround
**Entities per dimmable light: 4**
- 1 Sensor (brightness)
- 1 Binary Sensor (state)
- 1 Switch (control)
- 1 Template Light (combining all three)

### New Approach: Native ADS Light
**Entities per dimmable light: 1**
- 1 Native ADS Light (handles everything)

## Complete Example for One Light

### OLD: Template Workaround (4 entities)

```yaml
##################################
# SENSOR FOR BRIGHTNESS
##################################
sensor:
  - platform: ads
    name: "EGWohnzimmerLicht1_Brightness"
    adsvar: ".EGWohnzimmerLicht1.Wert"
    adstype: "byte"
    unique_id: "a3b1f7e0-7f87-4c32-8e1b-1a2c4b9d1234"
    state_class: "measurement"

##################################
# BINARY SENSOR FOR STATE
##################################
binary_sensor:
  - platform: ads
    name: "EGWohnzimmerLicht1_State"
    adsvar: ".EGWohnzimmerLicht1.EIN"
    device_class: light
    unique_id: "7ei8j9k0-1f23-4lg6-57gi-4ei8j3k5678"

##################################
# SWITCH FOR CONTROL
##################################
switch:
  - platform: ads
    name: "EGWohnzimmerLicht1_Switch"
    adsvar: ".EGWohnzimmerLicht1.EIN"
    unique_id: "fmp6r7s8-9n01-4to4-35oq-2fmp1s3456"

##################################
# TEMPLATE LIGHT (COMBINES ALL)
##################################
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

### NEW: Native ADS Light (1 entity)

```yaml
##################################
# NATIVE ADS LIGHT
##################################
light:
  - platform: ads_custom
    name: "Vorne"
    adsvar: ".EGWohnzimmerLicht1.EIN"
    adsvar_brightness: ".EGWohnzimmerLicht1.Wert"
    adsvar_brightness_scale: 100
    adsvar_brightness_type: byte
    unique_id: "7a1c9148-c2e9-492b-8321-3b6bab24d928"
```

## Lines of Configuration

### For 6 Dimmable Lights:

**Old Approach:**
- Sensors: ~12 lines × 6 = 72 lines
- Binary Sensors: ~6 lines × 6 = 36 lines
- Switches: ~5 lines × 6 = 30 lines
- Template Lights: ~18 lines × 6 = 108 lines
- **Total: ~246 lines**

**New Approach:**
- Native ADS Lights: ~8 lines × 6 = 48 lines
- **Total: ~48 lines**

**Savings: 198 lines (80% reduction!)**

## Entity Count Comparison

### Your Configuration (6 Dimmable Lights)

**Old Approach:**
- 6 Brightness Sensors
- 6 State Binary Sensors
- 6 Control Switches
- 6 Template Lights
- **Total: 24 entities**

**New Approach:**
- 6 Native ADS Lights
- **Total: 6 entities**

**Reduction: 18 fewer entities (75% fewer!)**

## Feature Comparison

| Feature | Old (Template) | New (Native) |
|---------|----------------|--------------|
| ON/OFF Control | ✅ Yes | ✅ Yes |
| Brightness Control | ✅ Yes | ✅ Yes |
| BYTE Support (0-100) | ✅ Yes (via template) | ✅ Yes (native) |
| UINT Support (0-255) | ✅ Yes (via template) | ✅ Yes (native) |
| Real-time Updates | ✅ Yes | ✅ Yes |
| Configuration Complexity | 🔴 High (4 entities) | 🟢 Low (1 entity) |
| Performance | 🟡 Good | 🟢 Better |
| Template Evaluation | 🔴 Required | 🟢 Not needed |
| Service Calls | 🔴 Multiple | 🟢 Single |
| Entity Count | 🔴 4× per light | 🟢 1× per light |

## Full Configuration Comparison

### OLD: Complete Configuration (Only showing relevant sections)

```yaml
ads:
  device: "192.168.1.55.1.1"
  port: 801

sensor:
  # 6 brightness sensors (one per dimmable light)
  - platform: ads
    name: "EGWohnzimmerLicht1_Brightness"
    adsvar: ".EGWohnzimmerLicht1.Wert"
    adstype: "byte"
  # ... 5 more sensors ...

binary_sensor:
  # 6 state sensors (one per dimmable light)
  - platform: ads
    name: "EGWohnzimmerLicht1_State"
    adsvar: ".EGWohnzimmerLicht1.EIN"
    device_class: light
  # ... 5 more binary sensors ...

switch:
  # 6 control switches (one per dimmable light)
  - platform: ads
    name: "EGWohnzimmerLicht1_Switch"
    adsvar: ".EGWohnzimmerLicht1.EIN"
  # ... 5 more switches ...

light:
  # 2 simple ON/OFF lights
  - platform: ads
    name: "EG Terasse Licht 1"
    adsvar: ".EGTerrasseLicht1.EIN"
  # ... 1 more simple light ...

template:
  - light:
      # 6 template lights (combining sensors, binary sensors, and switches)
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
          - service: switch.turn_on
            target: { entity_id: switch.EGWohnzimmerLicht1_Switch }
          - service: ads.write_data_by_name
            data:
              adsvar: ".EGWohnzimmerLicht1.Wert"
              value: "{{ (brightness * 100 / 255) | int }}"
              adstype: byte
      # ... 5 more template lights ...
```

### NEW: Complete Configuration

```yaml
ads_custom:
  device: "192.168.1.55.1.1"
  port: 801

# Keep only sensors that are not light-related
sensor:
  - platform: ads_custom
    name: "Windgeschwindigkeit"
    adsvar: ".ParameterWetterstation.Windgschwindigkeit"
    adstype: "real"
  # ... other non-light sensors (7 total)

# No binary sensors needed (all were light-related)

# Keep only switches that are not light-related
switch:
  - platform: ads_custom
    name: "Freigabe System Aaron"
    adsvar: ".bFreigabeSystemAaron"
  # ... other non-light switches ...

# All lights in one place!
light:
  # 2 simple ON/OFF lights
  - platform: ads_custom
    name: "EG Terasse Licht 1"
    adsvar: ".EGTerrasseLicht1.EIN"
    unique_id: "mtw3y4z5-6u78-4a01-02vx-9mtw8z0123"

  - platform: ads_custom
    name: "EG WC Licht 1"
    adsvar: ".EGWcLicht1.EIN"
    unique_id: "nux4z5a6-7v89-4b12-13wy-0nux9a1234"

  # 6 dimmable lights with native BYTE support
  - platform: ads_custom
    name: "Vorne"
    adsvar: ".EGWohnzimmerLicht1.EIN"
    adsvar_brightness: ".EGWohnzimmerLicht1.Wert"
    adsvar_brightness_scale: 100
    adsvar_brightness_type: byte
    unique_id: "7a1c9148-c2e9-492b-8321-3b6bab24d928"

  - platform: ads_custom
    name: "hinten"
    adsvar: ".EGWohnzimmerLicht2.EIN"
    adsvar_brightness: ".EGWohnzimmerLicht2.Wert"
    adsvar_brightness_scale: 100
    adsvar_brightness_type: byte
    unique_id: "aa30a3b0-61e3-4587-a1b2-95f6dea6a06b"

  # ... 4 more dimmable lights ...

# No template section needed for lights!
```

## Migration Checklist

- [ ] Update `ads:` to `ads_custom:`
- [ ] Change all `platform: ads` to `platform: ads_custom`
- [ ] Replace template lights with native ADS lights
- [ ] Remove brightness sensors for lights
- [ ] Remove state binary sensors for lights
- [ ] Remove control switches for lights
- [ ] Keep non-light sensors, binary sensors, and switches
- [ ] Test each light (on/off and brightness)
- [ ] Update automations if needed
- [ ] Remove old configuration backup after verification

## Result

✅ **Simpler**: 80% fewer lines of configuration
✅ **Cleaner**: 75% fewer entities
✅ **Faster**: No template evaluation overhead
✅ **Native**: Built-in support for BYTE brightness (0-100)
✅ **Maintainable**: One entity per light instead of four
