# Testing Guide for ADS Custom Integration

This guide outlines the testing steps to verify the functionality of the ADS Custom integration.

## Prerequisites
- Home Assistant 2024.1.0 or later
- At least one Beckhoff PLC/ADS device configured
- Access to Settings → Devices & Services

## Test 1: Verify Device Association Fix (Critical Fix)

### Test 1.1: Check Entity Device Association
1. Go to Settings → Devices & Services
2. Click on "ADS Custom"
3. View the list of devices
4. **Expected**: Should see one device per entity (named after the entity)
5. **Not Expected**: Should NOT see all entities grouped under a single hub device
6. Click on an entity's device
7. **Expected**: Should see that entity (and ONLY that entity) listed under its device

### Test 1.2: Verify Device Registry
1. Go to Settings → Devices & Services → Devices (or `/config/devices/dashboard`)
2. Search for your ADS entities
3. **Expected**: Each entity should have its own device entry
4. **Expected**: Device name should match the entity name
5. **Not Expected**: Should NOT see all entities under one "ADS Connection" or hub device

**Success Criteria**: Each entity has its own device in the device registry, properly associated based on its subentry unique_id.

## Test 2: Verify Subentry Edit Functionality (Critical Fix)

### Test 2.1: Edit Switch Entity
1. Go to Settings → Devices & Services
2. Find your ADS Custom integration
3. Click "Configure" on the hub entry
4. Find a Switch entity in the subentry list
5. Click the gear icon or edit button
6. Change the entity name or ADS variable
7. Click "Submit"
8. **Expected**: Changes should save successfully without "unknown error"
9. **Expected**: Entity should show new name/configuration

### Test 2.2: Edit Sensor Entity
1. Follow same steps as Test 2.1 but with a Sensor entity
2. Modify name, data type, or unit of measurement
3. **Expected**: Changes should save successfully

### Test 2.3: Edit Other Entity Types
Repeat the edit test for:
- Binary Sensor
- Light
- Cover (if configured)
- Valve (if configured)
- Select (if configured)

**Success Criteria**: All entity types should save edits without errors. The MappingProxyType wrapper ensures data immutability.

## Test 3: Verify "Add ADS Entity" Button Label

### Test 3.1: Check Button Display
1. Go to Settings → Devices & Services
2. Find your ADS Custom integration device
3. Look for the button to add new entities
4. **Expected**: Button should be labeled "Add ADS Entity"
5. **Not Expected**: Button should NOT show a translation key like `config_subentries.entity.initiate_flow.user`

### Test 3.2: Check Add Flow Title
1. Click the "Add ADS Entity" button
2. **Expected**: Dialog/form title should show "Add Entity"
3. **Expected**: Dropdown should show "Entity Type" label

**Success Criteria**: All UI labels should display properly, not show translation keys.

## Test 4: Verify Hub Selection Display

### Test 4.1: Single Hub (Baseline)
1. With only one ADS hub configured
2. Click "Add ADS Entity" button
3. **Expected**: Should go directly to entity type selection
4. **Note**: Hub is auto-selected when only one exists

### Test 4.2: Multiple Hubs (Critical Test)
1. Configure a second ADS hub (different AMS Net ID)
2. From the Devices page, try to add an entity
3. **Expected**: Should be prompted to select which hub to add entity to
4. **Expected**: Hub selection should show hub names clearly
5. **Not Expected**: Should NOT show raw entry IDs or missing labels

**Success Criteria**: When multiple hubs exist, hub selection should be clear and properly labeled.

## Test 5: Verify Complete Entity Lifecycle

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
