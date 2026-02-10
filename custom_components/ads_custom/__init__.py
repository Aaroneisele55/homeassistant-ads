"""Support for Automation Device Specification (ADS)."""

from __future__ import annotations

import asyncio
import logging
import uuid
from types import MappingProxyType

import pyads
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.const import (
    CONF_DEVICE,
    CONF_DEVICE_CLASS,
    CONF_IP_ADDRESS,
    CONF_NAME,
    CONF_PORT,
    CONF_UNIQUE_ID,
    CONF_UNIT_OF_MEASUREMENT,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.typing import ConfigType

from .const import CONF_ADS_VAR, DOMAIN, AdsType, SUBENTRY_TYPE_ENTITY
from .hub import AdsHub

_LOGGER = logging.getLogger(__name__)

# Helper constant for entity configuration
CONF_ENTITY_TYPE = "entity_type"

# Old migration constants (kept for backward compatibility during migration)
CONF_ENTRY_TYPE = "entry_type"
CONF_PARENT_ENTRY_ID = "parent_entry_id"
ENTRY_TYPE_HUB = "hub"
ENTRY_TYPE_ENTITY = "entity"

# Config schema for YAML configuration
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_DEVICE): vol.Coerce(str),
                vol.Optional(CONF_IP_ADDRESS): vol.Coerce(str),
                vol.Optional(CONF_PORT, default=48898): vol.Coerce(int),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

ADS_TYPEMAP = {
    AdsType.BOOL: pyads.PLCTYPE_BOOL,
    AdsType.BYTE: pyads.PLCTYPE_BYTE,
    AdsType.INT: pyads.PLCTYPE_INT,
    AdsType.UINT: pyads.PLCTYPE_UINT,
    AdsType.SINT: pyads.PLCTYPE_SINT,
    AdsType.USINT: pyads.PLCTYPE_USINT,
    AdsType.DINT: pyads.PLCTYPE_DINT,
    AdsType.UDINT: pyads.PLCTYPE_UDINT,
    AdsType.WORD: pyads.PLCTYPE_WORD,
    AdsType.DWORD: pyads.PLCTYPE_DWORD,
    AdsType.REAL: pyads.PLCTYPE_REAL,
    AdsType.LREAL: pyads.PLCTYPE_LREAL,
    AdsType.STRING: pyads.PLCTYPE_STRING,
    AdsType.TIME: pyads.PLCTYPE_TIME,
    AdsType.DATE: pyads.PLCTYPE_DATE,
    AdsType.DATE_AND_TIME: pyads.PLCTYPE_DT,
    AdsType.TOD: pyads.PLCTYPE_TOD,
}

CONF_ADS_FACTOR = "factor"
CONF_ADS_TYPE = "adstype"
CONF_ADS_VALUE = "value"

# All platforms supported by this integration
PLATFORMS = [
    "binary_sensor",
    "sensor",
    "switch",
    "light",
    "cover",
    "valve",
    "select",
]

# Platform YAML keys to scan for entity migration (same as PLATFORMS)
_PLATFORM_KEYS = PLATFORMS

# Keys to copy per entity type when migrating from YAML
_ENTITY_KEYS: dict[str, list[str]] = {
    "sensor": [
        CONF_ADS_VAR, CONF_ADS_TYPE, CONF_ADS_FACTOR, CONF_NAME,
        CONF_DEVICE_CLASS, "state_class", CONF_UNIT_OF_MEASUREMENT, CONF_UNIQUE_ID,
    ],
    "binary_sensor": [
        CONF_ADS_VAR, CONF_ADS_TYPE, CONF_NAME, CONF_DEVICE_CLASS, CONF_UNIQUE_ID,
    ],
    "switch": [CONF_ADS_VAR, CONF_NAME, CONF_UNIQUE_ID],
    "light": [
        CONF_ADS_VAR, "adsvar_brightness", "adsvar_brightness_scale",
        "adsvar_brightness_type", CONF_NAME, CONF_UNIQUE_ID,
    ],
    "cover": [
        CONF_ADS_VAR, "adsvar_position", "adsvar_position_type",
        "adsvar_set_position", "adsvar_open", "adsvar_close", "adsvar_stop",
        "inverted", CONF_NAME, CONF_DEVICE_CLASS, CONF_UNIQUE_ID,
    ],
    "valve": [CONF_ADS_VAR, CONF_NAME, CONF_DEVICE_CLASS, CONF_UNIQUE_ID],
    "select": [CONF_ADS_VAR, CONF_NAME, "options", CONF_UNIQUE_ID],
}


def _collect_yaml_entities(config: ConfigType) -> list[dict]:
    """Collect entity configurations from YAML platform sections."""
    entities: list[dict] = []

    for platform_key in _PLATFORM_KEYS:
        platform_configs = config.get(platform_key, [])
        if not isinstance(platform_configs, list):
            platform_configs = [platform_configs]

        for pcfg in platform_configs:
            if not isinstance(pcfg, dict):
                continue
            if pcfg.get("platform") != DOMAIN:
                continue

            entity: dict = {CONF_ENTITY_TYPE: platform_key}
            allowed_keys = _ENTITY_KEYS.get(platform_key, [])
            for key in allowed_keys:
                if key in pcfg:
                    value = pcfg[key]
                    # Convert enum values to strings for JSON serialization
                    if hasattr(value, "value"):
                        value = value.value
                    entity[key] = value

            # Ensure every migrated entity has a unique_id
            if not entity.get(CONF_UNIQUE_ID):
                entity[CONF_UNIQUE_ID] = uuid.uuid4().hex

            entities.append(entity)

    return entities


SERVICE_WRITE_DATA_BY_NAME = "write_data_by_name"

SCHEMA_SERVICE_WRITE_DATA_BY_NAME = vol.Schema(
    {
        vol.Required(CONF_ADS_TYPE): vol.Coerce(AdsType),
        vol.Required(CONF_ADS_VALUE): vol.Coerce(int),
        vol.Required(CONF_ADS_VAR): str,
    }
)


async def _async_setup_connection(
    hass: HomeAssistant, config_data: dict, storage_key: str
) -> bool:
    """Set up an ADS connection from configuration data."""
    net_id = config_data[CONF_DEVICE]
    ip_address = config_data.get(CONF_IP_ADDRESS)
    port = config_data.get(CONF_PORT, 48898)

    client = pyads.Connection(net_id, port, ip_address)

    try:
        ads = AdsHub(client)
    except pyads.ADSError as err:
        _LOGGER.error(
            "Could not connect to ADS host (netid=%s, ip=%s, port=%s): %s",
            net_id,
            ip_address,
            port,
            err,
        )
        return False

    # Store the ADS hub
    hass.data[DOMAIN][storage_key] = ads

    async def async_shutdown_handler(event):
        """Shutdown ADS connection."""
        ads.shutdown()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_shutdown_handler)

    # Register services
    await _async_register_services(hass, ads)

    return True


async def _async_migrate_to_subentries(hass: HomeAssistant) -> None:
    """Migrate old entity config entries and hub options entities to subentries."""
    entries = hass.config_entries.async_entries(DOMAIN)

    # Separate hub and entity entries
    hub_entries: dict[str, ConfigEntry] = {}
    entity_entries: list[ConfigEntry] = []

    for entry in entries:
        entry_type = entry.data.get(CONF_ENTRY_TYPE, ENTRY_TYPE_HUB)
        if entry_type == ENTRY_TYPE_ENTITY:
            entity_entries.append(entry)
        else:
            hub_entries[entry.entry_id] = entry

    # 1) Migrate old entity config entries to subentries on their parent hub
    for entity_entry in entity_entries:
        parent_id = entity_entry.data.get(CONF_PARENT_ENTRY_ID)
        parent_hub = hub_entries.get(parent_id)

        if parent_hub is None:
            _LOGGER.warning(
                "Orphan entity config entry '%s' has no parent hub, removing",
                entity_entry.title,
            )
            await hass.config_entries.async_remove(entity_entry.entry_id)
            continue

        # Build subentry data (strip migration-only keys)
        entity_data = dict(entity_entry.data)
        entity_data.pop(CONF_ENTRY_TYPE, None)
        entity_data.pop(CONF_PARENT_ENTRY_ID, None)

        entity_unique_id = entity_data.get(CONF_UNIQUE_ID) or entity_data.get("unique_id")

        # Check for duplicates
        existing_unique_ids = {s.unique_id for s in parent_hub.subentries.values()}
        if entity_unique_id and entity_unique_id in existing_unique_ids:
            _LOGGER.debug(
                "Entity '%s' already migrated as subentry, removing old entry",
                entity_entry.title,
            )
        else:
            subentry = ConfigSubentry(
                data=MappingProxyType(entity_data),
                subentry_type=SUBENTRY_TYPE_ENTITY,
                title=entity_entry.title,
                unique_id=entity_unique_id,
            )
            hass.config_entries.async_add_subentry(parent_hub, subentry)
            _LOGGER.info(
                "Migrated entity config entry '%s' to subentry on hub '%s'",
                entity_entry.title,
                parent_hub.title,
            )

        await hass.config_entries.async_remove(entity_entry.entry_id)

    # 2) Migrate hub options entities list to subentries
    for hub_entry in hub_entries.values():
        entities_in_options = hub_entry.options.get("entities", [])
        if not entities_in_options:
            continue

        # Also strip old entry_type from hub data if present
        hub_data = dict(hub_entry.data)
        needs_data_update = False
        if CONF_ENTRY_TYPE in hub_data:
            hub_data.pop(CONF_ENTRY_TYPE)
            needs_data_update = True

        existing_unique_ids = {s.unique_id for s in hub_entry.subentries.values()}

        for entity_config in entities_in_options:
            entity_unique_id = entity_config.get(CONF_UNIQUE_ID) or entity_config.get("unique_id")

            # Ensure unique_id exists
            if not entity_unique_id:
                entity_unique_id = uuid.uuid4().hex
                entity_config = dict(entity_config)
                entity_config[CONF_UNIQUE_ID] = entity_unique_id

            if entity_unique_id in existing_unique_ids:
                continue

            entity_type = entity_config.get(CONF_ENTITY_TYPE, "unknown")
            entity_name = entity_config.get(CONF_NAME, "Entity")

            subentry = ConfigSubentry(
                data=MappingProxyType(dict(entity_config)),
                subentry_type=SUBENTRY_TYPE_ENTITY,
                title=f"{entity_name} ({entity_type.replace('_', ' ').title()})",
                unique_id=entity_unique_id,
            )
            hass.config_entries.async_add_subentry(hub_entry, subentry)
            existing_unique_ids.add(entity_unique_id)
            _LOGGER.info(
                "Migrated options entity '%s' to subentry on hub '%s'",
                entity_name,
                hub_entry.title,
            )

        # Clear entities from options and optionally update data
        if needs_data_update:
            hass.config_entries.async_update_entry(
                hub_entry,
                data=hub_data,
                options={},
            )
        else:
            hass.config_entries.async_update_entry(
                hub_entry,
                options={},
            )


async def _async_migrate_entity_config_entries(hass: HomeAssistant) -> None:
    """Migrate entity registry entries to have proper config_entry_id."""
    entries = hass.config_entries.async_entries(DOMAIN)
    
    # Only process hub entries (not old entity entries)
    hub_entries = [e for e in entries if e.data.get(CONF_ENTRY_TYPE, ENTRY_TYPE_HUB) == ENTRY_TYPE_HUB]
    
    for hub_entry in hub_entries:
        await _async_migrate_entity_config_entries_for_hub(hass, hub_entry)


async def _async_migrate_entity_config_entries_for_hub(hass: HomeAssistant, hub_entry: ConfigEntry) -> None:
    """Migrate entity and device registry entries for a hub to have proper subentry associations."""
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)
    
    # Get all entities that belong to this hub's subentries
    for subentry in hub_entry.subentries.values():
        if subentry.subentry_type != SUBENTRY_TYPE_ENTITY:
            continue
        
        subentry_unique_id = subentry.unique_id
        if not subentry_unique_id:
            continue

        # Migrate device: ensure device is properly associated with subentry
        # For existing users who already have the duplicate display issue,
        # we need to clean up and re-associate properly
        device = device_registry.async_get_device(
            identifiers={(DOMAIN, subentry_unique_id)}
        )
        if device is not None:
            subentry_ids = device.config_entries_subentries.get(hub_entry.entry_id)
            needs_subentry = subentry_ids is None or subentry.subentry_id not in subentry_ids
            has_subentry_association = not needs_subentry  # Inverse: True if subentry already exists
            has_direct_hub_association = hub_entry.entry_id in device.config_entries
            
            # Identify devices with duplicate display issue:
            # - Has direct hub association (device.config_entries contains hub_id)
            # - Has subentry association (needs_subentry is False, meaning subentry already exists)
            # This happens when old migration called add_config_entry_id explicitly,
            # creating a redundant direct association separate from the proper parent relationship
            has_duplicate_display = has_direct_hub_association and has_subentry_association
            
            if has_duplicate_display:
                _LOGGER.info(
                    "Cleaning up device '%s' associations for subentry '%s' on hub '%s' (fixing duplicate display)",
                    device.name,
                    subentry.title,
                    hub_entry.title,
                )
                # Fix: Remove redundant direct hub association, then re-add properly with subentry
                # This resets the device association to the correct state
                # Note: Two separate calls are needed because async_update_device doesn't support
                # remove and add of the same entry_id in a single call
                device_registry.async_update_device(
                    device.id,
                    remove_config_entry_id=hub_entry.entry_id,
                )
                device_registry.async_update_device(
                    device.id,
                    add_config_entry_id=hub_entry.entry_id,
                    add_config_subentry_id=subentry.subentry_id,
                )
            elif needs_subentry:
                _LOGGER.info(
                    "Migrating device '%s' to subentry '%s' on hub '%s'",
                    device.name,
                    subentry.title,
                    hub_entry.title,
                )
                # Device is already associated with hub via entity's device_info
                # Just add the subentry association to nest it properly in the UI
                device_registry.async_update_device(
                    device.id,
                    add_config_subentry_id=subentry.subentry_id,
                )
        
        # Migrate entity: associate existing entity with its subentry
        entity_entry = None
        for platform in PLATFORMS:
            entity_id = entity_registry.async_get_entity_id(
                platform,
                DOMAIN,
                subentry_unique_id
            )
            if entity_id:
                entity_entry = entity_registry.entities.get(entity_id)
                break
        
        if entity_entry is None:
            continue

        needs_update = False
        update_kwargs: dict[str, str] = {}

        if entity_entry.config_entry_id != hub_entry.entry_id:
            update_kwargs["config_entry_id"] = hub_entry.entry_id
            needs_update = True

        if entity_entry.config_subentry_id != subentry.subentry_id:
            update_kwargs["config_subentry_id"] = subentry.subentry_id
            needs_update = True

        if needs_update:
            _LOGGER.info(
                "Migrating entity '%s' (unique_id: %s) to subentry '%s' on hub '%s'",
                entity_entry.entity_id,
                subentry_unique_id,
                subentry.title,
                hub_entry.title,
            )
            entity_registry.async_update_entity(
                entity_entry.entity_id,
                **update_kwargs,
            )


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the ADS component from YAML configuration."""
    # Initialize data storage once
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    # Migrate old entity config entries / hub options to subentries
    await _async_migrate_to_subentries(hass)
    
    # Migrate entity registry entries to have proper config_entry_id
    await _async_migrate_entity_config_entries(hass)

    if DOMAIN not in config:
        # No YAML configuration, but config entries may exist
        _LOGGER.debug("No YAML configuration found, waiting for config entries")
        return True

    conf = config[DOMAIN]

    # Collect entity configs from platform YAML sections
    entities = _collect_yaml_entities(config)

    # Trigger import flow to create a config entry from YAML
    _LOGGER.info(
        "YAML configuration detected for %s, migrating to config entry", DOMAIN
    )
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={**conf, "entities": entities},
        )
    )

    # Still set up the YAML connection for backward compatibility
    # (platforms using setup_platform need it until YAML is removed)
    return await _async_setup_connection(hass, conf, "connection")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ADS from a config entry (hub only)."""
    # Initialize data storage
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    # Safety check: old entity entries should have been migrated in async_setup
    if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_ENTITY:
        _LOGGER.warning(
            "Unexpected entity config entry '%s' found; it should have been "
            "migrated to a subentry. Skipping setup.",
            entry.title,
        )
        return False

    _LOGGER.debug("Setting up hub config entry: %s", entry.title)
    
    # Migrate entity registry entries for this hub (if not already done)
    await _async_migrate_entity_config_entries_for_hub(hass, entry)

    # Set up the ADS connection
    success = await _async_setup_connection(hass, entry.data, entry.entry_id)
    if not success:
        return False

    # Also store as "connection" for backward compatibility with YAML platforms
    if "connection" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["connection"] = hass.data[DOMAIN][entry.entry_id]

    # Forward all platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload when config entry is updated (e.g. subentry added/removed)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options or subentries change."""
    _LOGGER.debug("Reloading config entry due to update")
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading config entry: %s", entry.title)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if not unload_ok:
        _LOGGER.error("Failed to unload some platforms")
        return False

    ads_hub = hass.data[DOMAIN].get(entry.entry_id)
    if ads_hub:
        await hass.async_add_executor_job(ads_hub.shutdown)
        hass.data[DOMAIN].pop(entry.entry_id, None)

    # Clean up "connection" if it points to this hub
    if hass.data[DOMAIN].get("connection") is ads_hub:
        hass.data[DOMAIN].pop("connection", None)

    return True


async def _async_register_services(hass: HomeAssistant, ads: AdsHub) -> None:
    """Register ADS services (thread-safe)."""
    # Store registration state in hass.data instead of global variable
    if "_services_registered" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["_services_lock"] = asyncio.Lock()
        hass.data[DOMAIN]["_services_registered"] = False

    async with hass.data[DOMAIN]["_services_lock"]:
        if hass.data[DOMAIN]["_services_registered"]:
            return

        async def handle_write_data_by_name(call: ServiceCall) -> None:
            """Write a value to the connected ADS device."""
            ads_var: str = call.data[CONF_ADS_VAR]
            ads_type: AdsType = call.data[CONF_ADS_TYPE]
            value: int = call.data[CONF_ADS_VALUE]

            try:
                ads.write_by_name(ads_var, value, ADS_TYPEMAP[ads_type])
            except pyads.ADSError as err:
                _LOGGER.error(err)

        hass.services.async_register(
            DOMAIN,
            SERVICE_WRITE_DATA_BY_NAME,
            handle_write_data_by_name,
            schema=SCHEMA_SERVICE_WRITE_DATA_BY_NAME,
        )

        hass.data[DOMAIN]["_services_registered"] = True
