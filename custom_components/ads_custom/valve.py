"""Support for ADS valves."""

from __future__ import annotations

import logging

import pyads
import voluptuous as vol

from homeassistant.components.valve import (
    DEVICE_CLASSES_SCHEMA as VALVE_DEVICE_CLASSES_SCHEMA,
    PLATFORM_SCHEMA as VALVE_PLATFORM_SCHEMA,
    ValveDeviceClass,
    ValveEntity,
    ValveEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_CLASS, CONF_NAME, CONF_UNIQUE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import CONF_ADS_VAR, DOMAIN, STATE_KEY_STATE
from .entity import AdsEntity
from .hub import AdsHub

_LOGGER = logging.getLogger(__name__)
DEFAULT_NAME = "ADS valve"

PLATFORM_SCHEMA = VALVE_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ADS_VAR): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_DEVICE_CLASS): VALVE_DEVICE_CLASSES_SCHEMA,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up an ADS valve device."""
    ads_hub = hass.data.get(DOMAIN, {}).get("connection")
    
    if ads_hub is None:
        _LOGGER.error(
            "No ADS connection configured. Please add 'ads_custom:' "
            "section to your configuration.yaml"
        )
        return

    ads_var: str = config.get(CONF_ADS_VAR)
    if not ads_var:
        _LOGGER.error("Missing required field adsvar in valve configuration")
        return
    name: str = config.get(CONF_NAME, DEFAULT_NAME)
    device_class: ValveDeviceClass | None = config.get(CONF_DEVICE_CLASS)
    unique_id: str | None = config.get(CONF_UNIQUE_ID)

    entity = AdsValve(ads_hub, ads_var, name, device_class, unique_id)

    add_entities([entity])


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ADS valve entities from a config entry."""
    ads_hub = hass.data[DOMAIN][entry.entry_id]
    
    # Get valve entities from config entry options
    entities = entry.options.get("entities", [])
    valves = [e for e in entities if e.get("entity_type") == "valve"]
    
    if not valves:
        return
    
    valve_entities = []
    for valve_config in valves:
        name = valve_config.get(CONF_NAME, DEFAULT_NAME)
        ads_var = valve_config.get(CONF_ADS_VAR)
        device_class = valve_config.get(CONF_DEVICE_CLASS)
        unique_id = valve_config.get(CONF_UNIQUE_ID)
        
        if ads_var:
            valve_entities.append(
                AdsValve(ads_hub, ads_var, name, device_class, unique_id)
            )
    
    if valve_entities:
        async_add_entities(valve_entities)


class AdsValve(AdsEntity, ValveEntity):
    """Representation of an ADS valve entity."""

    _attr_supported_features = ValveEntityFeature.OPEN | ValveEntityFeature.CLOSE

    def __init__(
        self,
        ads_hub: AdsHub,
        ads_var: str,
        name: str,
        device_class: ValveDeviceClass | None,
        unique_id: str | None,
    ) -> None:
        """Initialize AdsValve entity."""
        super().__init__(ads_hub, name, ads_var, unique_id)
        self._configured_device_class = device_class
        self._attr_reports_position = False

    async def async_added_to_hass(self) -> None:
        """Register device notification."""
        await self.async_initialize_device(self._ads_var, pyads.PLCTYPE_BOOL)

    @property
    def device_class(self) -> ValveDeviceClass | None:
        """Return the device class of the valve.

        Checks entity registry for custom device_class first,
        then falls back to configured value.
        """
        if self.registry_entry and self.registry_entry.device_class:
            return self.registry_entry.device_class
        return self._configured_device_class

    @property
    def is_closed(self) -> bool | None:
        """Return if the valve is closed."""
        # True from PLC means open, so is_closed is the inverse
        state = self._state_dict.get(STATE_KEY_STATE)
        if state is None:
            return None
        return not state

    def open_valve(self, **kwargs) -> None:
        """Open the valve."""
        self._ads_hub.write_by_name(self._ads_var, True, pyads.PLCTYPE_BOOL)

    def close_valve(self, **kwargs) -> None:
        """Close the valve."""
        self._ads_hub.write_by_name(self._ads_var, False, pyads.PLCTYPE_BOOL)
