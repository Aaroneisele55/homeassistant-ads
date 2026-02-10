"""Config flow for ADS Custom integration."""

from __future__ import annotations

import logging
import uuid
from types import MappingProxyType
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
from homeassistant.helpers import device_registry as dr, selector
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
# Using selector option format with labels for better accessibility
# All options must be in dict format for proper SelectSelector validation
BINARY_SENSOR_DEVICE_CLASSES = [
    {"label": "(None)", "value": ""},  # Empty option to allow clearing device_class
    {"label": "Battery", "value": "battery"},
    {"label": "Battery Charging", "value": "battery_charging"},
    {"label": "Carbon Monoxide", "value": "carbon_monoxide"},
    {"label": "Cold", "value": "cold"},
    {"label": "Connectivity", "value": "connectivity"},
    {"label": "Door", "value": "door"},
    {"label": "Garage Door", "value": "garage_door"},
    {"label": "Gas", "value": "gas"},
    {"label": "Heat", "value": "heat"},
    {"label": "Light", "value": "light"},
    {"label": "Lock", "value": "lock"},
    {"label": "Moisture", "value": "moisture"},
    {"label": "Motion", "value": "motion"},
    {"label": "Moving", "value": "moving"},
    {"label": "Occupancy", "value": "occupancy"},
    {"label": "Opening", "value": "opening"},
    {"label": "Plug", "value": "plug"},
    {"label": "Power", "value": "power"},
    {"label": "Presence", "value": "presence"},
    {"label": "Problem", "value": "problem"},
    {"label": "Running", "value": "running"},
    {"label": "Safety", "value": "safety"},
    {"label": "Smoke", "value": "smoke"},
    {"label": "Sound", "value": "sound"},
    {"label": "Tamper", "value": "tamper"},
    {"label": "Update", "value": "update"},
    {"label": "Vibration", "value": "vibration"},
    {"label": "Window", "value": "window"},
]

SENSOR_DEVICE_CLASSES = [
    {"label": "(None)", "value": ""},  # Empty option to allow clearing device_class
    {"label": "Apparent Power", "value": "apparent_power"},
    {"label": "AQI", "value": "aqi"},
    {"label": "Atmospheric Pressure", "value": "atmospheric_pressure"},
    {"label": "Battery", "value": "battery"},
    {"label": "Carbon Dioxide", "value": "carbon_dioxide"},
    {"label": "Carbon Monoxide", "value": "carbon_monoxide"},
    {"label": "Current", "value": "current"},
    {"label": "Data Rate", "value": "data_rate"},
    {"label": "Data Size", "value": "data_size"},
    {"label": "Date", "value": "date"},
    {"label": "Distance", "value": "distance"},
    {"label": "Duration", "value": "duration"},
    {"label": "Energy", "value": "energy"},
    {"label": "Energy Storage", "value": "energy_storage"},
    {"label": "Enum", "value": "enum"},
    {"label": "Frequency", "value": "frequency"},
    {"label": "Gas", "value": "gas"},
    {"label": "Humidity", "value": "humidity"},
    {"label": "Illuminance", "value": "illuminance"},
    {"label": "Irradiance", "value": "irradiance"},
    {"label": "Moisture", "value": "moisture"},
    {"label": "Monetary", "value": "monetary"},
    {"label": "Nitrogen Dioxide", "value": "nitrogen_dioxide"},
    {"label": "Nitrogen Monoxide", "value": "nitrogen_monoxide"},
    {"label": "Nitrous Oxide", "value": "nitrous_oxide"},
    {"label": "Ozone", "value": "ozone"},
    {"label": "pH", "value": "ph"},
    {"label": "PM1", "value": "pm1"},
    {"label": "PM10", "value": "pm10"},
    {"label": "PM2.5", "value": "pm25"},
    {"label": "Power", "value": "power"},
    {"label": "Power Factor", "value": "power_factor"},
    {"label": "Precipitation", "value": "precipitation"},
    {"label": "Precipitation Intensity", "value": "precipitation_intensity"},
    {"label": "Pressure", "value": "pressure"},
    {"label": "Reactive Power", "value": "reactive_power"},
    {"label": "Signal Strength", "value": "signal_strength"},
    {"label": "Sound Pressure", "value": "sound_pressure"},
    {"label": "Speed", "value": "speed"},
    {"label": "Sulphur Dioxide", "value": "sulphur_dioxide"},
    {"label": "Temperature", "value": "temperature"},
    {"label": "Timestamp", "value": "timestamp"},
    {"label": "Volatile Organic Compounds", "value": "volatile_organic_compounds"},
    {"label": "Volatile Organic Compounds Parts", "value": "volatile_organic_compounds_parts"},
    {"label": "Voltage", "value": "voltage"},
    {"label": "Volume", "value": "volume"},
    {"label": "Volume Flow Rate", "value": "volume_flow_rate"},
    {"label": "Volume Storage", "value": "volume_storage"},
    {"label": "Water", "value": "water"},
    {"label": "Weight", "value": "weight"},
    {"label": "Wind Speed", "value": "wind_speed"},
]

COVER_DEVICE_CLASSES = [
    {"label": "(None)", "value": ""},  # Empty option to allow clearing device_class
    {"label": "Awning", "value": "awning"},
    {"label": "Blind", "value": "blind"},
    {"label": "Curtain", "value": "curtain"},
    {"label": "Damper", "value": "damper"},
    {"label": "Door", "value": "door"},
    {"label": "Garage", "value": "garage"},
    {"label": "Gate", "value": "gate"},
    {"label": "Shade", "value": "shade"},
    {"label": "Shutter", "value": "shutter"},
    {"label": "Window", "value": "window"},
]

VALVE_DEVICE_CLASSES = [
    {"label": "(None)", "value": ""},  # Empty option to allow clearing device_class
    {"label": "Gas", "value": "gas"},
    {"label": "Water", "value": "water"},
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

    @property
    def entry(self) -> ConfigEntry:
        """Return the config entry linked to this subentry flow.

        Tries to use public API first (handler.config_entry), then falls back
        to protected method for compatibility with older HA versions.
        """
        # Try modern public API first (HA 2024.2+)
        if hasattr(self, "handler") and hasattr(self.handler, "config_entry"):
            return self.handler.config_entry

        # Fall back to protected method for older versions
        return self._get_entry()

    @staticmethod
    def _remove_empty_optional_fields(data: dict[str, Any], *field_names: str) -> None:
        """Remove optional fields with empty values from data dictionary.

        This helper is intended for optional metadata fields like ``device_class``
        or ``state_class`` where an empty UI selection should clear the value.
        It considers a field "empty" if its value is:

        - ``None``
        - an empty or whitespace-only string
        - an empty collection (list, dict, set, tuple)

        Valid falsy values such as ``0`` or ``False`` are preserved so that this
        helper can be safely reused for optional fields that legitimately accept
        those values.

        Args:
            data: Dictionary to modify in-place.
            *field_names: Names of fields to check and remove if empty.
        """
        for field_name in field_names:
            if field_name not in data:
                continue

            value = data[field_name]

            # Remove explicit None
            if value is None:
                data.pop(field_name)
                continue

            # Remove empty or whitespace-only strings
            if isinstance(value, str) and not value.strip():
                data.pop(field_name)
                continue

            # Remove empty collections (but keep 0/False etc.)
            if isinstance(value, (list, dict, set, tuple)) and not value:
                data.pop(field_name)

    def _update_device_name_if_changed(
        self, subentry_unique_id: str, old_name: str | None, new_name: str
    ) -> None:
        """Update device registry name when subentry name changes."""
        # Skip if old_name is None or names are the same
        if not old_name or old_name == new_name:
            return

        # Get the device registry
        device_registry = dr.async_get(self.hass)

        # Find the device by identifier
        device = device_registry.async_get_device(
            identifiers={(DOMAIN, subentry_unique_id)}
        )

        if not device:
            _LOGGER.debug(
                "No device found for subentry '%s', skipping device name update",
                subentry_unique_id,
            )
            return

        # Only update if the current device name matches the old subentry name
        # This prevents overwriting user-customized device names
        current_device_name = device.name_by_user or device.name
        if current_device_name != old_name:
            _LOGGER.debug(
                "Device name '%s' differs from old subentry name '%s', skipping update",
                current_device_name,
                old_name,
            )
            return

        _LOGGER.info(
            "Subentry '%s' renamed to '%s', updating device",
            old_name,
            new_name,
        )

        # Update the appropriate name field
        # If name_by_user is set and matches old_name, update it
        # Otherwise update the base name field
        if device.name_by_user and device.name_by_user == old_name:
            device_registry.async_update_device(
                device.id,
                name_by_user=new_name,
            )
        else:
            device_registry.async_update_device(
                device.id,
                name=new_name,
            )

    # ── Add new entity ──────────────────────────────────────────────

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Select entity type to add."""
        return self.async_show_menu(
            step_id="user",
            menu_options=[
                "add_switch",
                "add_sensor",
                "add_binary_sensor",
                "add_light",
                "add_cover",
                "add_valve",
                "add_select",
            ],
        )

    # ── Menu handlers for entity type selection ──────────────────────

    async def async_step_add_switch(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Route to switch configuration."""
        return await self.async_step_configure_switch()

    async def async_step_add_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Route to sensor configuration."""
        return await self.async_step_configure_sensor()

    async def async_step_add_binary_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Route to binary sensor configuration."""
        return await self.async_step_configure_binary_sensor()

    async def async_step_add_light(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Route to light configuration."""
        return await self.async_step_configure_light()

    async def async_step_add_cover(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Route to cover configuration."""
        return await self.async_step_configure_cover()

    async def async_step_add_valve(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Route to valve configuration."""
        return await self.async_step_configure_valve()

    async def async_step_add_select(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Route to select configuration."""
        return await self.async_step_configure_select()

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
            # Remove empty optional fields to allow clearing
            self._remove_empty_optional_fields(
                user_input, CONF_DEVICE_CLASS, CONF_STATE_CLASS
            )

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
            # Remove empty optional fields to allow clearing
            self._remove_empty_optional_fields(user_input, CONF_DEVICE_CLASS)

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

            # Remove empty optional fields to allow clearing
            self._remove_empty_optional_fields(user_input, CONF_DEVICE_CLASS)

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
            # Remove empty optional fields to allow clearing
            self._remove_empty_optional_fields(user_input, CONF_DEVICE_CLASS)

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
            subentry = self._get_reconfigure_subentry()
            new_title = f"{user_input[CONF_NAME]} (Switch)"

            # Update device name if changed
            old_name = self._entity_data.get(CONF_NAME)
            new_name = user_input[CONF_NAME]
            if subentry.unique_id:
                self._update_device_name_if_changed(subentry.unique_id, old_name, new_name)

            self.hass.config_entries.async_update_subentry(
                self.entry, subentry, data=MappingProxyType(new_data), title=new_title
            )
            return self.async_abort(reason="reconfigure_successful")

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

            # Remove empty optional fields to allow clearing
            self._remove_empty_optional_fields(
                new_data, CONF_DEVICE_CLASS, CONF_STATE_CLASS
            )

            subentry = self._get_reconfigure_subentry()
            new_title = f"{user_input[CONF_NAME]} (Sensor)"

            # Update device name if changed
            old_name = self._entity_data.get(CONF_NAME)
            new_name = user_input[CONF_NAME]
            if subentry.unique_id:
                self._update_device_name_if_changed(subentry.unique_id, old_name, new_name)

            self.hass.config_entries.async_update_subentry(
                self.entry, subentry, data=MappingProxyType(new_data), title=new_title
            )
            return self.async_abort(reason="reconfigure_successful")

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

            # Remove empty optional fields to allow clearing
            self._remove_empty_optional_fields(new_data, CONF_DEVICE_CLASS)

            subentry = self._get_reconfigure_subentry()
            new_title = f"{user_input[CONF_NAME]} (Binary Sensor)"

            # Update device name if changed
            old_name = self._entity_data.get(CONF_NAME)
            new_name = user_input[CONF_NAME]
            if subentry.unique_id:
                self._update_device_name_if_changed(subentry.unique_id, old_name, new_name)

            self.hass.config_entries.async_update_subentry(
                self.entry, subentry, data=MappingProxyType(new_data), title=new_title
            )
            return self.async_abort(reason="reconfigure_successful")

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
            subentry = self._get_reconfigure_subentry()
            new_title = f"{user_input[CONF_NAME]} (Light)"

            # Update device name if changed
            old_name = self._entity_data.get(CONF_NAME)
            new_name = user_input[CONF_NAME]
            if subentry.unique_id:
                self._update_device_name_if_changed(subentry.unique_id, old_name, new_name)

            self.hass.config_entries.async_update_subentry(
                self.entry, subentry, data=MappingProxyType(new_data), title=new_title
            )
            return self.async_abort(reason="reconfigure_successful")

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

                # Remove empty optional fields to allow clearing
                self._remove_empty_optional_fields(new_data, CONF_DEVICE_CLASS)

                subentry = self._get_reconfigure_subentry()
                new_title = f"{user_input[CONF_NAME]} (Cover)"

                # Update device name if changed
                old_name = self._entity_data.get(CONF_NAME)
                new_name = user_input[CONF_NAME]
                if subentry.unique_id:
                    self._update_device_name_if_changed(subentry.unique_id, old_name, new_name)

                self.hass.config_entries.async_update_subentry(
                    self.entry, subentry, data=MappingProxyType(new_data), title=new_title
                )
                return self.async_abort(reason="reconfigure_successful")

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

            # Remove empty optional fields to allow clearing
            self._remove_empty_optional_fields(new_data, CONF_DEVICE_CLASS)

            subentry = self._get_reconfigure_subentry()
            new_title = f"{user_input[CONF_NAME]} (Valve)"

            # Update device name if changed
            old_name = self._entity_data.get(CONF_NAME)
            new_name = user_input[CONF_NAME]
            if subentry.unique_id:
                self._update_device_name_if_changed(subentry.unique_id, old_name, new_name)

            self.hass.config_entries.async_update_subentry(
                self.entry, subentry, data=MappingProxyType(new_data), title=new_title
            )
            return self.async_abort(reason="reconfigure_successful")

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
                subentry = self._get_reconfigure_subentry()
                new_title = f"{user_input[CONF_NAME]} (Select)"

                # Update device name if changed
                old_name = self._entity_data.get(CONF_NAME)
                new_name = user_input[CONF_NAME]
                if subentry.unique_id:
                    self._update_device_name_if_changed(subentry.unique_id, old_name, new_name)

                self.hass.config_entries.async_update_subentry(
                    self.entry, subentry, data=MappingProxyType(new_data), title=new_title
                )
                return self.async_abort(reason="reconfigure_successful")

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
