"""Config flow for ADS Custom integration."""

from __future__ import annotations

import logging
from typing import Any

import pyads
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE, CONF_IP_ADDRESS, CONF_NAME, CONF_PORT, CONF_UNIQUE_ID
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .const import CONF_ADS_VAR, DOMAIN, AdsType

_LOGGER = logging.getLogger(__name__)

# Entity type constants
CONF_ENTITY_TYPE = "entity_type"
CONF_ADS_TYPE = "adstype"
CONF_DEVICE_CLASS = "device_class"
CONF_UNIT_OF_MEASUREMENT = "unit_of_measurement"
CONF_STATE_CLASS = "state_class"

ENTITY_TYPES = [
    "binary_sensor",
    "sensor",
    "switch",
    "light",
    "cover",
    "valve",
    "select",
]

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE): cv.string,
        vol.Optional(CONF_IP_ADDRESS): cv.string,
        vol.Optional(CONF_PORT, default=48898): cv.port,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    net_id = data[CONF_DEVICE]
    ip_address = data.get(CONF_IP_ADDRESS)
    port = data.get(CONF_PORT, 48898)

    # Test connection
    def test_connection():
        """Test the ADS connection."""
        client = pyads.Connection(net_id, port, ip_address)
        try:
            client.open()
            client.close()
            return True
        except pyads.ADSError as err:
            _LOGGER.error("Connection test failed: %s", err)
            raise

    try:
        await hass.async_add_executor_job(test_connection)
    except pyads.ADSError as err:
        raise CannotConnect from err

    # Return info that you want to store in the config entry.
    return {"title": f"ADS ({net_id})"}


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ADS Custom."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Create a unique ID based on the device (AMS Net ID)
                await self.async_set_unique_id(user_input[CONF_DEVICE])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=user_input, options={"entities": []})

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for ADS Custom."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self.entity_data = {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            action = user_input.get("action")
            if action == "add_entity":
                return await self.async_step_add_entity()
            elif action == "list_entities":
                return await self.async_step_list_entities()

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("action"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": "add_entity", "label": "Add Entity"},
                            {"value": "list_entities", "label": "List Entities"},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
        )

    async def async_step_add_entity(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add a new entity."""
        if user_input is not None:
            self.entity_data = user_input
            entity_type = user_input[CONF_ENTITY_TYPE]
            
            # Route to specific entity configuration
            if entity_type == "switch":
                return await self.async_step_configure_switch()
            elif entity_type == "sensor":
                return await self.async_step_configure_sensor()
            elif entity_type == "binary_sensor":
                return await self.async_step_configure_binary_sensor()
            elif entity_type == "light":
                return await self.async_step_configure_light()
            # Cover, valve, and select not yet implemented via UI
            else:
                return self.async_abort(reason="entity_type_not_supported")

        # Only show implemented entity types
        available_types = ["binary_sensor", "sensor", "switch", "light"]
        
        return self.async_show_form(
            step_id="add_entity",
            data_schema=vol.Schema({
                vol.Required(CONF_ENTITY_TYPE): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=available_types,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
        )

    async def async_step_configure_switch(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure a switch entity."""
        if user_input is not None:
            # Merge entity type with configuration
            entity_config = {**self.entity_data, **user_input}
            
            # Add to entities list
            entities = self.config_entry.options.get("entities", [])
            entities.append(entity_config)
            
            return self.async_create_entry(
                title="",
                data={"entities": entities},
            )

        return self.async_show_form(
            step_id="configure_switch",
            data_schema=vol.Schema({
                vol.Required(CONF_ADS_VAR): cv.string,
                vol.Required(CONF_NAME): cv.string,
                vol.Optional(CONF_UNIQUE_ID): cv.string,
            }),
            description_placeholders={
                "entity_type": "Switch",
            },
        )

    async def async_step_configure_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure a sensor entity."""
        if user_input is not None:
            # Merge entity type with configuration
            entity_config = {**self.entity_data, **user_input}
            
            # Add to entities list
            entities = self.config_entry.options.get("entities", [])
            entities.append(entity_config)
            
            return self.async_create_entry(
                title="",
                data={"entities": entities},
            )

        return self.async_show_form(
            step_id="configure_sensor",
            data_schema=vol.Schema({
                vol.Required(CONF_ADS_VAR): cv.string,
                vol.Required(CONF_NAME): cv.string,
                vol.Optional(CONF_ADS_TYPE, default="int"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[t.value for t in AdsType],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
                vol.Optional(CONF_DEVICE_CLASS): cv.string,
                vol.Optional(CONF_STATE_CLASS): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["measurement", "total", "total_increasing"],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_UNIQUE_ID): cv.string,
            }),
            description_placeholders={
                "entity_type": "Sensor",
            },
        )

    async def async_step_configure_binary_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure a binary sensor entity."""
        if user_input is not None:
            # Merge entity type with configuration
            entity_config = {**self.entity_data, **user_input}
            
            # Add to entities list
            entities = self.config_entry.options.get("entities", [])
            entities.append(entity_config)
            
            return self.async_create_entry(
                title="",
                data={"entities": entities},
            )

        return self.async_show_form(
            step_id="configure_binary_sensor",
            data_schema=vol.Schema({
                vol.Required(CONF_ADS_VAR): cv.string,
                vol.Required(CONF_NAME): cv.string,
                vol.Optional(CONF_ADS_TYPE, default="bool"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["bool", "real"],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_DEVICE_CLASS): cv.string,
                vol.Optional(CONF_UNIQUE_ID): cv.string,
            }),
            description_placeholders={
                "entity_type": "Binary Sensor",
            },
        )

    async def async_step_configure_light(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure a light entity."""
        if user_input is not None:
            # Merge entity type with configuration
            entity_config = {**self.entity_data, **user_input}
            
            # Add to entities list
            entities = self.config_entry.options.get("entities", [])
            entities.append(entity_config)
            
            return self.async_create_entry(
                title="",
                data={"entities": entities},
            )

        return self.async_show_form(
            step_id="configure_light",
            data_schema=vol.Schema({
                vol.Required(CONF_ADS_VAR): cv.string,
                vol.Required(CONF_NAME): cv.string,
                vol.Optional("adsvar_brightness"): cv.string,
                vol.Optional("adsvar_brightness_scale", default=255): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=65535)
                ),
                vol.Optional(CONF_UNIQUE_ID): cv.string,
            }),
            description_placeholders={
                "entity_type": "Light",
            },
        )

    async def async_step_list_entities(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """List configured entities."""
        entities = self.config_entry.options.get("entities", [])
        
        if not entities:
            return self.async_abort(reason="no_entities")
        
        # Create a readable list of entities
        entity_list = "\n".join([
            f"- {e.get(CONF_NAME, 'Unnamed')} ({e.get(CONF_ENTITY_TYPE, 'unknown')})"
            for e in entities
        ])
        
        return self.async_show_form(
            step_id="list_entities",
            data_schema=vol.Schema({}),
            description_placeholders={"entity_list": entity_list},
        )
