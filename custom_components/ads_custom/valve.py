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
    # Get the first (and typically only) ADS hub from config entries
    ads_hub = None
    for entry_id in hass.data.get(DOMAIN, {}):
        ads_hub = hass.data[DOMAIN][entry_id]
        break

    if ads_hub is None:
        # Fallback to YAML connection if no config entry hub found
        ads_hub = hass.data.get(DOMAIN, {}).get("yaml_connection")
        if ads_hub is None:
            _LOGGER.error("No ADS connection configured. Please set up the ADS integration first.")
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
        self._attr_device_class = device_class
        self._attr_reports_position = False

    async def async_added_to_hass(self) -> None:
        """Register device notification."""
        await self.async_initialize_device(self._ads_var, pyads.PLCTYPE_BOOL)

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
