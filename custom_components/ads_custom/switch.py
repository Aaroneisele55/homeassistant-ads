"""Support for ADS switch platform."""

from __future__ import annotations

import logging
from typing import Any

import pyads
import voluptuous as vol

from homeassistant.components.switch import (
    PLATFORM_SCHEMA as SWITCH_PLATFORM_SCHEMA,
    SwitchEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_UNIQUE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import CONF_ADS_VAR, DOMAIN, STATE_KEY_STATE
from .entity import AdsEntity

_LOGGER = logging.getLogger(__name__)
DEFAULT_NAME = "ADS Switch"

PLATFORM_SCHEMA = SWITCH_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ADS_VAR): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up switch platform for ADS."""
    ads_hub = hass.data.get(DOMAIN, {}).get("connection")
    
    if ads_hub is None:
        _LOGGER.error(
            "No ADS connection configured. Please add 'ads_custom:' "
            "section to your configuration.yaml"
        )
        return

    name: str = config.get(CONF_NAME, DEFAULT_NAME)
    ads_var: str = config.get(CONF_ADS_VAR)
    if not ads_var:
        _LOGGER.error("Missing required field adsvar in switch configuration")
        return
    unique_id: str | None = config.get(CONF_UNIQUE_ID)

    add_entities([AdsSwitch(ads_hub, name, ads_var, unique_id)])


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ADS switch entities from a config entry."""
    # Check if this is a hub or entity config entry
    entry_type = entry.data.get("entry_type", "hub")
    
    if entry_type == "entity":
        # This is an entity config entry - check if it's a switch
        if entry.data.get("entity_type") == "switch":
            ads_hub = hass.data[DOMAIN].get(entry.data.get("parent_entry_id"))
            if ads_hub is None:
                _LOGGER.error("Parent hub not found for entity %s", entry.title)
                return
            
            name = entry.data.get(CONF_NAME, DEFAULT_NAME)
            ads_var = entry.data.get(CONF_ADS_VAR)
            unique_id = entry.data.get(CONF_UNIQUE_ID)
            
            # Get device info from parent hub entry
            parent_entry = hass.config_entries.async_get_entry(entry.data.get("parent_entry_id"))
            if parent_entry:
                device_identifiers = {(DOMAIN, parent_entry.entry_id)}
                device_name = parent_entry.title
            else:
                device_identifiers = None
                device_name = None
            
            if ads_var:
                async_add_entities([AdsSwitch(ads_hub, name, ads_var, unique_id, device_name, device_identifiers)])
        return
    
    # This is a hub config entry - load switches from options (backward compatibility)
    ads_hub = hass.data[DOMAIN][entry.entry_id]
    
    # Get switch entities from config entry options
    entities = entry.options.get("entities", [])
    switches = [e for e in entities if e.get("entity_type") == "switch"]
    
    if not switches:
        return
    
    # Create device identifiers based on the ADS connection
    device_identifiers = {(DOMAIN, entry.entry_id)}
    device_name = entry.title
    
    switch_entities = []
    for switch_config in switches:
        name = switch_config.get(CONF_NAME, DEFAULT_NAME)
        ads_var = switch_config.get(CONF_ADS_VAR)
        unique_id = switch_config.get(CONF_UNIQUE_ID)
        
        if ads_var:
            switch_entities.append(AdsSwitch(ads_hub, name, ads_var, unique_id, device_name, device_identifiers))
    
    if switch_entities:
        async_add_entities(switch_entities)


class AdsSwitch(AdsEntity, SwitchEntity):
    """Representation of an ADS switch device."""
    
    def __init__(
        self,
        ads_hub,
        name: str,
        ads_var: str,
        unique_id: str | None,
        device_name: str | None = None,
        device_identifiers: set | None = None,
    ) -> None:
        """Initialize AdsSwitch entity."""
        super().__init__(ads_hub, name, ads_var, unique_id, device_name, device_identifiers)

    async def async_added_to_hass(self) -> None:
        """Register device notification."""
        await self.async_initialize_device(self._ads_var, pyads.PLCTYPE_BOOL)

    @property
    def is_on(self) -> bool | None:
        """Return True if the entity is on."""
        return self._state_dict.get(STATE_KEY_STATE)

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        self._ads_hub.write_by_name(self._ads_var, True, pyads.PLCTYPE_BOOL)

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        self._ads_hub.write_by_name(self._ads_var, False, pyads.PLCTYPE_BOOL)
