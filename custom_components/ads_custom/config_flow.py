"""Config flow for Automation Device Specification (ADS) integration."""

from __future__ import annotations

import logging
from typing import Any

import pyads
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_DEVICE, CONF_IP_ADDRESS, CONF_NAME, CONF_PORT
from homeassistant.core import callback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DEFAULT_PORT = 48898

# Entity types supported
ENTITY_TYPES = {
    "light": "Light",
    "switch": "Switch",
    "binary_sensor": "Binary Sensor",
    "sensor": "Sensor",
    "cover": "Cover",
    "valve": "Valve",
    "select": "Select",
}


def _base_schema(ads_config: dict[str, Any] | None = None) -> vol.Schema:
    """Generate base schema."""
    if ads_config is None:
        ads_config = {}

    return vol.Schema(
        {
            vol.Required(
                CONF_DEVICE, default=ads_config.get(CONF_DEVICE, "")
            ): str,
            vol.Optional(
                CONF_IP_ADDRESS, default=ads_config.get(CONF_IP_ADDRESS, "")
            ): str,
            vol.Optional(
                CONF_PORT, default=ads_config.get(CONF_PORT, DEFAULT_PORT)
            ): int,
        }
    )


async def validate_input(data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from _base_schema with values provided by the user.
    """
    net_id = data[CONF_DEVICE]
    ip_address = data.get(CONF_IP_ADDRESS) or None
    port = data[CONF_PORT]

    # Test the connection
    client = pyads.Connection(net_id, port, ip_address)
    try:
        client.open()
        # Try to read device info to verify connection
        device_info = client.read_device_info()
        client.close()
    except pyads.ADSError as err:
        _LOGGER.error("Failed to connect to ADS device: %s", err)
        raise

    return {"title": f"ADS {net_id}", "device_info": device_info}


def _format_device(user_input: dict[str, Any]) -> str:
    """Format device info for display."""
    net_id = user_input[CONF_DEVICE]
    ip_address = user_input.get(CONF_IP_ADDRESS)
    port = user_input[CONF_PORT]

    if ip_address:
        return f"{net_id} ({ip_address}:{port})"
    return f"{net_id}:{port}"


class AdsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ADS."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the ADS config flow."""
        self.ads_config: dict[str, Any] = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> AdsOptionsFlow:
        """Get the options flow for this handler."""
        return AdsOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        description_placeholders: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(user_input)
            except pyads.ADSError as ex:
                errors["base"] = "cannot_connect"
                description_placeholders["error"] = str(ex)
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Check if already configured
                await self.async_set_unique_id(user_input[CONF_DEVICE])
                self._abort_if_unique_id_configured()

                title = info["title"]
                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_base_schema(self.ads_config),
            errors=errors,
            description_placeholders=description_placeholders,
        )


class AdsOptionsFlow(OptionsFlow):
    """Handle options flow for ADS integration."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self.entity_config: dict[str, Any] = {}
        self.entity_type: str | None = None
        self.editing_entity_id: str | None = None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["add_entity", "list_entities"],
        )

    async def async_step_add_entity(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add a new entity."""
        if user_input is not None:
            self.entity_type = user_input["entity_type"]
            return await self.async_step_configure_entity()

        return self.async_show_form(
            step_id="add_entity",
            data_schema=vol.Schema(
                {
                    vol.Required("entity_type"): vol.In(ENTITY_TYPES),
                }
            ),
        )

    async def async_step_configure_entity(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure the entity based on type."""
        if user_input is not None:
            # Process select options if it's a select entity
            if self.entity_type == "select" and "options" in user_input:
                # Convert comma-separated string to list
                options_str = user_input["options"].strip()
                user_input["options"] = [opt.strip() for opt in options_str.split(",") if opt.strip()]
            
            # Store the entity configuration
            entities = dict(self.config_entry.options.get("entities", {}))
            entity_id = user_input.get("entity_id") or f"{self.entity_type}_{len(entities)}"
            
            entities[entity_id] = {
                "type": self.entity_type,
                **user_input,
            }
            
            return self.async_create_entry(title="", data={"entities": entities})

        # Build schema based on entity type
        schema = self._get_entity_schema(self.entity_type)
        
        return self.async_show_form(
            step_id="configure_entity",
            data_schema=schema,
            description_placeholders={"entity_type": ENTITY_TYPES.get(self.entity_type, self.entity_type)},
        )

    async def async_step_list_entities(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """List and manage existing entities."""
        entities = self.config_entry.options.get("entities", {})
        
        if not entities:
            return self.async_abort(reason="no_entities")

        if user_input is not None:
            entity_id = user_input["entity"]
            self.editing_entity_id = entity_id
            
            return await self.async_step_manage_entity()

        entity_choices = {
            entity_id: f"{config.get('name', entity_id)} ({config['type']})"
            for entity_id, config in entities.items()
        }

        return self.async_show_form(
            step_id="list_entities",
            data_schema=vol.Schema(
                {
                    vol.Required("entity"): vol.In(entity_choices),
                }
            ),
        )

    async def async_step_manage_entity(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage an entity (edit or remove)."""
        return self.async_show_menu(
            step_id="manage_entity",
            menu_options=["edit_entity", "remove_entity"],
        )

    async def async_step_edit_entity(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Edit an existing entity."""
        # Check if editing_entity_id is set
        if self.editing_entity_id is None:
            return await self.async_step_init()

        entities = dict(self.config_entry.options.get("entities", {}))
        entity_config = entities.get(self.editing_entity_id, {})

        # Check if entity exists
        if not entity_config or "type" not in entity_config:
            return await self.async_step_init()
        if user_input is not None:
            # Process select options if it's a select entity
            if entity_config["type"] == "select" and "options" in user_input:
                # Convert comma-separated string to list
                options_str = user_input["options"].strip()
                user_input["options"] = [opt.strip() for opt in options_str.split(",") if opt.strip()]
            
            entities[self.editing_entity_id] = {
                "type": entity_config["type"],
                **user_input,
            }
            return self.async_create_entry(title="", data={"entities": entities})

        self.entity_type = entity_config["type"]
        schema = self._get_entity_schema(self.entity_type, entity_config)
        
        return self.async_show_form(
            step_id="edit_entity",
            data_schema=schema,
        )

    async def async_step_remove_entity(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Remove an entity."""
        # Check if editing_entity_id is set
        if self.editing_entity_id is None:
            return await self.async_step_init()

        if user_input is not None:
            entities = dict(self.config_entry.options.get("entities", {}))
            
            if self.editing_entity_id in entities:
                del entities[self.editing_entity_id]
            
            return self.async_create_entry(title="", data={"entities": entities})
        
        # Show confirmation form
        entity_config = self.config_entry.options.get("entities", {}).get(
            self.editing_entity_id, {}
        )
        entity_name = entity_config.get("name", self.editing_entity_id)
        
        return self.async_show_form(
            step_id="remove_entity",
            data_schema=vol.Schema({}),
            description_placeholders={"entity_name": entity_name},
        )

    def _get_entity_schema(
        self, entity_type: str, existing_config: dict[str, Any] | None = None
    ) -> vol.Schema:
        """Get the configuration schema for an entity type."""
        if existing_config is None:
            existing_config = {}

        base_schema = {
            vol.Optional("entity_id", default=existing_config.get("entity_id", "")): str,
            vol.Required("name", default=existing_config.get("name", "")): str,
            vol.Required("adsvar", default=existing_config.get("adsvar", "")): str,
        }

        if entity_type == "light":
            base_schema.update({
                vol.Optional(
                    "adsvar_brightness",
                    default=existing_config.get("adsvar_brightness", ""),
                ): str,
                vol.Optional(
                    "adsvar_brightness_scale",
                    default=existing_config.get("adsvar_brightness_scale", 255),
                ): int,
                vol.Optional(
                    "adsvar_brightness_type",
                    default=existing_config.get("adsvar_brightness_type", "byte"),
                ): vol.In(["byte", "uint"]),
            })
        elif entity_type == "sensor":
            base_schema.update({
                vol.Optional(
                    "adstype",
                    default=existing_config.get("adstype", "int"),
                ): vol.In(["bool", "byte", "int", "uint", "sint", "usint", "dint", "udint", "word", "dword", "real", "lreal"]),
                vol.Optional(
                    "unit_of_measurement",
                    default=existing_config.get("unit_of_measurement", ""),
                ): str,
                vol.Optional(
                    "device_class",
                    default=existing_config.get("device_class", ""),
                ): str,
                vol.Optional(
                    "state_class",
                    default=existing_config.get("state_class", ""),
                ): str,
                vol.Optional(
                    "factor",
                    default=existing_config.get("factor", 1),
                ): int,
            })
        elif entity_type == "cover":
            base_schema.update({
                vol.Optional(
                    "adsvar_position",
                    default=existing_config.get("adsvar_position", ""),
                ): str,
                vol.Optional(
                    "adsvar_set_position",
                    default=existing_config.get("adsvar_set_position", ""),
                ): str,
                vol.Optional(
                    "adsvar_open",
                    default=existing_config.get("adsvar_open", ""),
                ): str,
                vol.Optional(
                    "adsvar_close",
                    default=existing_config.get("adsvar_close", ""),
                ): str,
                vol.Optional(
                    "adsvar_stop",
                    default=existing_config.get("adsvar_stop", ""),
                ): str,
                vol.Optional(
                    "device_class",
                    default=existing_config.get("device_class", ""),
                ): str,
            })
        elif entity_type == "binary_sensor":
            base_schema.update({
                vol.Optional(
                    "device_class",
                    default=existing_config.get("device_class", ""),
                ): str,
            })
        elif entity_type == "valve":
            base_schema.update({
                vol.Optional(
                    "device_class",
                    default=existing_config.get("device_class", ""),
                ): str,
            })
        elif entity_type == "select":
            # Options should be a comma-separated list in the UI
            options_str = existing_config.get("options", "")
            if isinstance(options_str, list):
                options_str = ",".join(options_str)
            base_schema.update({
                vol.Required(
                    "options",
                    default=options_str,
                ): str,
            })
        # switch has only base fields

        return vol.Schema(base_schema)
