"""Support for Automation Device Specification (ADS)."""

from __future__ import annotations

import asyncio
import logging
import uuid

import pyads
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
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
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.typing import ConfigType

from .const import CONF_ADS_VAR, DOMAIN, AdsType, CONF_ENTRY_TYPE, ENTRY_TYPE_HUB, ENTRY_TYPE_ENTITY
from .hub import AdsHub

_LOGGER = logging.getLogger(__name__)

# Helper constant for entity configuration
CONF_ENTITY_TYPE = "entity_type"

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


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the ADS component from YAML configuration."""
    # Initialize data storage once
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    
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
    """Set up ADS from a config entry."""
    # Initialize data storage
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    
    # Check if this is a hub or entity config entry
    entry_type = entry.data.get(CONF_ENTRY_TYPE, ENTRY_TYPE_HUB)
    
    if entry_type == ENTRY_TYPE_ENTITY:
        # This is an entity config entry - just forward to platforms
        # The ADS hub should already be set up by the parent entry
        _LOGGER.debug("async_setup_entry: Setting up entity config entry: %s", entry.title)
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        
        # Register update listener for entity options changes
        entry.async_on_unload(entry.add_update_listener(async_reload_entry))
        return True
    
    # This is a hub config entry - set up the connection
    _LOGGER.debug("async_setup_entry: Setting up hub config entry: %s", entry.title)
    
    # Set up the connection
    success = await _async_setup_connection(hass, entry.data, entry.entry_id)
    
    if not success:
        return False
    
    # Also store as "connection" for backward compatibility with YAML platforms
    if "connection" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["connection"] = hass.data[DOMAIN][entry.entry_id]
    
    # Always forward all platforms so they're registered
    # Each platform's async_setup_entry will check if it has entities and return early if not
    _LOGGER.debug("async_setup_entry: Forwarding setup to all platforms")
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register update listener for options changes first
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    
    # Migrate any entities without unique_id (from old versions)
    # This must happen after registering the update listener to avoid issues
    entities = entry.options.get("entities", [])
    needs_migration = False
    updated_entities = []
    
    for entity_config in entities:
        if not entity_config.get(CONF_UNIQUE_ID):
            # Generate unique_id for entities that don't have one
            # Using dict() is sufficient as entity_config is a flat dictionary
            entity_config = dict(entity_config)  # Shallow copy is safe here
            entity_config[CONF_UNIQUE_ID] = uuid.uuid4().hex
            needs_migration = True
            _LOGGER.info("Generated unique_id for entity: %s", entity_config.get(CONF_NAME, "unknown"))
        updated_entities.append(entity_config)
    
    # Update config entry if migration was needed
    # Note: This triggers async_reload_entry via the update listener above
    # The reload is expected and ensures migrated entities are properly registered
    if needs_migration:
        _LOGGER.info("Migrating %d entities to add unique_id, integration will reload", len(updated_entities))
        hass.config_entries.async_update_entry(
            entry,
            options={**entry.options, "entities": updated_entities}
        )
        # Early return - the reload will re-run async_setup_entry with migrated data
        return True
    
    # Get entity registry to handle entity deletions
    entity_registry = er.async_get(hass)
    
    # Subscribe to entity registry updates to handle entity deletions
    @callback
    def async_registry_updated(event):
        """Handle entity registry update events."""
        if event.data["action"] != "remove":
            return
            
        entity_id = event.data["entity_id"]
        
        # Check if the removed entity had our config entry ID
        # The event includes the old entry before removal (EntityRegistryEntry object)
        old_entry = event.data.get("old")
        if old_entry and old_entry.config_entry_id == entry.entry_id:
            # This entity belonged to our config entry
            unique_id = old_entry.unique_id
            if unique_id:
                # Remove from config entry options
                entities = list(entry.options.get("entities", []))
                updated_entities = [e for e in entities if e.get(CONF_UNIQUE_ID) != unique_id]
                
                if len(updated_entities) < len(entities):
                    _LOGGER.info("Entity %s (unique_id: %s) removed from registry, removing from config", 
                               entity_id, unique_id)
                    hass.config_entries.async_update_entry(
                        entry,
                        options={**entry.options, "entities": updated_entities}
                    )
    
    entry.async_on_unload(
        hass.bus.async_listen(er.EVENT_ENTITY_REGISTRY_UPDATED, async_registry_updated)
    )
    
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    _LOGGER.debug("async_reload_entry: Reloading config entry due to options change")
    await hass.config_entries.async_reload(entry.entry_id)


# Add helper constant for entity configuration
CONF_ENTITY_TYPE = "entity_type"


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle permanent removal of a config entry."""
    entry_type = entry.data.get(CONF_ENTRY_TYPE, ENTRY_TYPE_HUB)

    if entry_type == ENTRY_TYPE_HUB:
        # Find and remove all child entity config entries
        child_entries = [
            child_entry for child_entry in hass.config_entries.async_entries(DOMAIN)
            if child_entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_ENTITY
            and child_entry.data.get("parent_entry_id") == entry.entry_id
        ]

        if child_entries:
            _LOGGER.info(
                "Hub entry being removed - also removing %d child entity entries",
                len(child_entries),
            )
            for child_entry in child_entries:
                await hass.config_entries.async_remove(child_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("async_unload_entry: Unloading config entry")

    entry_type = entry.data.get(CONF_ENTRY_TYPE, ENTRY_TYPE_HUB)

    # Unload all platforms that were forwarded during setup
    _LOGGER.debug("async_unload_entry: Unloading platforms: %s", PLATFORMS)
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    
    if not unload_ok:
        _LOGGER.error("async_unload_entry: Failed to unload some platforms")
        return False
    
    # Get the hub before we remove it (only for hub entries)
    if entry_type == ENTRY_TYPE_HUB:
        ads_hub = hass.data[DOMAIN].get(entry.entry_id)
        
        if ads_hub:
            await hass.async_add_executor_job(ads_hub.shutdown)
            hass.data[DOMAIN].pop(entry.entry_id, None)
        
        # Clean up "connection" if it points to this hub
        if hass.data[DOMAIN].get("connection") is ads_hub:
            hass.data[DOMAIN].pop("connection", None)
    
    _LOGGER.debug("async_unload_entry: Successfully unloaded")
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

