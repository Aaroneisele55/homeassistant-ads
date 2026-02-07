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


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ADS switches from a config entry."""
    ads_hub = hass.data[DOMAIN][entry.entry_id]
    
    # Get entities configured via UI
    entities_config = entry.options.get("entities", {})
    entities = []
    
    for entity_id, config in entities_config.items():
        if config.get("type") == "switch":
            ads_var = config.get(CONF_ADS_VAR)
            name = config.get(CONF_NAME, DEFAULT_NAME)
            if not ads_var:
                _LOGGER.warning("Skipping switch %s: missing adsvar", entity_id)
                continue
            unique_id = config.get(CONF_UNIQUE_ID) or entity_id
            
            entities.append(AdsSwitch(ads_hub, name, ads_var, unique_id))
    
    if entities:
        async_add_entities(entities)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up switch platform for ADS."""
    # Get the first (and typically only) ADS hub from config entries
    ads_hub = None
    for entry_id in hass.data.get(DOMAIN, {}):
        ads_hub = hass.data[DOMAIN][entry_id]
        break

    if ads_hub is None:
        return

    name: str = config.get(CONF_NAME, DEFAULT_NAME)
    ads_var: str = config.get(CONF_ADS_VAR)
    if not ads_var:
        _LOGGER.error("Missing required field adsvar in switch configuration")
        return
    unique_id: str | None = config.get(CONF_UNIQUE_ID)

    add_entities([AdsSwitch(ads_hub, name, ads_var, unique_id)])


class AdsSwitch(AdsEntity, SwitchEntity):
    """Representation of an ADS switch device."""

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
