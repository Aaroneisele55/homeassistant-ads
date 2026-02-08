# Testing Guide for Config Flow Fixes

This guide outlines the testing steps to verify the fixes for config flow and subentry issues in the ADS Custom integration.

## Prerequisites
- Home Assistant 2025.7.0 or later
- At least one Beckhoff PLC/ADS device configured
- Access to Settings → Devices & Services

## Test 1: Verify Subentry Edit Functionality (Critical Fix)

### Test 1.1: Edit Switch Entity
1. Go to Settings → Devices & Services
2. Find your ADS Custom integration
3. Click on a Switch entity
4. Click the gear icon to edit
5. Change the entity name or ADS variable
6. Click "Submit"
7. **Expected**: Changes should save successfully without "unknown error"
8. **Expected**: Entity should show new name/configuration

### Test 1.2: Edit Sensor Entity
1. Follow same steps as Test 1.1 but with a Sensor entity
2. Modify name, data type, or unit of measurement
3. **Expected**: Changes should save successfully

### Test 1.3: Edit Other Entity Types
Repeat the edit test for:
- Binary Sensor
- Light
- Cover (if configured)
- Valve (if configured)
- Select (if configured)

**Success Criteria**: All entity types should save edits without errors.

## Test 2: Verify "Add ADS Entity" Button Label

### Test 2.1: Check Button Display
1. Go to Settings → Devices & Services
2. Find your ADS Custom integration device
3. Look for the button to add new entities
4. **Expected**: Button should be labeled "Add ADS Entity"
5. **Not Expected**: Button should NOT show a translation key like `config_subentries.entity.initiate_flow.user`

### Test 2.2: Check Add Flow Title
1. Click the "Add ADS Entity" button
2. **Expected**: Dialog/form title should show "Add Entity"
3. **Expected**: Dropdown should show "Entity Type" label

**Success Criteria**: All UI labels should display properly, not show translation keys.

## Test 3: Verify Hub Selection Display

### Test 3.1: Single Hub (Baseline)
1. With only one ADS hub configured
2. Click "Add ADS Entity" button
3. **Expected**: Should go directly to entity type selection
4. **Note**: Hub is auto-selected when only one exists

### Test 3.2: Multiple Hubs (Critical Test)
1. Configure a second ADS hub (different AMS Net ID)
2. From the Devices page, try to add an entity
3. **Expected**: Should be prompted to select which hub to add entity to
4. **Expected**: Hub selection should show hub names clearly
5. **Not Expected**: Should NOT show raw entry IDs or missing labels

**Success Criteria**: When multiple hubs exist, hub selection should be clear and properly labeled.

## Test 4: Verify Device Registry Display

### Test 4.1: Check Device Structure
1. Go to Settings → Devices & Services
2. Click on "ADS Custom"
3. View the list of devices
4. **Expected**: Should see one device per configured hub
5. **Expected**: Device name should match the hub title (e.g., "ADS (192.168.1.100.1.1)")
6. **Not Expected**: Should NOT see duplicate devices
7. **Not Expected**: Should NOT see devices listed as "subdevices" of themselves

### Test 4.2: Check Entity Association
1. Click on a hub device
2. **Expected**: Should see all entities (switches, sensors, etc.) listed under that hub
3. **Expected**: Each entity should show its type and name
4. **Not Expected**: Hub device should NOT appear empty or with zero entities

**Success Criteria**: Device hierarchy should be flat - one hub device with all its entities. No duplicate or nested device entries.

## Test 5: Complete Entity Lifecycle

### Test 5.1: Add → Edit → Remove
1. Add a new switch entity
   - Click "Add ADS Entity"
   - Select "switch" type
   - Configure name and ADS variable
   - Submit
2. Edit the newly created switch
   - Change the name
   - Submit
3. Remove the switch
   - Click delete/remove
   - Confirm deletion
4. **Expected**: All operations should complete without errors

**Success Criteria**: Complete entity lifecycle works smoothly.

## Known Issues to Watch For

### Issue: Hub Selection Not Visible
**Symptom**: With multiple hubs, no prompt to select hub when adding entity
**Possible Cause**: Home Assistant version too old (< 2025.7.0) or subentry API not fully supported

### Issue: Translation Keys Visible
**Symptom**: Seeing `config_subentries.entity.entry_type` instead of "ADS Entity"
**Possible Cause**: Translation files not loaded properly, may need HA restart

### Issue: Device Shows as "Subdevice"
**Symptom**: Hub device shows as child of itself in device registry
**Status**: Under investigation - may require additional code changes

## Reporting Results

When reporting test results, please include:
1. Home Assistant version
2. Which tests passed/failed
3. Screenshots of any issues
4. Error messages from Home Assistant logs (Settings → System → Logs)

## Additional Notes

- After installing the integration, Home Assistant may need a restart to load translations
- Clear browser cache if UI labels don't update
- Check Home Assistant logs for any warnings or errors related to ADS Custom
