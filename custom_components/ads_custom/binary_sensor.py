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
from homeassistant.helpers import entity_platform
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import ADS_TYPEMAP, CONF_ADS_TYPE
from .const import CONF_ADS_VAR, DOMAIN, STATE_KEY_STATE, SUBENTRY_TYPE_ENTITY, AdsType
from .entity import AdsEntity
from .hub import AdsHub

_LOGGER = logging.getLogger(__name__)
DEFAULT_NAME = "ADS binary sensor"
PLATFORM_SCHEMA = BINARY_SENSOR_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ADS_VAR): cv.string,
        vol.Optional(CONF_ADS_TYPE, default=AdsType.BOOL): vol.All(
            vol.Coerce(AdsType),  # Coerce string to AdsType enum (StrEnum)
            vol.In([AdsType.BOOL, AdsType.REAL]),
        ),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_DEVICE_CLASS): DEVICE_CLASSES_SCHEMA,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Binary Sensor platform for ADS."""
    ads_hub = hass.data.get(DOMAIN, {}).get("connection")
    
    if ads_hub is None:
        _LOGGER.error(
            "No ADS connection configured. Please add 'ads_custom:' "
            "section to your configuration.yaml"
        )
        return

    ads_var: str = config.get(CONF_ADS_VAR)
    if not ads_var:
        _LOGGER.error("Missing required field adsvar in binary_sensor configuration")
        return
    ads_type: AdsType = config.get(CONF_ADS_TYPE, AdsType.BOOL)
    name: str = config.get(CONF_NAME, DEFAULT_NAME)
    device_class: BinarySensorDeviceClass | None = config.get(CONF_DEVICE_CLASS) or None
    unique_id: str | None = config.get(CONF_UNIQUE_ID)

    ads_sensor = AdsBinarySensor(ads_hub, name, ads_var, ads_type, device_class, unique_id)
    add_entities([ads_sensor])


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ADS binary sensor entities from a config entry's subentries."""

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_options_flow(AdsEntityOptionsFlowHandler)

    ads_hub = hass.data[DOMAIN].get(entry.entry_id)
    if ads_hub is None:
        return

    for subentry_id, subentry in entry.subentries.items():
        if subentry.subentry_type != SUBENTRY_TYPE_ENTITY:
            continue
        if subentry.data.get("entity_type") != "binary_sensor":
            continue

        name = subentry.data.get(CONF_NAME, DEFAULT_NAME)
        ads_var = subentry.data.get(CONF_ADS_VAR)
        ads_type_value = subentry.data.get(CONF_ADS_TYPE, AdsType.BOOL)
        ads_type = AdsType(ads_type_value) if isinstance(ads_type_value, str) else ads_type_value
        device_class = subentry.data.get(CONF_DEVICE_CLASS) or None
        unique_id = subentry.data.get(CONF_UNIQUE_ID) or subentry.data.get("unique_id")

        if ads_var and unique_id:
            # Each subentry gets its own device using the subentry's unique_id
            device_identifiers = {(DOMAIN, subentry.unique_id)}
            device_name = name
            
            async_add_entities(
                [AdsBinarySensor(ads_hub, name, ads_var, ads_type, device_class, unique_id, device_name, device_identifiers, entry.entry_id)],
                config_subentry_id=subentry_id,
            )


class AdsBinarySensor(AdsEntity, BinarySensorEntity):
    """Representation of ADS binary sensors."""

    def __init__(
        self,
        ads_hub: AdsHub,
        name: str,
        ads_var: str,
        ads_type: AdsType,
        device_class: BinarySensorDeviceClass | None,
        unique_id: str | None,
        device_name: str | None = None,
        device_identifiers: set | None = None,
        config_entry_id: str | None = None,
    ) -> None:
        """Initialize ADS binary sensor."""
        super().__init__(ads_hub, name, ads_var, unique_id, device_name, device_identifiers, config_entry_id)
        self._ads_type = ads_type
        self._configured_device_class = device_class

    async def async_added_to_hass(self) -> None:
        """Register device notification."""
        await self.async_initialize_device(self._ads_var, ADS_TYPEMAP[self._ads_type])

    @property
    def device_class(self) -> BinarySensorDeviceClass | None:
        """Return the device class of the binary sensor.

        Checks entity registry for custom device_class first,
        then falls back to configured value.
        """
        if self.registry_entry and self.registry_entry.device_class:
            return self.registry_entry.device_class
        return self._configured_device_class

    @property
    def is_on(self) -> bool | None:
        """Return True if the entity is on."""
        value = self._state_dict.get(STATE_KEY_STATE)
        if value is None:
            return None
        # For REAL type, treat 0.0 as False, any other value as True
        # Note: Direct comparison with 0.0 is appropriate here as PLC values
        # are typically exact (0.0, 1.0, etc.) and floating-point precision
        # issues are unlikely in this context
        if self._ads_type == AdsType.REAL:
            return bool(value != 0.0)
        # For BOOL type, return value directly
        return bool(value)
