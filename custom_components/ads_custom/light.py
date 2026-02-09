"""Support for ADS light sources."""

from __future__ import annotations

import logging
from typing import Any

import pyads
import voluptuous as vol

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    PLATFORM_SCHEMA as LIGHT_PLATFORM_SCHEMA,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_UNIQUE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import CONF_ADS_VAR, DOMAIN, STATE_KEY_STATE, SUBENTRY_TYPE_ENTITY
from .entity import AdsEntity
from .hub import AdsHub

_LOGGER = logging.getLogger(__name__)

CONF_ADS_VAR_BRIGHTNESS = "adsvar_brightness"
CONF_ADS_BRIGHTNESS_SCALE = "adsvar_brightness_scale"
CONF_ADS_VAR_BRIGHTNESS_TYPE = "adsvar_brightness_type"
STATE_KEY_BRIGHTNESS = "brightness"

DEFAULT_NAME = "ADS Light"
DEFAULT_BRIGHTNESS_SCALE = 255
# Default to BYTE because Beckhoff lights typically use BYTE (0-255) for brightness
DEFAULT_BRIGHTNESS_TYPE = "byte"

PLATFORM_SCHEMA = LIGHT_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ADS_VAR): cv.string,
        vol.Optional(CONF_ADS_VAR_BRIGHTNESS): cv.string,
        vol.Optional(CONF_ADS_BRIGHTNESS_SCALE, default=DEFAULT_BRIGHTNESS_SCALE): cv.positive_int,
        vol.Optional(CONF_ADS_VAR_BRIGHTNESS_TYPE, default=DEFAULT_BRIGHTNESS_TYPE): vol.In(["byte", "uint"]),
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
    """Set up the light platform for ADS."""
    ads_hub = hass.data.get(DOMAIN, {}).get("connection")
    
    if ads_hub is None:
        _LOGGER.error(
            "No ADS connection configured. Please add 'ads_custom:' "
            "section to your configuration.yaml"
        )
        return

    ads_var_enable: str = config.get(CONF_ADS_VAR)
    if not ads_var_enable:
        _LOGGER.error("Missing required field adsvar in light configuration")
        return
    ads_var_brightness: str | None = config.get(CONF_ADS_VAR_BRIGHTNESS)
    brightness_scale: int = config.get(CONF_ADS_BRIGHTNESS_SCALE, DEFAULT_BRIGHTNESS_SCALE)
    brightness_type: str = config.get(CONF_ADS_VAR_BRIGHTNESS_TYPE, DEFAULT_BRIGHTNESS_TYPE)
    name: str = config.get(CONF_NAME, DEFAULT_NAME)
    unique_id: str | None = config.get(CONF_UNIQUE_ID)

    add_entities(
        [AdsLight(ads_hub, ads_var_enable, ads_var_brightness, brightness_scale, brightness_type, name, unique_id)]
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ADS light entities from a config entry's subentries."""
    ads_hub = hass.data[DOMAIN].get(entry.entry_id)
    if ads_hub is None:
        return

    entities = []
    for subentry in entry.subentries.values():
        if subentry.subentry_type != SUBENTRY_TYPE_ENTITY:
            continue
        if subentry.data.get("entity_type") != "light":
            continue

        name = subentry.data.get(CONF_NAME, DEFAULT_NAME)
        ads_var = subentry.data.get(CONF_ADS_VAR)
        ads_var_brightness = subentry.data.get(CONF_ADS_VAR_BRIGHTNESS)
        brightness_scale = subentry.data.get(CONF_ADS_BRIGHTNESS_SCALE, DEFAULT_BRIGHTNESS_SCALE)
        brightness_type = subentry.data.get(CONF_ADS_VAR_BRIGHTNESS_TYPE, DEFAULT_BRIGHTNESS_TYPE)
        unique_id = subentry.data.get(CONF_UNIQUE_ID) or subentry.data.get("unique_id")

        if ads_var and unique_id:
            # All entities share the hub device using the entry's entry_id
            device_identifiers = {(DOMAIN, entry.entry_id)}
            device_name = entry.title
            
            entities.append(
                AdsLight(ads_hub, ads_var, ads_var_brightness, brightness_scale, brightness_type, name, unique_id, device_name, device_identifiers)
            )

    if entities:
        async_add_entities(entities)


class AdsLight(AdsEntity, LightEntity):
    """Representation of ADS light."""

    def __init__(
        self,
        ads_hub: AdsHub,
        ads_var_enable: str,
        ads_var_brightness: str | None,
        brightness_scale: int,
        brightness_type: str,
        name: str,
        unique_id: str | None,
        device_name: str | None = None,
        device_identifiers: set | None = None,
    ) -> None:
        """Initialize AdsLight entity."""
        super().__init__(ads_hub, name, ads_var_enable, unique_id, device_name, device_identifiers)
        self._state_dict[STATE_KEY_BRIGHTNESS] = None
        self._ads_var_brightness = ads_var_brightness
        self._brightness_scale = brightness_scale
        self._brightness_type = brightness_type
        if ads_var_brightness is not None:
            self._attr_color_mode = ColorMode.BRIGHTNESS
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        else:
            self._attr_color_mode = ColorMode.ONOFF
            self._attr_supported_color_modes = {ColorMode.ONOFF}

    def _get_brightness_plc_type(self) -> type:
        """Return the PLC data type to use for brightness based on configuration."""
        return pyads.PLCTYPE_BYTE if self._brightness_type == "byte" else pyads.PLCTYPE_UINT

    async def async_added_to_hass(self) -> None:
        """Register device notification."""
        await self.async_initialize_device(self._ads_var, pyads.PLCTYPE_BOOL)

        if self._ads_var_brightness is not None:
            # Calculate the scaling factor to convert PLC value to HA brightness (0-255)
            # When reading from PLC, the factor is passed to async_initialize_device which
            # divides the PLC value by the factor to get the HA value (see entity.py).
            # For a 0-100 range: factor = 100/255, so value/factor scales 100 to 255.
            # For the default 255 range, factor is None to avoid unnecessary division by 1.
            brightness_factor = self._brightness_scale / 255 if self._brightness_scale != 255 else None
            await self.async_initialize_device(
                self._ads_var_brightness,
                self._get_brightness_plc_type(),
                STATE_KEY_BRIGHTNESS,
                brightness_factor,
            )

    @property
    def brightness(self) -> int | None:
        """Return the brightness of the light (0..255)."""
        return self._state_dict.get(STATE_KEY_BRIGHTNESS)

    @property
    def is_on(self) -> bool | None:
        """Return True if the entity is on."""
        return self._state_dict.get(STATE_KEY_STATE)

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the light on or set a specific dimmer value."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        self._ads_hub.write_by_name(self._ads_var, True, pyads.PLCTYPE_BOOL)

        if self._ads_var_brightness is not None and brightness is not None:
            # Scale brightness from HA range (0-255) to PLC range (0-brightness_scale)
            scaled_brightness = int(brightness * self._brightness_scale / 255)
            self._ads_hub.write_by_name(
                self._ads_var_brightness, scaled_brightness, self._get_brightness_plc_type()
            )

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        self._ads_hub.write_by_name(self._ads_var, False, pyads.PLCTYPE_BOOL)
