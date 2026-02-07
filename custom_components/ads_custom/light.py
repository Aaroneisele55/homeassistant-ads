"""Support for ADS light sources."""

from __future__ import annotations

from typing import Any

import pyads
import voluptuous as vol

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    PLATFORM_SCHEMA as LIGHT_PLATFORM_SCHEMA,
    ColorMode,
    LightEntity,
)
from homeassistant.const import CONF_NAME, CONF_UNIQUE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import CONF_ADS_VAR, DOMAIN, STATE_KEY_STATE
from .entity import AdsEntity
from .hub import AdsHub

CONF_ADS_VAR_BRIGHTNESS = "adsvar_brightness"
CONF_ADS_BRIGHTNESS_SCALE = "adsvar_brightness_scale"
STATE_KEY_BRIGHTNESS = "brightness"

DEFAULT_NAME = "ADS Light"
DEFAULT_BRIGHTNESS_SCALE = 255
PLATFORM_SCHEMA = LIGHT_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ADS_VAR): cv.string,
        vol.Optional(CONF_ADS_VAR_BRIGHTNESS): cv.string,
        vol.Optional(CONF_ADS_BRIGHTNESS_SCALE, default=DEFAULT_BRIGHTNESS_SCALE): cv.positive_int,
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
    # Get the first (and typically only) ADS hub from config entries
    ads_hub = None
    for entry_id in hass.data.get(DOMAIN, {}):
        ads_hub = hass.data[DOMAIN][entry_id]
        break

    if ads_hub is None:
        return

    ads_var_enable: str = config[CONF_ADS_VAR]
    ads_var_brightness: str | None = config.get(CONF_ADS_VAR_BRIGHTNESS)
    brightness_scale: int = config[CONF_ADS_BRIGHTNESS_SCALE]
    name: str = config[CONF_NAME]
    unique_id: str | None = config.get(CONF_UNIQUE_ID)

    add_entities(
        [AdsLight(ads_hub, ads_var_enable, ads_var_brightness, brightness_scale, name, unique_id)]
    )


class AdsLight(AdsEntity, LightEntity):
    """Representation of ADS light."""

    def __init__(
        self,
        ads_hub: AdsHub,
        ads_var_enable: str,
        ads_var_brightness: str | None,
        brightness_scale: int,
        name: str,
        unique_id: str | None,
    ) -> None:
        """Initialize AdsLight entity."""
        super().__init__(ads_hub, name, ads_var_enable, unique_id)
        self._state_dict[STATE_KEY_BRIGHTNESS] = None
        self._ads_var_brightness = ads_var_brightness
        self._brightness_scale = brightness_scale
        if ads_var_brightness is not None:
            self._attr_color_mode = ColorMode.BRIGHTNESS
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        else:
            self._attr_color_mode = ColorMode.ONOFF
            self._attr_supported_color_modes = {ColorMode.ONOFF}

    async def async_added_to_hass(self) -> None:
        """Register device notification."""
        await self.async_initialize_device(self._ads_var, pyads.PLCTYPE_BOOL)

        if self._ads_var_brightness is not None:
            # Calculate the scaling factor to convert PLC value to HA brightness (0-255)
            # The factor is used as a divisor in entity.py: value / factor
            # To scale 0-100 to 0-255: we need to multiply by 255/100
            # So factor should be: 100/255 = 0.392 (so value / 0.392 gives us the scaled value)
            # Or better: factor = brightness_scale / 255
            brightness_factor = self._brightness_scale / 255 if self._brightness_scale != 255 else None
            await self.async_initialize_device(
                self._ads_var_brightness,
                pyads.PLCTYPE_UINT,
                STATE_KEY_BRIGHTNESS,
                brightness_factor,
            )

    @property
    def brightness(self) -> int | None:
        """Return the brightness of the light (0..255)."""
        return self._state_dict[STATE_KEY_BRIGHTNESS]

    @property
    def is_on(self) -> bool:
        """Return True if the entity is on."""
        return self._state_dict[STATE_KEY_STATE]

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the light on or set a specific dimmer value."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        self._ads_hub.write_by_name(self._ads_var, True, pyads.PLCTYPE_BOOL)

        if self._ads_var_brightness is not None and brightness is not None:
            # Scale brightness from HA range (0-255) to PLC range (0-brightness_scale)
            scaled_brightness = int(brightness * self._brightness_scale / 255)
            self._ads_hub.write_by_name(
                self._ads_var_brightness, scaled_brightness, pyads.PLCTYPE_UINT
            )

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        self._ads_hub.write_by_name(self._ads_var, False, pyads.PLCTYPE_BOOL)
