"""Support for ADS select entities."""

from __future__ import annotations

import logging

import pyads
import voluptuous as vol

from homeassistant.components.select import (
    PLATFORM_SCHEMA as SELECT_PLATFORM_SCHEMA,
    SelectEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_UNIQUE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import CONF_ADS_VAR, DOMAIN, SUBENTRY_TYPE_ENTITY
from .entity import AdsEntity
from .hub import AdsHub

_LOGGER = logging.getLogger(__name__)
DEFAULT_NAME = "ADS select"

CONF_OPTIONS = "options"

PLATFORM_SCHEMA = SELECT_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ADS_VAR): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_OPTIONS): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_UNIQUE_ID): cv.string,
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up an ADS select device."""
    ads_hub = hass.data.get(DOMAIN, {}).get("connection")
    
    if ads_hub is None:
        _LOGGER.error(
            "No ADS connection configured. Please add 'ads_custom:' "
            "section to your configuration.yaml"
        )
        return

    ads_var: str = config.get(CONF_ADS_VAR)
    if not ads_var:
        _LOGGER.error("Missing required field adsvar in select configuration")
        return
    name: str = config.get(CONF_NAME, DEFAULT_NAME)
    options: list[str] = config.get(CONF_OPTIONS, [])
    if not options:
        _LOGGER.error("Missing required field options in select configuration")
        return
    unique_id: str | None = config.get(CONF_UNIQUE_ID)

    entity = AdsSelect(ads_hub, ads_var, name, options, unique_id)

    add_entities([entity])


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ADS select entities from a config entry's subentries."""
    ads_hub = hass.data[DOMAIN].get(entry.entry_id)
    if ads_hub is None:
        return

    for subentry in entry.subentries.values():
        if subentry.subentry_type != SUBENTRY_TYPE_ENTITY:
            continue
        if subentry.data.get("entity_type") != "select":
            continue

        name = subentry.data.get(CONF_NAME, DEFAULT_NAME)
        ads_var = subentry.data.get(CONF_ADS_VAR)
        options = subentry.data.get(CONF_OPTIONS, [])
        unique_id = subentry.data.get(CONF_UNIQUE_ID) or subentry.data.get("unique_id")

        if ads_var and options and unique_id:
            # Each subentry gets its own device using the subentry's unique_id
            device_identifiers = {(DOMAIN, subentry.unique_id)}
            device_name = name
            
            async_add_entities(
                [AdsSelect(ads_hub, ads_var, name, options, unique_id, device_name, device_identifiers, entry.entry_id)],
                config_subentry_id=subentry.subentry_id,
            )
        else:
            _LOGGER.warning(
                "Select configuration for '%s' must include 'adsvar' and 'options'. Skipping.",
                name
            )


class AdsSelect(AdsEntity, SelectEntity):
    """Representation of an ADS select entity."""

    def __init__(
        self,
        ads_hub: AdsHub,
        ads_var: str,
        name: str,
        options: list[str],
        unique_id: str | None,
        device_name: str | None = None,
        device_identifiers: set | None = None,
        config_entry_id: str | None = None,
    ) -> None:
        """Initialize the AdsSelect entity."""
        super().__init__(ads_hub, name, ads_var, unique_id, device_name, device_identifiers, config_entry_id)
        # Ensure options is a valid non-empty list
        if not options or not isinstance(options, list):
            raise ValueError(f"Select entity {name} must have a non-empty list of options")
        self._attr_options = options
        self._attr_current_option = None

    async def async_added_to_hass(self) -> None:
        """Register device notification."""
        # Register notification with custom callback for select entity
        def update_callback(name: str, value: int) -> None:
            """Handle the value update from ADS."""
            # Additional safety check for options
            if self._attr_options and 0 <= value < len(self._attr_options):
                self._attr_current_option = self._attr_options[value]
                self.schedule_update_ha_state()
            else:
                _LOGGER.warning(
                    "Invalid value %d for select %s (valid range: 0-%d)",
                    value,
                    self.name,
                    len(self._attr_options) - 1 if self._attr_options else -1,
                )

        await self.hass.async_add_executor_job(
            self._ads_hub.add_device_notification,
            self._ads_var,
            pyads.PLCTYPE_INT,
            update_callback
        )

    def select_option(self, option: str) -> None:
        """Change the selected option."""
        if option in self._attr_options:
            index = self._attr_options.index(option)
            self._ads_hub.write_by_name(self._ads_var, index, pyads.PLCTYPE_INT)
            self._attr_current_option = option
            self.schedule_update_ha_state()
