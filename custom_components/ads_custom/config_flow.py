"""Config flow for ADS Custom integration."""

from __future__ import annotations

import logging
import uuid
from typing import Any

import pyads
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE, CONF_IP_ADDRESS, CONF_NAME, CONF_PORT
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

# Device class options for dropdowns
BINARY_SENSOR_DEVICE_CLASSES = [
    "battery",
    "battery_charging",
    "carbon_monoxide",
    "cold",
    "connectivity",
    "door",
    "garage_door",
    "gas",
    "heat",
    "light",
    "lock",
    "moisture",
    "motion",
    "moving",
    "occupancy",
    "opening",
    "plug",
    "power",
    "presence",
    "problem",
    "running",
    "safety",
    "smoke",
    "sound",
    "tamper",
    "update",
    "vibration",
    "window",
]

SENSOR_DEVICE_CLASSES = [
    "apparent_power",
    "aqi",
    "atmospheric_pressure",
    "battery",
    "carbon_dioxide",
    "carbon_monoxide",
    "current",
    "data_rate",
    "data_size",
    "date",
    "distance",
    "duration",
    "energy",
    "energy_storage",
    "enum",
    "frequency",
    "gas",
    "humidity",
    "illuminance",
    "irradiance",
    "moisture",
    "monetary",
    "nitrogen_dioxide",
    "nitrogen_monoxide",
    "nitrous_oxide",
    "ozone",
    "ph",
    "pm1",
    "pm10",
    "pm25",
    "power",
    "power_factor",
    "precipitation",
    "precipitation_intensity",
    "pressure",
    "reactive_power",
    "signal_strength",
    "sound_pressure",
    "speed",
    "sulphur_dioxide",
    "temperature",
    "timestamp",
    "volatile_organic_compounds",
    "volatile_organic_compounds_parts",
    "voltage",
    "volume",
    "volume_flow_rate",
    "volume_storage",
    "water",
    "weight",
    "wind_speed",
]

COVER_DEVICE_CLASSES = [
    "awning",
    "blind",
    "curtain",
    "damper",
    "door",
    "garage",
    "gate",
    "shade",
    "shutter",
    "window",
]

VALVE_DEVICE_CLASSES = [
    "gas",
    "water",
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

    async def async_step_import(
        self, import_data: dict[str, Any]
    ) -> FlowResult:
        """Handle import from YAML configuration."""
        # Extract connection data
        device = import_data[CONF_DEVICE]
        await self.async_set_unique_id(device)
        self._abort_if_unique_id_configured()

        connection_data = {
            CONF_DEVICE: device,
            CONF_PORT: import_data.get(CONF_PORT, 48898),
        }
        if CONF_IP_ADDRESS in import_data:
            connection_data[CONF_IP_ADDRESS] = import_data[CONF_IP_ADDRESS]

        # Extract migrated entities (if any)
        entities = import_data.get("entities", [])

        return self.async_create_entry(
            title=f"ADS ({device})",
            data=connection_data,
            options={"entities": entities},
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for ADS Custom."""

    def __init__(self) -> None:
        """Initialize options flow."""
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
            elif action == "edit_entity":
                return await self.async_step_select_entity_to_edit()

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("action"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": "add_entity", "label": "Add Entity"},
                            {"value": "edit_entity", "label": "Edit Entity"},
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
            elif entity_type == "cover":
                return await self.async_step_configure_cover()
            elif entity_type == "valve":
                return await self.async_step_configure_valve()
            elif entity_type == "select":
                return await self.async_step_configure_select()
            else:
                return self.async_abort(reason="entity_type_not_supported")

        # Show all implemented entity types
        available_types = ["binary_sensor", "sensor", "switch", "light", "cover", "valve", "select"]
        
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
            # Auto-generate unique_id
            entity_config["unique_id"] = uuid.uuid4().hex
            
            # Add to entities list
            entities = list(self.config_entry.options.get("entities", []))
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
            # Auto-generate unique_id
            entity_config["unique_id"] = uuid.uuid4().hex
            
            # Add to entities list
            entities = list(self.config_entry.options.get("entities", []))
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
                vol.Optional(CONF_DEVICE_CLASS): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=SENSOR_DEVICE_CLASSES,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_STATE_CLASS): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["measurement", "total", "total_increasing"],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
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
            # Auto-generate unique_id
            entity_config["unique_id"] = uuid.uuid4().hex
            
            # Add to entities list
            entities = list(self.config_entry.options.get("entities", []))
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
                vol.Optional(CONF_DEVICE_CLASS): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=BINARY_SENSOR_DEVICE_CLASSES,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
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
            # Auto-generate unique_id
            entity_config["unique_id"] = uuid.uuid4().hex
            
            # Add to entities list
            entities = list(self.config_entry.options.get("entities", []))
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
                vol.Optional("adsvar_brightness_type", default="byte"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["byte", "uint"],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional("adsvar_brightness_scale", default=255): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=65535)
                ),
            }),
            description_placeholders={
                "entity_type": "Light",
            },
        )

    async def async_step_configure_cover(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure a cover entity."""
        if user_input is not None:
            # Merge entity type with configuration
            entity_config = {**self.entity_data, **user_input}
            # Auto-generate unique_id
            entity_config["unique_id"] = uuid.uuid4().hex
            
            # Add to entities list
            entities = list(self.config_entry.options.get("entities", []))
            entities.append(entity_config)
            
            return self.async_create_entry(
                title="",
                data={"entities": entities},
            )

        return self.async_show_form(
            step_id="configure_cover",
            data_schema=vol.Schema({
                vol.Optional(CONF_ADS_VAR): cv.string,
                vol.Required(CONF_NAME): cv.string,
                vol.Optional("adsvar_position"): cv.string,
                vol.Optional("adsvar_position_type", default="byte"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["byte", "uint"],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional("adsvar_set_position"): cv.string,
                vol.Optional("adsvar_open"): cv.string,
                vol.Optional("adsvar_close"): cv.string,
                vol.Optional("adsvar_stop"): cv.string,
                vol.Optional("inverted", default=False): cv.boolean,
                vol.Optional(CONF_DEVICE_CLASS): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=COVER_DEVICE_CLASSES,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
            description_placeholders={
                "entity_type": "Cover",
            },
        )

    async def async_step_configure_valve(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure a valve entity."""
        if user_input is not None:
            # Merge entity type with configuration
            entity_config = {**self.entity_data, **user_input}
            # Auto-generate unique_id
            entity_config["unique_id"] = uuid.uuid4().hex
            
            # Add to entities list
            entities = list(self.config_entry.options.get("entities", []))
            entities.append(entity_config)
            
            return self.async_create_entry(
                title="",
                data={"entities": entities},
            )

        return self.async_show_form(
            step_id="configure_valve",
            data_schema=vol.Schema({
                vol.Required(CONF_ADS_VAR): cv.string,
                vol.Required(CONF_NAME): cv.string,
                vol.Optional(CONF_DEVICE_CLASS): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=VALVE_DEVICE_CLASSES,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
            description_placeholders={
                "entity_type": "Valve",
            },
        )

    async def async_step_configure_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure a select entity."""
        if user_input is not None:
            # Parse options from comma-separated string or list
            options = user_input.get("options", [])
            if isinstance(options, str):
                options = [opt.strip() for opt in options.split(",") if opt.strip()]
            
            # Merge entity type with configuration
            entity_config = {**self.entity_data, **user_input}
            entity_config["options"] = options
            # Auto-generate unique_id
            entity_config["unique_id"] = uuid.uuid4().hex
            
            # Add to entities list
            entities = list(self.config_entry.options.get("entities", []))
            entities.append(entity_config)
            
            return self.async_create_entry(
                title="",
                data={"entities": entities},
            )

        return self.async_show_form(
            step_id="configure_select",
            data_schema=vol.Schema({
                vol.Required(CONF_ADS_VAR): cv.string,
                vol.Required(CONF_NAME): cv.string,
                vol.Required("options"): cv.string,
            }),
            description_placeholders={
                "entity_type": "Select",
                "options_help": "Enter options separated by commas (e.g., 'Off, Auto, Manual')",
            },
        )

    async def async_step_list_entities(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """List configured entities."""
        entities = self.config_entry.options.get("entities", [])
        
        if not entities:
            return self.async_abort(reason="no_entities")
        
        # If user submitted the form (clicked OK), return to main menu
        if user_input is not None:
            return await self.async_step_init()
        
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

    async def async_step_select_entity_to_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select an entity to edit."""
        entities = self.config_entry.options.get("entities", [])
        
        if not entities:
            return self.async_abort(reason="no_entities")
        
        if user_input is not None:
            entity_index = int(user_input.get("entity_index"))
            # Store the entity index and data for editing
            self.entity_data = {"index": entity_index, "entity": entities[entity_index].copy()}
            entity_type = entities[entity_index].get(CONF_ENTITY_TYPE)
            
            # Route to specific edit configuration based on entity type
            if entity_type == "switch":
                return await self.async_step_edit_switch()
            elif entity_type == "sensor":
                return await self.async_step_edit_sensor()
            elif entity_type == "binary_sensor":
                return await self.async_step_edit_binary_sensor()
            elif entity_type == "light":
                return await self.async_step_edit_light()
            elif entity_type == "cover":
                return await self.async_step_edit_cover()
            elif entity_type == "valve":
                return await self.async_step_edit_valve()
            elif entity_type == "select":
                return await self.async_step_edit_select()
            else:
                return self.async_abort(reason="entity_type_not_supported")
        
        # Create list of entities with their indices
        entity_options = [
            {
                "value": str(idx),
                "label": f"{e.get(CONF_NAME, 'Unnamed')} ({e.get(CONF_ENTITY_TYPE, 'unknown')})"
            }
            for idx, e in enumerate(entities)
        ]
        
        return self.async_show_form(
            step_id="select_entity_to_edit",
            data_schema=vol.Schema({
                vol.Required("entity_index"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=entity_options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
        )

    async def async_step_edit_switch(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Edit a switch entity."""
        if user_input is not None:
            # Update the entity with new values
            entities = list(self.config_entry.options.get("entities", []))
            entity_index = self.entity_data["index"]
            entities[entity_index].update(user_input)
            
            return self.async_create_entry(
                title="",
                data={"entities": entities},
            )
        
        entity = self.entity_data["entity"]
        return self.async_show_form(
            step_id="edit_switch",
            data_schema=vol.Schema({
                vol.Required(CONF_ADS_VAR, default=entity.get(CONF_ADS_VAR, "")): cv.string,
                vol.Required(CONF_NAME, default=entity.get(CONF_NAME, "")): cv.string,
            }),
            description_placeholders={
                "entity_type": "Switch",
            },
        )

    async def async_step_edit_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Edit a sensor entity."""
        if user_input is not None:
            # Update the entity with new values
            entities = list(self.config_entry.options.get("entities", []))
            entity_index = self.entity_data["index"]
            entities[entity_index].update(user_input)
            
            return self.async_create_entry(
                title="",
                data={"entities": entities},
            )
        
        entity = self.entity_data["entity"]
        
        # Build schema with conditional defaults for optional fields
        schema_dict: dict[Any, Any] = {
            vol.Required(CONF_ADS_VAR, default=entity.get(CONF_ADS_VAR, "")): cv.string,
            vol.Required(CONF_NAME, default=entity.get(CONF_NAME, "")): cv.string,
            vol.Optional(CONF_ADS_TYPE, default=entity.get(CONF_ADS_TYPE, "int")): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[t.value for t in AdsType],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
        }
        
        # Only add default for unit_of_measurement if it has a value
        unit = entity.get(CONF_UNIT_OF_MEASUREMENT)
        if unit:
            schema_dict[vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=unit)] = cv.string
        else:
            schema_dict[vol.Optional(CONF_UNIT_OF_MEASUREMENT)] = cv.string
        
        # Only add default for device_class if it has a non-empty value
        device_class = entity.get(CONF_DEVICE_CLASS)
        if device_class:
            schema_dict[vol.Optional(CONF_DEVICE_CLASS, default=device_class)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SENSOR_DEVICE_CLASSES,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        else:
            schema_dict[vol.Optional(CONF_DEVICE_CLASS)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SENSOR_DEVICE_CLASSES,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        
        # Only add default for state_class if it has a non-empty value
        state_class = entity.get(CONF_STATE_CLASS)
        if state_class:
            schema_dict[vol.Optional(CONF_STATE_CLASS, default=state_class)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["measurement", "total", "total_increasing"],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        else:
            schema_dict[vol.Optional(CONF_STATE_CLASS)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["measurement", "total", "total_increasing"],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        
        return self.async_show_form(
            step_id="edit_sensor",
            data_schema=vol.Schema(schema_dict),
            description_placeholders={
                "entity_type": "Sensor",
            },
        )

    async def async_step_edit_binary_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Edit a binary sensor entity."""
        if user_input is not None:
            # Update the entity with new values
            entities = list(self.config_entry.options.get("entities", []))
            entity_index = self.entity_data["index"]
            entities[entity_index].update(user_input)
            
            return self.async_create_entry(
                title="",
                data={"entities": entities},
            )
        
        entity = self.entity_data["entity"]
        
        # Build schema with conditional defaults
        schema_dict: dict[Any, Any] = {
            vol.Required(CONF_ADS_VAR, default=entity.get(CONF_ADS_VAR, "")): cv.string,
            vol.Required(CONF_NAME, default=entity.get(CONF_NAME, "")): cv.string,
            vol.Optional(CONF_ADS_TYPE, default=entity.get(CONF_ADS_TYPE, "bool")): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["bool", "real"],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
        }
        
        # Only add default for device_class if it has a non-empty value
        device_class = entity.get(CONF_DEVICE_CLASS)
        if device_class:
            schema_dict[vol.Optional(CONF_DEVICE_CLASS, default=device_class)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=BINARY_SENSOR_DEVICE_CLASSES,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        else:
            schema_dict[vol.Optional(CONF_DEVICE_CLASS)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=BINARY_SENSOR_DEVICE_CLASSES,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        
        return self.async_show_form(
            step_id="edit_binary_sensor",
            data_schema=vol.Schema(schema_dict),
            description_placeholders={
                "entity_type": "Binary Sensor",
            },
        )

    async def async_step_edit_light(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Edit a light entity."""
        if user_input is not None:
            # Update the entity with new values
            entities = list(self.config_entry.options.get("entities", []))
            entity_index = self.entity_data["index"]
            entities[entity_index].update(user_input)
            
            return self.async_create_entry(
                title="",
                data={"entities": entities},
            )
        
        entity = self.entity_data["entity"]
        return self.async_show_form(
            step_id="edit_light",
            data_schema=vol.Schema({
                vol.Required(CONF_ADS_VAR, default=entity.get(CONF_ADS_VAR, "")): cv.string,
                vol.Required(CONF_NAME, default=entity.get(CONF_NAME, "")): cv.string,
                vol.Optional("adsvar_brightness", default=entity.get("adsvar_brightness", "")): cv.string,
                vol.Optional("adsvar_brightness_type", default=entity.get("adsvar_brightness_type", "byte")): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["byte", "uint"],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional("adsvar_brightness_scale", default=entity.get("adsvar_brightness_scale", 255)): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=65535)
                ),
            }),
            description_placeholders={
                "entity_type": "Light",
            },
        )

    async def async_step_edit_cover(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Edit a cover entity."""
        if user_input is not None:
            # Update the entity with new values
            entities = list(self.config_entry.options.get("entities", []))
            entity_index = self.entity_data["index"]
            entities[entity_index].update(user_input)
            
            return self.async_create_entry(
                title="",
                data={"entities": entities},
            )
        
        entity = self.entity_data["entity"]
        
        # Build schema with conditional defaults
        schema_dict: dict[Any, Any] = {
            vol.Required(CONF_NAME, default=entity.get(CONF_NAME, "")): cv.string,
            vol.Optional("adsvar_position_type", default=entity.get("adsvar_position_type", "byte")): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["byte", "uint"],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional("inverted", default=entity.get("inverted", False)): cv.boolean,
        }
        
        # Add optional string fields with defaults only if they have values
        for field in [CONF_ADS_VAR, "adsvar_position", "adsvar_set_position", "adsvar_open", "adsvar_close", "adsvar_stop"]:
            value = entity.get(field)
            if value:
                schema_dict[vol.Optional(field, default=value)] = cv.string
            else:
                schema_dict[vol.Optional(field)] = cv.string
        
        # Only add default for device_class if it has a non-empty value
        device_class = entity.get(CONF_DEVICE_CLASS)
        if device_class:
            schema_dict[vol.Optional(CONF_DEVICE_CLASS, default=device_class)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=COVER_DEVICE_CLASSES,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        else:
            schema_dict[vol.Optional(CONF_DEVICE_CLASS)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=COVER_DEVICE_CLASSES,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        
        return self.async_show_form(
            step_id="edit_cover",
            data_schema=vol.Schema(schema_dict),
            description_placeholders={
                "entity_type": "Cover",
            },
        )

    async def async_step_edit_valve(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Edit a valve entity."""
        if user_input is not None:
            # Update the entity with new values
            entities = list(self.config_entry.options.get("entities", []))
            entity_index = self.entity_data["index"]
            entities[entity_index].update(user_input)
            
            return self.async_create_entry(
                title="",
                data={"entities": entities},
            )
        
        entity = self.entity_data["entity"]
        
        # Build schema with conditional defaults
        schema_dict: dict[Any, Any] = {
            vol.Required(CONF_ADS_VAR, default=entity.get(CONF_ADS_VAR, "")): cv.string,
            vol.Required(CONF_NAME, default=entity.get(CONF_NAME, "")): cv.string,
        }
        
        # Only add default for device_class if it has a non-empty value
        device_class = entity.get(CONF_DEVICE_CLASS)
        if device_class:
            schema_dict[vol.Optional(CONF_DEVICE_CLASS, default=device_class)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=VALVE_DEVICE_CLASSES,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        else:
            schema_dict[vol.Optional(CONF_DEVICE_CLASS)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=VALVE_DEVICE_CLASSES,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        
        return self.async_show_form(
            step_id="edit_valve",
            data_schema=vol.Schema(schema_dict),
            description_placeholders={
                "entity_type": "Valve",
            },
        )

    async def async_step_edit_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Edit a select entity."""
        if user_input is not None:
            # Parse options from comma-separated string or list
            options = user_input.get("options", [])
            if isinstance(options, str):
                options = [opt.strip() for opt in options.split(",") if opt.strip()]
            
            # Update the entity with new values
            entities = list(self.config_entry.options.get("entities", []))
            entity_index = self.entity_data["index"]
            user_input["options"] = options
            entities[entity_index].update(user_input)
            
            return self.async_create_entry(
                title="",
                data={"entities": entities},
            )
        
        entity = self.entity_data["entity"]
        # Convert list of options to comma-separated string for display
        options = entity.get("options", [])
        if isinstance(options, list):
            options_str = ", ".join(options)
        else:
            options_str = str(options) if options else ""
        return self.async_show_form(
            step_id="edit_select",
            data_schema=vol.Schema({
                vol.Required(CONF_ADS_VAR, default=entity.get(CONF_ADS_VAR, "")): cv.string,
                vol.Required(CONF_NAME, default=entity.get(CONF_NAME, "")): cv.string,
                vol.Required("options", default=options_str): cv.string,
            }),
            description_placeholders={
                "entity_type": "Select",
                "options_help": "Enter options separated by commas (e.g., 'Off, Auto, Manual')",
            },
        )
