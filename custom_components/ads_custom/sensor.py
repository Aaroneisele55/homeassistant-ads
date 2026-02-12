"""Support for ADS sensors."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.components.sensor import (
    CONF_STATE_CLASS,
    DEVICE_CLASSES_SCHEMA as SENSOR_DEVICE_CLASSES_SCHEMA,
    PLATFORM_SCHEMA as SENSOR_PLATFORM_SCHEMA,
    STATE_CLASSES_SCHEMA as SENSOR_STATE_CLASSES_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_NAME,
    CONF_UNIQUE_ID,
    CONF_UNIT_OF_MEASUREMENT,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback, entity_platform
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType, StateType

from . import ADS_TYPEMAP, CONF_ADS_FACTOR, CONF_ADS_TYPE
from .const import CONF_ADS_VAR, DOMAIN, STATE_KEY_STATE, SUBENTRY_TYPE_ENTITY, AdsType
from .entity import AdsEntity
from .entity_options_flow import AdsEntityOptionsFlowHandler
from .hub import AdsHub

_LOGGER = logging.getLogger(__name__)
DEFAULT_NAME = "ADS sensor"

PLATFORM_SCHEMA = SENSOR_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ADS_VAR): cv.string,
        vol.Optional(CONF_ADS_FACTOR): cv.positive_int,
        vol.Optional(CONF_ADS_TYPE, default=AdsType.INT): vol.All(
            vol.Coerce(AdsType),
            vol.In(
                [
                    AdsType.BOOL,
                    AdsType.BYTE,
                    AdsType.INT,
                    AdsType.UINT,
                    AdsType.SINT,
                    AdsType.USINT,
                    AdsType.DINT,
                    AdsType.UDINT,
                    AdsType.WORD,
                    AdsType.DWORD,
                    AdsType.LREAL,
                    AdsType.REAL,
                ]
            ),
        ),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_DEVICE_CLASS): SENSOR_DEVICE_CLASSES_SCHEMA,
        vol.Optional(CONF_STATE_CLASS): SENSOR_STATE_CLASSES_SCHEMA,
        vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up an ADS sensor device."""
    ads_hub = hass.data.get(DOMAIN, {}).get("connection")
    
    if ads_hub is None:
        _LOGGER.error(
            "No ADS connection configured. Please add 'ads_custom:' "
            "section to your configuration.yaml"
        )
        return

    ads_var: str = config.get(CONF_ADS_VAR)
    if not ads_var:
        _LOGGER.error("Missing required field adsvar in sensor configuration")
        return
    ads_type: AdsType = config.get(CONF_ADS_TYPE, AdsType.INT)
    name: str = config.get(CONF_NAME, DEFAULT_NAME)
    factor: int | None = config.get(CONF_ADS_FACTOR)
    device_class: SensorDeviceClass | None = config.get(CONF_DEVICE_CLASS) or None
    state_class: SensorStateClass | None = config.get(CONF_STATE_CLASS) or None
    unit_of_measurement: str | None = config.get(CONF_UNIT_OF_MEASUREMENT)
    unique_id: str | None = config.get(CONF_UNIQUE_ID)

    entity = AdsSensor(
        ads_hub,
        name,
        ads_var,
        ads_type,
        factor,
        device_class,
        state_class,
        unit_of_measurement,
        unique_id,
    )

    add_entities([entity])


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ADS sensor entities from a config entry's subentries."""

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_options_flow(AdsEntityOptionsFlowHandler)

    ads_hub = hass.data[DOMAIN].get(entry.entry_id)
    if ads_hub is None:
        return

    for subentry_id, subentry in entry.subentries.items():
        if subentry.subentry_type != SUBENTRY_TYPE_ENTITY:
            continue
        if subentry.data.get("entity_type") != "sensor":
            continue

        name = subentry.data.get(CONF_NAME, DEFAULT_NAME)
        ads_var = subentry.data.get(CONF_ADS_VAR)
        ads_type_value = subentry.data.get(CONF_ADS_TYPE, AdsType.INT)
        ads_type = AdsType(ads_type_value) if isinstance(ads_type_value, str) else ads_type_value
        factor = subentry.data.get(CONF_ADS_FACTOR)
        device_class = subentry.data.get(CONF_DEVICE_CLASS) or None
        state_class = subentry.data.get(CONF_STATE_CLASS) or None
        unit_of_measurement = subentry.data.get(CONF_UNIT_OF_MEASUREMENT)
        unique_id = subentry.data.get(CONF_UNIQUE_ID) or subentry.data.get("unique_id")

        if ads_var and unique_id:
            # Each subentry gets its own device using the subentry's unique_id
            device_identifiers = {(DOMAIN, subentry.unique_id)}
            device_name = name
            
            async_add_entities(
                [AdsSensor(
                    ads_hub,
                    name,
                    ads_var,
                    ads_type,
                    factor,
                    device_class,
                    state_class,
                    unit_of_measurement,
                    unique_id,
                    device_name,
                    device_identifiers,
                    entry.entry_id,
                )],
                config_subentry_id=subentry_id,
            )


class AdsSensor(AdsEntity, SensorEntity):
    """Representation of an ADS sensor entity."""

    def __init__(
        self,
        ads_hub: AdsHub,
        name: str,
        ads_var: str,
        ads_type: AdsType,
        factor: int | None,
        device_class: SensorDeviceClass | None,
        state_class: SensorStateClass | None,
        unit_of_measurement: str | None,
        unique_id: str | None,
        device_name: str | None = None,
        device_identifiers: set | None = None,
        config_entry_id: str | None = None,
    ) -> None:
        """Initialize AdsSensor entity."""
        super().__init__(ads_hub, name, ads_var, unique_id, device_name, device_identifiers, config_entry_id)
        self._ads_type = ads_type
        self._factor = factor
        self._configured_device_class = device_class
        self._attr_state_class = state_class
        self._attr_native_unit_of_measurement = unit_of_measurement

    async def async_added_to_hass(self) -> None:
        """Register device notification."""
        await self.async_initialize_device(
            self._ads_var,
            ADS_TYPEMAP[self._ads_type],
            STATE_KEY_STATE,
            self._factor,
        )

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the device class of the sensor.

        Checks entity registry for custom device_class first,
        then falls back to configured value.
        """
        if self.registry_entry and self.registry_entry.device_class:
            return self.registry_entry.device_class
        return self._configured_device_class

    @property
    def native_value(self) -> StateType:
        """Return the state of the device."""
        return self._state_dict.get(STATE_KEY_STATE)
