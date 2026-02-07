"""Support for Automation Device Specification (ADS)."""

from __future__ import annotations

import logging

import pyads
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_DEVICE,
    CONF_IP_ADDRESS,
    CONF_PORT,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType

from .const import CONF_ADS_VAR, DOMAIN, AdsType
from .hub import AdsHub

_LOGGER = logging.getLogger(__name__)

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


SERVICE_WRITE_DATA_BY_NAME = "write_data_by_name"

SCHEMA_SERVICE_WRITE_DATA_BY_NAME = vol.Schema(
    {
        vol.Required(CONF_ADS_TYPE): vol.Coerce(AdsType),
        vol.Required(CONF_ADS_VALUE): vol.Coerce(int),
        vol.Required(CONF_ADS_VAR): str,
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the ADS component from YAML configuration."""
    # Initialize data storage
    hass.data.setdefault(DOMAIN, {})
    
    if DOMAIN not in config:
        # No YAML configuration, but config entries may exist
        _LOGGER.debug("No YAML configuration found, waiting for config entries")
        return True

    conf = config[DOMAIN]
    net_id = conf[CONF_DEVICE]
    ip_address = conf.get(CONF_IP_ADDRESS)
    port = conf.get(CONF_PORT, 48898)

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

    # Store the ADS hub for platform access
    hass.data[DOMAIN]["connection"] = ads

    async def async_shutdown_handler(event):
        """Shutdown ADS connection."""
        ads.shutdown()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_shutdown_handler)

    # Register services
    await _async_register_services(hass, ads)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ADS from a config entry."""
    net_id = entry.data[CONF_DEVICE]
    ip_address = entry.data.get(CONF_IP_ADDRESS)
    port = entry.data.get(CONF_PORT, 48898)

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

    # Store the ADS hub using entry_id to allow multiple connections
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = ads
    
    # Also store as "connection" for backward compatibility with YAML platforms
    if "connection" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["connection"] = ads

    async def async_shutdown_handler(event):
        """Shutdown ADS connection."""
        ads.shutdown()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_shutdown_handler)

    # Register services (only once)
    await _async_register_services(hass, ads)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    ads_hub = hass.data[DOMAIN].pop(entry.entry_id, None)
    
    if ads_hub:
        await hass.async_add_executor_job(ads_hub.shutdown)
    
    # Clean up "connection" if it was this entry
    if hass.data[DOMAIN].get("connection") is ads_hub:
        hass.data[DOMAIN].pop("connection", None)
    
    return True


async def _async_register_services(hass: HomeAssistant, ads: AdsHub) -> None:
    """Register ADS services."""
    # Only register services once
    if hass.services.has_service(DOMAIN, SERVICE_WRITE_DATA_BY_NAME):
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

