"""Support for ADS covers."""

from __future__ import annotations

import logging
from typing import Any

import pyads
import voluptuous as vol

from homeassistant.components.cover import (
    ATTR_POSITION,
    DEVICE_CLASSES_SCHEMA,
    PLATFORM_SCHEMA as COVER_PLATFORM_SCHEMA,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
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
DEFAULT_NAME = "ADS Cover"

CONF_ADS_VAR_SET_POS = "adsvar_set_position"
CONF_ADS_VAR_OPEN = "adsvar_open"
CONF_ADS_VAR_CLOSE = "adsvar_close"
CONF_ADS_VAR_STOP = "adsvar_stop"
CONF_ADS_VAR_POSITION = "adsvar_position"
CONF_ADS_VAR_POSITION_TYPE = "adsvar_position_type"
CONF_INVERTED = "inverted"

STATE_KEY_POSITION = "position"

# Default to BYTE for backwards compatibility
DEFAULT_POSITION_TYPE = "byte"

PLATFORM_SCHEMA = COVER_PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_ADS_VAR): cv.string,
        vol.Optional(CONF_ADS_VAR_POSITION): cv.string,
        vol.Optional(CONF_ADS_VAR_POSITION_TYPE, default=DEFAULT_POSITION_TYPE): vol.In(["byte", "uint"]),
        vol.Optional(CONF_ADS_VAR_SET_POS): cv.string,
        vol.Optional(CONF_ADS_VAR_CLOSE): cv.string,
        vol.Optional(CONF_ADS_VAR_OPEN): cv.string,
        vol.Optional(CONF_ADS_VAR_STOP): cv.string,
        vol.Optional(CONF_INVERTED, default=False): cv.boolean,
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
    """Set up the cover platform for ADS."""
    ads_hub = hass.data.get(DOMAIN, {}).get("connection")
    
    if ads_hub is None:
        _LOGGER.error(
            "No ADS connection configured. Please add 'ads_custom:' "
            "section to your configuration.yaml"
        )
        return

    ads_var_is_closed: str | None = config.get(CONF_ADS_VAR)
    ads_var_position: str | None = config.get(CONF_ADS_VAR_POSITION)
    ads_var_position_type: str = config.get(CONF_ADS_VAR_POSITION_TYPE, DEFAULT_POSITION_TYPE)
    ads_var_pos_set: str | None = config.get(CONF_ADS_VAR_SET_POS)
    ads_var_open: str | None = config.get(CONF_ADS_VAR_OPEN)
    ads_var_close: str | None = config.get(CONF_ADS_VAR_CLOSE)
    ads_var_stop: str | None = config.get(CONF_ADS_VAR_STOP)
    inverted: bool = config.get(CONF_INVERTED, False)
    name: str = config.get(CONF_NAME, DEFAULT_NAME)
    device_class: CoverDeviceClass | None = config.get(CONF_DEVICE_CLASS)
    unique_id: str | None = config.get(CONF_UNIQUE_ID)
    
    # Validate that at least one state variable is provided
    if not ads_var_is_closed and not ads_var_position:
        _LOGGER.error(
            "Cover configuration must include either 'adsvar' (closed state) "
            "or 'adsvar_position' (position feedback)"
        )
        return

    add_entities(
        [
            AdsCover(
                ads_hub,
                ads_var_is_closed,
                ads_var_position,
                ads_var_position_type,
                ads_var_pos_set,
                ads_var_open,
                ads_var_close,
                ads_var_stop,
                inverted,
                name,
                device_class,
                unique_id,
            )
        ]
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ADS cover entities from a config entry."""
    ads_hub = hass.data[DOMAIN][entry.entry_id]
    
    # Get cover entities from config entry options
    entities = entry.options.get("entities", [])
    covers = [e for e in entities if e.get("entity_type") == "cover"]
    
    if not covers:
        return
    
    cover_entities = []
    for cover_config in covers:
        name = cover_config.get(CONF_NAME, DEFAULT_NAME)
        ads_var_is_closed = cover_config.get(CONF_ADS_VAR)
        ads_var_position = cover_config.get(CONF_ADS_VAR_POSITION)
        ads_var_position_type = cover_config.get(CONF_ADS_VAR_POSITION_TYPE, DEFAULT_POSITION_TYPE)
        ads_var_pos_set = cover_config.get(CONF_ADS_VAR_SET_POS)
        ads_var_open = cover_config.get(CONF_ADS_VAR_OPEN)
        ads_var_close = cover_config.get(CONF_ADS_VAR_CLOSE)
        ads_var_stop = cover_config.get(CONF_ADS_VAR_STOP)
        inverted = cover_config.get(CONF_INVERTED, False)
        device_class = cover_config.get(CONF_DEVICE_CLASS)
        unique_id = cover_config.get(CONF_UNIQUE_ID)
        
        # Validate that at least one state variable is provided
        if not ads_var_is_closed and not ads_var_position:
            _LOGGER.warning(
                "Cover configuration for '%s' must include either 'adsvar' (closed state) "
                "or 'adsvar_position' (position feedback). Skipping.",
                name
            )
            continue
        
        cover_entities.append(
            AdsCover(
                ads_hub,
                ads_var_is_closed,
                ads_var_position,
                ads_var_position_type,
                ads_var_pos_set,
                ads_var_open,
                ads_var_close,
                ads_var_stop,
                inverted,
                name,
                device_class,
                unique_id,
            )
        )
    
    if cover_entities:
        async_add_entities(cover_entities)


class AdsCover(AdsEntity, CoverEntity):
    """Representation of ADS cover."""

    def __init__(
        self,
        ads_hub: AdsHub,
        ads_var_closed_state: str | None,
        ads_var_position: str | None,
        ads_var_position_type: str,
        ads_var_pos_set: str | None,
        ads_var_open: str | None,
        ads_var_close: str | None,
        ads_var_stop: str | None,
        inverted: bool,
        name: str,
        device_class: CoverDeviceClass | None,
        unique_id: str | None,
    ) -> None:
        """Initialize AdsCover entity."""
        super().__init__(ads_hub, name, ads_var_closed_state, unique_id)
        if self._attr_unique_id is None:
            if ads_var_position is not None:
                self._attr_unique_id = ads_var_position
            elif ads_var_pos_set is not None:
                self._attr_unique_id = ads_var_pos_set
            elif ads_var_open is not None:
                self._attr_unique_id = ads_var_open

        self._state_dict[STATE_KEY_POSITION] = None
        self._ads_var_position = ads_var_position
        self._ads_var_position_type = ads_var_position_type
        self._ads_var_pos_set = ads_var_pos_set
        self._ads_var_open = ads_var_open
        self._ads_var_close = ads_var_close
        self._ads_var_stop = ads_var_stop
        self._inverted = inverted
        self._configured_device_class = device_class
        self._attr_supported_features = (
            CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE
        )
        if ads_var_stop is not None:
            self._attr_supported_features |= CoverEntityFeature.STOP
        if ads_var_pos_set is not None:
            self._attr_supported_features |= CoverEntityFeature.SET_POSITION

    async def async_added_to_hass(self) -> None:
        """Register device notification."""
        if self._ads_var is not None:
            await self.async_initialize_device(self._ads_var, pyads.PLCTYPE_BOOL)

        if self._ads_var_position is not None:
            # Use UINT or BYTE based on configuration
            plctype = pyads.PLCTYPE_UINT if self._ads_var_position_type == "uint" else pyads.PLCTYPE_BYTE
            await self.async_initialize_device(
                self._ads_var_position, plctype, STATE_KEY_POSITION
            )

    @property
    def device_class(self) -> CoverDeviceClass | None:
        """Return the device class of the cover.

        Checks entity registry for custom device_class first,
        then falls back to configured value.
        """
        if self.registry_entry and self.registry_entry.device_class:
            return self.registry_entry.device_class
        return self._configured_device_class

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed."""
        if self._ads_var is not None:
            return self._state_dict.get(STATE_KEY_STATE)
        if self._ads_var_position is not None:
            position = self._state_dict.get(STATE_KEY_POSITION)
            # Safe comparison handling potential type mismatches
            try:
                if self._inverted:
                    # When inverted: PLC uses 0=open, 100=closed
                    # So position == 100 means closed (raw PLC value)
                    return position == 100 if position is not None else None
                else:
                    # Normal mode: PLC uses 0=closed, 100=open
                    # So position == 0 means closed (raw PLC value)
                    return position == 0 if position is not None else None
            except (TypeError, ValueError):
                return None
        return None

    @property
    def current_cover_position(self) -> int | None:
        """Return current position of cover.
        
        Home Assistant convention: 0=closed, 100=open
        When inverted: PLC uses 0=open, 100=closed, so we convert.
        """
        position = self._state_dict.get(STATE_KEY_POSITION)
        if position is not None and self._inverted:
            # Convert PLC's inverted position to HA's expected position
            # PLC 0 (open) -> HA 100 (open)
            # PLC 100 (closed) -> HA 0 (closed)
            return 100 - position
        return position

    def stop_cover(self, **kwargs: Any) -> None:
        """Fire the stop action."""
        if self._ads_var_stop:
            self._ads_hub.write_by_name(self._ads_var_stop, True, pyads.PLCTYPE_BOOL)

    def set_cover_position(self, **kwargs: Any) -> None:
        """Set cover position.
        
        Receives HA position (0=closed, 100=open) and converts if needed.
        """
        position = kwargs[ATTR_POSITION]
        if self._ads_var_pos_set is not None:
            # When inverted, convert HA position to PLC's inverted position
            # HA 100 (open) -> PLC 0 (open in PLC's inverted logic)
            # HA 0 (closed) -> PLC 100 (closed in PLC's inverted logic)
            write_position = (100 - position) if self._inverted else position
            # Use UINT or BYTE based on configuration
            plctype = pyads.PLCTYPE_UINT if self._ads_var_position_type == "uint" else pyads.PLCTYPE_BYTE
            self._ads_hub.write_by_name(
                self._ads_var_pos_set, write_position, plctype
            )

    def open_cover(self, **kwargs: Any) -> None:
        """Move the cover up."""
        if self._ads_var_open is not None:
            self._ads_hub.write_by_name(self._ads_var_open, True, pyads.PLCTYPE_BOOL)
            # Write FALSE to close command to ensure only one command is active
            if self._ads_var_close is not None:
                self._ads_hub.write_by_name(self._ads_var_close, False, pyads.PLCTYPE_BOOL)
        elif self._ads_var_pos_set is not None:
            # Always use 100 for open in Home Assistant terms
            # set_cover_position will handle inversion if needed
            self.set_cover_position(**{ATTR_POSITION: 100})

    def close_cover(self, **kwargs: Any) -> None:
        """Move the cover down."""
        if self._ads_var_close is not None:
            self._ads_hub.write_by_name(self._ads_var_close, True, pyads.PLCTYPE_BOOL)
            # Write FALSE to open command to ensure only one command is active
            if self._ads_var_open is not None:
                self._ads_hub.write_by_name(self._ads_var_open, False, pyads.PLCTYPE_BOOL)
        elif self._ads_var_pos_set is not None:
            # Always use 0 for close in Home Assistant terms
            # set_cover_position will handle inversion if needed
            self.set_cover_position(**{ATTR_POSITION: 0})

    @property
    def available(self) -> bool:
        """Return False if state has not been updated yet."""
        if self._ads_var is not None or self._ads_var_position is not None:
            return (
                self._state_dict[STATE_KEY_STATE] is not None
                or self._state_dict[STATE_KEY_POSITION] is not None
            )
        return True
