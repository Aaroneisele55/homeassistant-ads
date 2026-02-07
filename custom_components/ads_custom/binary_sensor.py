"""Support for ADS binary sensors."""

from __future__ import annotations

import logging

import pyads
import voluptuous as vol

from homeassistant.components.binary_sensor import (
    DEVICE_CLASSES_SCHEMA,
    PLATFORM_SCHEMA as BINARY_SENSOR_PLATFORM_SCHEMA,
    BinarySensorDeviceClass,
    BinarySensorEntity,
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
DEFAULT_NAME = "ADS binary sensor"
PLATFORM_SCHEMA = BINARY_SENSOR_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ADS_VAR): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_DEVICE_CLASS): DEVICE_CLASSES_SCHEMA,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
    }
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ADS binary sensors from a config entry."""
    ads_hub = hass.data[DOMAIN][entry.entry_id]
    
    # Get entities configured via UI
    entities_config = entry.options.get("entities", {})
    entities = []
    
    for entity_id, config in entities_config.items():
        if config.get("type") == "binary_sensor":
            ads_var = config.get(CONF_ADS_VAR)
            name = config.get(CONF_NAME, DEFAULT_NAME)
            if not ads_var:
                _LOGGER.warning("Skipping binary_sensor %s: missing adsvar", entity_id)
                continue
            device_class = config.get(CONF_DEVICE_CLASS)
            unique_id = config.get(CONF_UNIQUE_ID) or entity_id
            
            entities.append(AdsBinarySensor(ads_hub, name, ads_var, device_class, unique_id))
    
    if entities:
        async_add_entities(entities)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Binary Sensor platform for ADS."""
    # Get the first (and typically only) ADS hub from config entries
    ads_hub = None
    for entry_id in hass.data.get(DOMAIN, {}):
        ads_hub = hass.data[DOMAIN][entry_id]
        break

    if ads_hub is None:
        return

    ads_var: str = config.get(CONF_ADS_VAR)
    if not ads_var:
        _LOGGER.error("Missing required field adsvar in binary_sensor configuration")
        return
    name: str = config.get(CONF_NAME, DEFAULT_NAME)
    device_class: BinarySensorDeviceClass | None = config.get(CONF_DEVICE_CLASS)
    unique_id: str | None = config.get(CONF_UNIQUE_ID)

    ads_sensor = AdsBinarySensor(ads_hub, name, ads_var, device_class, unique_id)
    add_entities([ads_sensor])


class AdsBinarySensor(AdsEntity, BinarySensorEntity):
    """Representation of ADS binary sensors."""

    def __init__(
        self,
        ads_hub: AdsHub,
        name: str,
        ads_var: str,
        device_class: BinarySensorDeviceClass | None,
        unique_id: str | None,
    ) -> None:
        """Initialize ADS binary sensor."""
        super().__init__(ads_hub, name, ads_var, unique_id)
        self._attr_device_class = device_class or BinarySensorDeviceClass.MOVING

    async def async_added_to_hass(self) -> None:
        """Register device notification."""
        await self.async_initialize_device(self._ads_var, pyads.PLCTYPE_BOOL)

    @property
    def is_on(self) -> bool | None:
        """Return True if the entity is on."""
        return self._state_dict.get(STATE_KEY_STATE)
