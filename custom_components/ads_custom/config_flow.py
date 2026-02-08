"""Config flow for ADS Custom integration."""

from __future__ import annotations

import logging
import uuid
from typing import Any

import pyads
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.const import CONF_DEVICE, CONF_IP_ADDRESS, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .const import CONF_ADS_VAR, DOMAIN, AdsType, SUBENTRY_TYPE_ENTITY

_LOGGER = logging.getLogger(__name__)

# Entity type constants
CONF_ENTITY_TYPE = "entity_type"
CONF_ADS_TYPE = "adstype"
CONF_DEVICE_CLASS = "device_class"
CONF_UNIT_OF_MEASUREMENT = "unit_of_measurement"
CONF_STATE_CLASS = "state_class"

# Cover ADS variable field names (for sanitization)
COVER_ADS_VAR_FIELDS = [
    CONF_ADS_VAR,
    "adsvar_position",
    "adsvar_set_position",
    "adsvar_open",
    "adsvar_close",
    "adsvar_stop",
]

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


class AdsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ADS Custom."""

    VERSION = 1

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Return subentries supported by this handler."""
        return {SUBENTRY_TYPE_ENTITY: AdsEntitySubentryFlowHandler}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
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

                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_import(
        self, import_data: dict[str, Any]
    ) -> ConfigFlowResult:
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

        # Store migrated entities in options for later migration to subentries
        entities = import_data.get("entities", [])

        return self.async_create_entry(
            title=f"ADS ({device})",
            data=connection_data,
            options={"entities": entities},
        )


class AdsEntitySubentryFlowHandler(ConfigSubentryFlow):
    """Handle ADS entity subentry flow for adding/editing entities."""

    _entity_data: dict[str, Any]

    # ── Add new entity ──────────────────────────────────────────────

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Select entity type to add."""
        if user_input is not None:
            self._entity_data = user_input
            entity_type = user_input[CONF_ENTITY_TYPE]

            if entity_type == "switch":
                return await self.async_step_configure_switch()
            if entity_type == "sensor":
                return await self.async_step_configure_sensor()
            if entity_type == "binary_sensor":
                return await self.async_step_configure_binary_sensor()
            if entity_type == "light":
                return await self.async_step_configure_light()
            if entity_type == "cover":
                return await self.async_step_configure_cover()
            if entity_type == "valve":
                return await self.async_step_configure_valve()
            if entity_type == "select":
                return await self.async_step_configure_select()

            return self.async_abort(reason="entity_type_not_supported")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ENTITY_TYPE): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=ENTITY_TYPES,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
        )

    # ── Configure new entities ──────────────────────────────────────

    async def async_step_configure_switch(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Configure a switch entity."""
        if user_input is not None:
            unique_id = uuid.uuid4().hex
            return self.async_create_entry(
                title=f"{user_input[CONF_NAME]} (Switch)",
                data={
                    CONF_ENTITY_TYPE: "switch",
                    **user_input,
                    "unique_id": unique_id,
                },
                unique_id=unique_id,
            )

        return self.async_show_form(
            step_id="configure_switch",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADS_VAR): cv.string,
                    vol.Required(CONF_NAME): cv.string,
                }
            ),
        )

    async def async_step_configure_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Configure a sensor entity."""
        if user_input is not None:
            unique_id = uuid.uuid4().hex
            return self.async_create_entry(
                title=f"{user_input[CONF_NAME]} (Sensor)",
                data={
                    CONF_ENTITY_TYPE: "sensor",
                    **user_input,
                    "unique_id": unique_id,
                },
                unique_id=unique_id,
            )

        return self.async_show_form(
            step_id="configure_sensor",
            data_schema=vol.Schema(
                {
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
                }
            ),
        )

    async def async_step_configure_binary_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Configure a binary sensor entity."""
        if user_input is not None:
            unique_id = uuid.uuid4().hex
            return self.async_create_entry(
                title=f"{user_input[CONF_NAME]} (Binary Sensor)",
                data={
                    CONF_ENTITY_TYPE: "binary_sensor",
                    **user_input,
                    "unique_id": unique_id,
                },
                unique_id=unique_id,
            )

        return self.async_show_form(
            step_id="configure_binary_sensor",
            data_schema=vol.Schema(
                {
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
                }
            ),
        )

    async def async_step_configure_light(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Configure a light entity."""
        if user_input is not None:
            unique_id = uuid.uuid4().hex
            return self.async_create_entry(
                title=f"{user_input[CONF_NAME]} (Light)",
                data={
                    CONF_ENTITY_TYPE: "light",
                    **user_input,
                    "unique_id": unique_id,
                },
                unique_id=unique_id,
            )

        return self.async_show_form(
            step_id="configure_light",
            data_schema=vol.Schema(
                {
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
                }
            ),
        )

    async def async_step_configure_cover(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Configure a cover entity."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Sanitize optional ADS variable fields
            for var in COVER_ADS_VAR_FIELDS:
                if var in user_input and isinstance(user_input[var], str) and not user_input[var].strip():
                    user_input.pop(var)

            if not user_input.get(CONF_ADS_VAR) and not user_input.get("adsvar_position"):
                errors["base"] = "no_state_var"

            if not errors:
                unique_id = uuid.uuid4().hex
                return self.async_create_entry(
                    title=f"{user_input[CONF_NAME]} (Cover)",
                    data={
                        CONF_ENTITY_TYPE: "cover",
                        **user_input,
                        "unique_id": unique_id,
                    },
                    unique_id=unique_id,
                )

        return self.async_show_form(
            step_id="configure_cover",
            data_schema=vol.Schema(
                {
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
                }
            ),
            errors=errors,
        )

    async def async_step_configure_valve(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Configure a valve entity."""
        if user_input is not None:
            unique_id = uuid.uuid4().hex
            return self.async_create_entry(
                title=f"{user_input[CONF_NAME]} (Valve)",
                data={
                    CONF_ENTITY_TYPE: "valve",
                    **user_input,
                    "unique_id": unique_id,
                },
                unique_id=unique_id,
            )

        return self.async_show_form(
            step_id="configure_valve",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADS_VAR): cv.string,
                    vol.Required(CONF_NAME): cv.string,
                    vol.Optional(CONF_DEVICE_CLASS): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=VALVE_DEVICE_CLASSES,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
        )

    async def async_step_configure_select(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Configure a select entity."""
        errors: dict[str, str] = {}

        if user_input is not None:
            options = user_input.get("options", [])
            if isinstance(options, str):
                options = [opt.strip() for opt in options.split(",") if opt.strip()]

            if not options:
                errors["options"] = "no_options"

            if not errors:
                unique_id = uuid.uuid4().hex
                return self.async_create_entry(
                    title=f"{user_input[CONF_NAME]} (Select)",
                    data={
                        CONF_ENTITY_TYPE: "select",
                        **user_input,
                        "options": options,
                        "unique_id": unique_id,
                    },
                    unique_id=unique_id,
                )

        return self.async_show_form(
            step_id="configure_select",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADS_VAR): cv.string,
                    vol.Required(CONF_NAME): cv.string,
                    vol.Required("options"): cv.string,
                }
            ),
            errors=errors,
        )

    # ── Reconfigure existing entity ─────────────────────────────────

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Reconfigure an entity subentry - route to type-specific step."""
        subentry = self._get_reconfigure_subentry()
        self._entity_data = dict(subentry.data)
        entity_type = self._entity_data.get(CONF_ENTITY_TYPE)

        if entity_type == "switch":
            return await self.async_step_reconfigure_switch()
        if entity_type == "sensor":
            return await self.async_step_reconfigure_sensor()
        if entity_type == "binary_sensor":
            return await self.async_step_reconfigure_binary_sensor()
        if entity_type == "light":
            return await self.async_step_reconfigure_light()
        if entity_type == "cover":
            return await self.async_step_reconfigure_cover()
        if entity_type == "valve":
            return await self.async_step_reconfigure_valve()
        if entity_type == "select":
            return await self.async_step_reconfigure_select()

        return self.async_abort(reason="entity_type_not_supported")

    async def async_step_reconfigure_switch(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Reconfigure a switch entity."""
        if user_input is not None:
            new_data = dict(self._entity_data)
            new_data.update(user_input)
            return self.async_update_and_abort(
                self._get_reconfigure_subentry(),
                data=new_data,
                title=f"{user_input[CONF_NAME]} (Switch)",
            )

        entity = self._entity_data
        return self.async_show_form(
            step_id="reconfigure_switch",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADS_VAR, default=entity.get(CONF_ADS_VAR, "")): cv.string,
                    vol.Required(CONF_NAME, default=entity.get(CONF_NAME, "")): cv.string,
                }
            ),
        )

    async def async_step_reconfigure_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Reconfigure a sensor entity."""
        if user_input is not None:
            new_data = dict(self._entity_data)
            new_data.update(user_input)
            return self.async_update_and_abort(
                self._get_reconfigure_subentry(),
                data=new_data,
                title=f"{user_input[CONF_NAME]} (Sensor)",
            )

        entity = self._entity_data
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
        unit = entity.get(CONF_UNIT_OF_MEASUREMENT)
        if unit:
            schema_dict[vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=unit)] = cv.string
        else:
            schema_dict[vol.Optional(CONF_UNIT_OF_MEASUREMENT)] = cv.string

        device_class = entity.get(CONF_DEVICE_CLASS)
        if device_class:
            schema_dict[vol.Optional(CONF_DEVICE_CLASS, default=device_class)] = selector.SelectSelector(
                selector.SelectSelectorConfig(options=SENSOR_DEVICE_CLASSES, mode=selector.SelectSelectorMode.DROPDOWN)
            )
        else:
            schema_dict[vol.Optional(CONF_DEVICE_CLASS)] = selector.SelectSelector(
                selector.SelectSelectorConfig(options=SENSOR_DEVICE_CLASSES, mode=selector.SelectSelectorMode.DROPDOWN)
            )

        state_class = entity.get(CONF_STATE_CLASS)
        if state_class:
            schema_dict[vol.Optional(CONF_STATE_CLASS, default=state_class)] = selector.SelectSelector(
                selector.SelectSelectorConfig(options=["measurement", "total", "total_increasing"], mode=selector.SelectSelectorMode.DROPDOWN)
            )
        else:
            schema_dict[vol.Optional(CONF_STATE_CLASS)] = selector.SelectSelector(
                selector.SelectSelectorConfig(options=["measurement", "total", "total_increasing"], mode=selector.SelectSelectorMode.DROPDOWN)
            )

        return self.async_show_form(
            step_id="reconfigure_sensor",
            data_schema=vol.Schema(schema_dict),
        )

    async def async_step_reconfigure_binary_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Reconfigure a binary sensor entity."""
        if user_input is not None:
            new_data = dict(self._entity_data)
            new_data.update(user_input)
            return self.async_update_and_abort(
                self._get_reconfigure_subentry(),
                data=new_data,
                title=f"{user_input[CONF_NAME]} (Binary Sensor)",
            )

        entity = self._entity_data
        schema_dict: dict[Any, Any] = {
            vol.Required(CONF_ADS_VAR, default=entity.get(CONF_ADS_VAR, "")): cv.string,
            vol.Required(CONF_NAME, default=entity.get(CONF_NAME, "")): cv.string,
            vol.Optional(CONF_ADS_TYPE, default=entity.get(CONF_ADS_TYPE, "bool")): selector.SelectSelector(
                selector.SelectSelectorConfig(options=["bool", "real"], mode=selector.SelectSelectorMode.DROPDOWN)
            ),
        }
        device_class = entity.get(CONF_DEVICE_CLASS)
        if device_class:
            schema_dict[vol.Optional(CONF_DEVICE_CLASS, default=device_class)] = selector.SelectSelector(
                selector.SelectSelectorConfig(options=BINARY_SENSOR_DEVICE_CLASSES, mode=selector.SelectSelectorMode.DROPDOWN)
            )
        else:
            schema_dict[vol.Optional(CONF_DEVICE_CLASS)] = selector.SelectSelector(
                selector.SelectSelectorConfig(options=BINARY_SENSOR_DEVICE_CLASSES, mode=selector.SelectSelectorMode.DROPDOWN)
            )

        return self.async_show_form(
            step_id="reconfigure_binary_sensor",
            data_schema=vol.Schema(schema_dict),
        )

    async def async_step_reconfigure_light(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Reconfigure a light entity."""
        if user_input is not None:
            new_data = dict(self._entity_data)
            new_data.update(user_input)
            return self.async_update_and_abort(
                self._get_reconfigure_subentry(),
                data=new_data,
                title=f"{user_input[CONF_NAME]} (Light)",
            )

        entity = self._entity_data
        light_schema: dict[Any, Any] = {
            vol.Required(CONF_ADS_VAR, default=entity.get(CONF_ADS_VAR, "")): cv.string,
            vol.Required(CONF_NAME, default=entity.get(CONF_NAME, "")): cv.string,
            vol.Optional("adsvar_brightness_type", default=entity.get("adsvar_brightness_type", "byte")): selector.SelectSelector(
                selector.SelectSelectorConfig(options=["byte", "uint"], mode=selector.SelectSelectorMode.DROPDOWN)
            ),
            vol.Optional("adsvar_brightness_scale", default=entity.get("adsvar_brightness_scale", 255)): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=65535)
            ),
        }
        existing_brightness_var = entity.get("adsvar_brightness")
        if existing_brightness_var:
            light_schema[vol.Optional("adsvar_brightness", default=existing_brightness_var)] = cv.string
        else:
            light_schema[vol.Optional("adsvar_brightness")] = cv.string

        return self.async_show_form(
            step_id="reconfigure_light",
            data_schema=vol.Schema(light_schema),
        )

    async def async_step_reconfigure_cover(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Reconfigure a cover entity."""
        errors: dict[str, str] = {}

        if user_input is not None:
            for var in COVER_ADS_VAR_FIELDS:
                if var in user_input and isinstance(user_input[var], str) and not user_input[var].strip():
                    user_input.pop(var)

            if not user_input.get(CONF_ADS_VAR) and not user_input.get("adsvar_position"):
                errors["base"] = "no_state_var"

            if not errors:
                new_data = dict(self._entity_data)
                new_data.update(user_input)
                return self.async_update_and_abort(
                    self._get_reconfigure_subentry(),
                    data=new_data,
                    title=f"{user_input[CONF_NAME]} (Cover)",
                )

        entity = self._entity_data
        schema_dict: dict[Any, Any] = {
            vol.Required(CONF_NAME, default=entity.get(CONF_NAME, "")): cv.string,
            vol.Optional("adsvar_position_type", default=entity.get("adsvar_position_type", "byte")): selector.SelectSelector(
                selector.SelectSelectorConfig(options=["byte", "uint"], mode=selector.SelectSelectorMode.DROPDOWN)
            ),
            vol.Optional("inverted", default=entity.get("inverted", False)): cv.boolean,
        }
        for field in COVER_ADS_VAR_FIELDS:
            value = entity.get(field)
            if value:
                schema_dict[vol.Optional(field, default=value)] = cv.string
            else:
                schema_dict[vol.Optional(field)] = cv.string

        device_class = entity.get(CONF_DEVICE_CLASS)
        if device_class:
            schema_dict[vol.Optional(CONF_DEVICE_CLASS, default=device_class)] = selector.SelectSelector(
                selector.SelectSelectorConfig(options=COVER_DEVICE_CLASSES, mode=selector.SelectSelectorMode.DROPDOWN)
            )
        else:
            schema_dict[vol.Optional(CONF_DEVICE_CLASS)] = selector.SelectSelector(
                selector.SelectSelectorConfig(options=COVER_DEVICE_CLASSES, mode=selector.SelectSelectorMode.DROPDOWN)
            )

        return self.async_show_form(
            step_id="reconfigure_cover",
            data_schema=vol.Schema(schema_dict),
            errors=errors,
        )

    async def async_step_reconfigure_valve(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Reconfigure a valve entity."""
        if user_input is not None:
            new_data = dict(self._entity_data)
            new_data.update(user_input)
            return self.async_update_and_abort(
                self._get_reconfigure_subentry(),
                data=new_data,
                title=f"{user_input[CONF_NAME]} (Valve)",
            )

        entity = self._entity_data
        schema_dict: dict[Any, Any] = {
            vol.Required(CONF_ADS_VAR, default=entity.get(CONF_ADS_VAR, "")): cv.string,
            vol.Required(CONF_NAME, default=entity.get(CONF_NAME, "")): cv.string,
        }
        device_class = entity.get(CONF_DEVICE_CLASS)
        if device_class:
            schema_dict[vol.Optional(CONF_DEVICE_CLASS, default=device_class)] = selector.SelectSelector(
                selector.SelectSelectorConfig(options=VALVE_DEVICE_CLASSES, mode=selector.SelectSelectorMode.DROPDOWN)
            )
        else:
            schema_dict[vol.Optional(CONF_DEVICE_CLASS)] = selector.SelectSelector(
                selector.SelectSelectorConfig(options=VALVE_DEVICE_CLASSES, mode=selector.SelectSelectorMode.DROPDOWN)
            )

        return self.async_show_form(
            step_id="reconfigure_valve",
            data_schema=vol.Schema(schema_dict),
        )

    async def async_step_reconfigure_select(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Reconfigure a select entity."""
        errors: dict[str, str] = {}

        if user_input is not None:
            options = user_input.get("options", [])
            if isinstance(options, str):
                options = [opt.strip() for opt in options.split(",") if opt.strip()]

            if not options:
                errors["options"] = "no_options"

            if not errors:
                new_data = dict(self._entity_data)
                new_data.update(user_input)
                new_data["options"] = options
                return self.async_update_and_abort(
                    self._get_reconfigure_subentry(),
                    data=new_data,
                    title=f"{user_input[CONF_NAME]} (Select)",
                )

        entity = self._entity_data
        options = entity.get("options", [])
        if isinstance(options, list):
            options_str = ", ".join(options)
        else:
            options_str = str(options) if options else ""

        return self.async_show_form(
            step_id="reconfigure_select",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADS_VAR, default=entity.get(CONF_ADS_VAR, "")): cv.string,
                    vol.Required(CONF_NAME, default=entity.get(CONF_NAME, "")): cv.string,
                    vol.Required("options", default=options_str): cv.string,
                }
            ),
            errors=errors,
        )
