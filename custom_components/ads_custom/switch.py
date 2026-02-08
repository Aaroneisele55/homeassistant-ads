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

from .const import CONF_ADS_VAR, DOMAIN, STATE_KEY_STATE, SUBENTRY_TYPE_ENTITY
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
    """Set up ADS switch entities from a config entry's subentries."""
    ads_hub = hass.data[DOMAIN].get(entry.entry_id)
    if ads_hub is None:
        return

    entities = []
    for subentry in entry.subentries.values():
        if subentry.subentry_type != SUBENTRY_TYPE_ENTITY:
            continue
        if subentry.data.get("entity_type") != "switch":
            continue

        name = subentry.data.get(CONF_NAME, DEFAULT_NAME)
        ads_var = subentry.data.get(CONF_ADS_VAR)
        unique_id = subentry.data.get(CONF_UNIQUE_ID) or subentry.data.get("unique_id")

        if ads_var and unique_id:
            # Each subentry entity gets its own device
            device_identifiers = {(DOMAIN, unique_id)}
            device_name = name
            
            entities.append(
                AdsSwitch(ads_hub, name, ads_var, unique_id, device_name, device_identifiers)
            )

    if entities:
        async_add_entities(entities)


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
