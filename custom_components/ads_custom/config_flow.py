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
    OptionsFlow,
    SubentryFlowResult,
)
from homeassistant.const import CONF_DEVICE, CONF_IP_ADDRESS, CONF_NAME, CONF_PORT, CONF_UNIQUE_ID
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, selector
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_ADS_VAR,
    CONF_ENTITY_DEVICE_ID,
    CONF_ENTITY_DEVICE_NAME,
    CONF_ENTITY_CATEGORY,
    CONF_ENTITY_ICON,
    CONF_ENTITY_PICTURE,
    DOMAIN,
    AdsType,
    SUBENTRY_TYPE_ENTITY,
)

_LOGGER = logging.getLogger(__name__)
DEVICE_OPTION_CREATE_NEW = "__create_new__"
DEFAULT_NEW_DEVICE_NAME = "ADS Device"
DEFAULT_MIGRATED_DEVICE_NAME = "Default ADS Device"
OPTION_DELETE_DEVICE = "__delete_device__"
CONF_SELECTED_DEVICE_ID = "selected_device_id"
CONF_SELECTED_ENTITY_SUBENTRY_ID = "selected_entity_subentry_id"
CONF_CONFIRM_DELETE = "confirm_delete"
CONF_DEVICE_ACTION = "device_action"

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
# Options are simple strings; labels come from translation files
# Translation keys: selector.select.options.<value>
BINARY_SENSOR_DEVICE_CLASSES = [
    {"label": "(None)", "value": ""},
    {"label": "battery", "value": "battery"},
    {"label": "battery_charging", "value": "battery_charging"},
    {"label": "carbon_monoxide", "value": "carbon_monoxide"},
    {"label": "cold", "value": "cold"},
    {"label": "connectivity", "value": "connectivity"},
    {"label": "door", "value": "door"},
    {"label": "garage_door", "value": "garage_door"},
    {"label": "gas", "value": "gas"},
    {"label": "heat", "value": "heat"},
    {"label": "light", "value": "light"},
    {"label": "lock", "value": "lock"},
    {"label": "moisture", "value": "moisture"},
    {"label": "motion", "value": "motion"},
    {"label": "moving", "value": "moving"},
    {"label": "occupancy", "value": "occupancy"},
    {"label": "opening", "value": "opening"},
    {"label": "plug", "value": "plug"},
    {"label": "power", "value": "power"},
    {"label": "presence", "value": "presence"},
    {"label": "problem", "value": "problem"},
    {"label": "running", "value": "running"},
    {"label": "safety", "value": "safety"},
    {"label": "smoke", "value": "smoke"},
    {"label": "sound", "value": "sound"},
    {"label": "tamper", "value": "tamper"},
    {"label": "update", "value": "update"},
    {"label": "vibration", "value": "vibration"},
    {"label": "window", "value": "window"},
]

SENSOR_DEVICE_CLASSES = [
    {"label": "(None)", "value": ""},
    {"label": "apparent_power", "value": "apparent_power"},
    {"label": "aqi", "value": "aqi"},
    {"label": "atmospheric_pressure", "value": "atmospheric_pressure"},
    {"label": "battery", "value": "battery"},
    {"label": "carbon_dioxide", "value": "carbon_dioxide"},
    {"label": "carbon_monoxide", "value": "carbon_monoxide"},
    {"label": "current", "value": "current"},
    {"label": "data_rate", "value": "data_rate"},
    {"label": "data_size", "value": "data_size"},
    {"label": "date", "value": "date"},
    {"label": "distance", "value": "distance"},
    {"label": "duration", "value": "duration"},
    {"label": "energy", "value": "energy"},
    {"label": "energy_storage", "value": "energy_storage"},
    {"label": "enum", "value": "enum"},
    {"label": "frequency", "value": "frequency"},
    {"label": "gas", "value": "gas"},
    {"label": "humidity", "value": "humidity"},
    {"label": "illuminance", "value": "illuminance"},
    {"label": "irradiance", "value": "irradiance"},
    {"label": "moisture", "value": "moisture"},
    {"label": "monetary", "value": "monetary"},
    {"label": "nitrogen_dioxide", "value": "nitrogen_dioxide"},
    {"label": "nitrogen_monoxide", "value": "nitrogen_monoxide"},
    {"label": "nitrous_oxide", "value": "nitrous_oxide"},
    {"label": "ozone", "value": "ozone"},
    {"label": "ph", "value": "ph"},
    {"label": "pm1", "value": "pm1"},
    {"label": "pm10", "value": "pm10"},
    {"label": "pm25", "value": "pm25"},
    {"label": "power", "value": "power"},
    {"label": "power_factor", "value": "power_factor"},
    {"label": "precipitation", "value": "precipitation"},
    {"label": "precipitation_intensity", "value": "precipitation_intensity"},
    {"label": "pressure", "value": "pressure"},
    {"label": "reactive_power", "value": "reactive_power"},
    {"label": "signal_strength", "value": "signal_strength"},
    {"label": "sound_pressure", "value": "sound_pressure"},
    {"label": "speed", "value": "speed"},
    {"label": "sulphur_dioxide", "value": "sulphur_dioxide"},
    {"label": "temperature", "value": "temperature"},
    {"label": "timestamp", "value": "timestamp"},
    {"label": "volatile_organic_compounds", "value": "volatile_organic_compounds"},
    {"label": "volatile_organic_compounds_parts", "value": "volatile_organic_compounds_parts"},
    {"label": "voltage", "value": "voltage"},
    {"label": "volume", "value": "volume"},
    {"label": "volume_flow_rate", "value": "volume_flow_rate"},
    {"label": "volume_storage", "value": "volume_storage"},
    {"label": "water", "value": "water"},
    {"label": "weight", "value": "weight"},
    {"label": "wind_speed", "value": "wind_speed"},
]

COVER_DEVICE_CLASSES = [
    {"label": "(None)", "value": ""},
    {"label": "awning", "value": "awning"},
    {"label": "blind", "value": "blind"},
    {"label": "curtain", "value": "curtain"},
    {"label": "damper", "value": "damper"},
    {"label": "door", "value": "door"},
    {"label": "garage", "value": "garage"},
    {"label": "gate", "value": "gate"},
    {"label": "shade", "value": "shade"},
    {"label": "shutter", "value": "shutter"},
    {"label": "window", "value": "window"},
]

VALVE_DEVICE_CLASSES = [
    {"label": "(None)", "value": ""},
    {"label": "gas", "value": "gas"},
    {"label": "water", "value": "water"},
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

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow for this config entry."""
        return AdsOptionsFlowHandler(config_entry)

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

    @staticmethod
    def _remove_cleared_optional_fields(
        merged_data: dict[str, Any],
        user_input: dict[str, Any],
        *field_names: str,
    ) -> None:
        """Remove optional fields that were cleared during reconfiguration.

        When reconfiguring, old entity data is merged with user input via
        ``dict.update()``.  If the user selects a blank / "(None)" option
        for an ``Optional`` select field, voluptuous may strip the empty
        value so the key is absent from *user_input*.  The old value then
        survives the merge.  This helper detects that situation and removes
        such stale keys from *merged_data*.

        Args:
            merged_data: Dictionary resulting from old data merged with user input.
            user_input: The raw user input from the form submission.
            *field_names: Names of optional fields that support clearing.
        """
        for field_name in field_names:
            if field_name in merged_data and field_name not in user_input:
                del merged_data[field_name]

    @staticmethod
    def _resolve_device_assignment(
        user_input: dict[str, Any],
        *,
        current_data: dict[str, Any] | None = None,
    ) -> bool:
        """Resolve and validate device assignment fields in-place.

        This method mutates ``user_input`` and returns ``True`` when assignment
        resolution succeeds, otherwise ``False`` when user input is invalid.
        It always sets/updates ``CONF_ENTITY_DEVICE_ID`` and may set or remove
        ``CONF_ENTITY_DEVICE_NAME`` based on the selected mode.

        Handled scenarios:
        - Existing device selected: keep selected device ID and clear new-device name.
        - New device selected: require ``entity_device_name`` and generate a new
          ``entity_device_id``.
        - No selection provided: preserve existing assignment from ``current_data``
          (including legacy ``unique_id`` fallback) or create a dedicated fallback
          assignment for compatibility.
        """
        selected_device_id = user_input.get(CONF_ENTITY_DEVICE_ID)
        if selected_device_id is None:
            # Keep existing assignment on reconfigure if field omitted
            if current_data is not None:
                existing_id = current_data.get(CONF_ENTITY_DEVICE_ID) or current_data.get(CONF_UNIQUE_ID)
                if existing_id:
                    user_input[CONF_ENTITY_DEVICE_ID] = existing_id
                    user_input.pop(CONF_ENTITY_DEVICE_NAME, None)
                    return True

            # New entities must explicitly select existing or create-new device
            return False

        if selected_device_id == DEVICE_OPTION_CREATE_NEW:
            new_device_name = (user_input.get(CONF_ENTITY_DEVICE_NAME) or "").strip()
            if not new_device_name:
                return False
            user_input[CONF_ENTITY_DEVICE_ID] = uuid.uuid4().hex
            user_input[CONF_ENTITY_DEVICE_NAME] = new_device_name
            return True

        # Existing device selected
        user_input[CONF_ENTITY_DEVICE_ID] = selected_device_id
        user_input.pop(CONF_ENTITY_DEVICE_NAME, None)
        return True

    def _get_device_assignment_options(self) -> list[dict[str, str]]:
        """Return sorted device options as label/value dictionaries.

        Options include all ADS devices linked to the current config entry,
        sorted alphabetically by label, plus a trailing ``Create new device``
        option used by config-flow forms.
        """
        device_registry = dr.async_get(self.hass)
        options: list[dict[str, str]] = []
        seen_identifiers: set[str] = set()

        for device in device_registry.devices.values():
            if self.entry.entry_id not in device.config_entries:
                continue

            for domain, identifier in device.identifiers:
                if domain != DOMAIN or identifier in seen_identifiers:
                    continue
                seen_identifiers.add(identifier)
                label = device.name_by_user or device.name or identifier
                options.append({"label": label, "value": identifier})
                break

        options.sort(key=lambda item: item["label"].lower())
        options.append({"label": "Create new device", "value": DEVICE_OPTION_CREATE_NEW})
        return options

    def _device_assignment_schema(
        self, current_data: dict[str, Any] | None = None
    ) -> dict[Any, Any]:
        """Build schema fields for assigning an entity to a device.

        Returns voluptuous schema entries for:
        - ``entity_device_id``: existing-device selector plus create-new option.
        - ``entity_device_name``: optional name used when creating a device.

        For legacy entities without explicit ``entity_device_id``, this method
        falls back to ``unique_id`` so reconfigure forms default to the correct
        previously-created device.
        """
        options = self._get_device_assignment_options()
        current_device_id = (
            current_data.get(CONF_ENTITY_DEVICE_ID) if current_data else None
        )
        if current_data and not current_device_id:
            # Legacy entities created before explicit device assignment used
            # the entity/subentry unique_id as the device identifier.
            current_device_id = current_data.get(CONF_UNIQUE_ID)

        if current_device_id and all(
            option["value"] != current_device_id for option in options
        ):
            fallback_label = current_data.get(
                CONF_ENTITY_DEVICE_NAME,
                current_data.get(CONF_NAME, current_device_id),
            )
            options.insert(
                0,
                {
                    "label": fallback_label,
                    "value": current_device_id,
                },
            )

        default_device_id = (
            current_device_id
            if current_device_id
            else (options[0]["value"] if options else DEVICE_OPTION_CREATE_NEW)
        )

        schema: dict[Any, Any] = {
            vol.Optional(CONF_ENTITY_DEVICE_ID, default=default_device_id): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        }

        if current_data and current_data.get(CONF_ENTITY_DEVICE_NAME):
            schema[vol.Optional(CONF_ENTITY_DEVICE_NAME, default=current_data[CONF_ENTITY_DEVICE_NAME])] = cv.string
        else:
            schema[vol.Optional(CONF_ENTITY_DEVICE_NAME)] = cv.string

        return schema

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
        errors: dict[str, str] = {}
        if user_input is not None:
            if not self._resolve_device_assignment(user_input):
                errors[CONF_ENTITY_DEVICE_NAME] = "device_name_required"
            else:
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
                    **self._device_assignment_schema(),
                }
            ),
            errors=errors,
        )

    async def async_step_configure_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Configure a sensor entity."""
        errors: dict[str, str] = {}
        if user_input is not None:
            # Remove empty optional fields to allow clearing
            self._remove_empty_optional_fields(
                user_input, CONF_DEVICE_CLASS, CONF_STATE_CLASS
            )

            if not self._resolve_device_assignment(user_input):
                errors[CONF_ENTITY_DEVICE_NAME] = "device_name_required"
            else:
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
                    **self._device_assignment_schema(),
                }
            ),
            errors=errors,
        )

    async def async_step_configure_binary_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Configure a binary sensor entity."""
        errors: dict[str, str] = {}
        if user_input is not None:
            # Remove empty optional fields to allow clearing
            self._remove_empty_optional_fields(user_input, CONF_DEVICE_CLASS)

            if not self._resolve_device_assignment(user_input):
                errors[CONF_ENTITY_DEVICE_NAME] = "device_name_required"
            else:
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
                    **self._device_assignment_schema(),
                }
            ),
            errors=errors,
        )

    async def async_step_configure_light(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Configure a light entity."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if not self._resolve_device_assignment(user_input):
                errors[CONF_ENTITY_DEVICE_NAME] = "device_name_required"
            else:
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
                    **self._device_assignment_schema(),
                }
            ),
            errors=errors,
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
            elif not self._resolve_device_assignment(user_input):
                errors[CONF_ENTITY_DEVICE_NAME] = "device_name_required"
            else:
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
                    **self._device_assignment_schema(),
                }
            ),
            errors=errors,
        )

    async def async_step_configure_valve(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Configure a valve entity."""
        errors: dict[str, str] = {}
        if user_input is not None:
            # Remove empty optional fields to allow clearing
            self._remove_empty_optional_fields(user_input, CONF_DEVICE_CLASS)

            if not self._resolve_device_assignment(user_input):
                errors[CONF_ENTITY_DEVICE_NAME] = "device_name_required"
            else:
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
                    **self._device_assignment_schema(),
                }
            ),
            errors=errors,
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
            elif not self._resolve_device_assignment(user_input):
                errors[CONF_ENTITY_DEVICE_NAME] = "device_name_required"
            else:
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
                    **self._device_assignment_schema(),
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
        errors: dict[str, str] = {}
        if user_input is not None:
            if not self._resolve_device_assignment(user_input, current_data=self._entity_data):
                errors[CONF_ENTITY_DEVICE_NAME] = "device_name_required"
            else:
                new_data = dict(self._entity_data)
                new_data.update(user_input)
                subentry = self._get_reconfigure_subentry()
                new_title = f"{user_input[CONF_NAME]} (Switch)"

                # Update device name if changed (legacy one-device-per-entity only)
                old_name = self._entity_data.get(CONF_NAME)
                new_name = user_input[CONF_NAME]
                if subentry.unique_id and CONF_ENTITY_DEVICE_ID not in self._entity_data:
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
                    **self._device_assignment_schema(entity),
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Reconfigure a sensor entity."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if not self._resolve_device_assignment(user_input, current_data=self._entity_data):
                errors[CONF_ENTITY_DEVICE_NAME] = "device_name_required"
            else:
                new_data = dict(self._entity_data)
                new_data.update(user_input)

                # Remove empty optional fields to allow clearing
                self._remove_empty_optional_fields(
                    new_data, CONF_DEVICE_CLASS, CONF_STATE_CLASS
                )
                self._remove_cleared_optional_fields(
                    new_data, user_input, CONF_DEVICE_CLASS, CONF_STATE_CLASS
                )

                subentry = self._get_reconfigure_subentry()
                new_title = f"{user_input[CONF_NAME]} (Sensor)"

                # Update device name if changed (legacy one-device-per-entity only)
                old_name = self._entity_data.get(CONF_NAME)
                new_name = user_input[CONF_NAME]
                if subentry.unique_id and CONF_ENTITY_DEVICE_ID not in self._entity_data:
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

        schema_dict[vol.Optional(CONF_DEVICE_CLASS)] = selector.SelectSelector(
            selector.SelectSelectorConfig(options=SENSOR_DEVICE_CLASSES, mode=selector.SelectSelectorMode.DROPDOWN)
        )

        schema_dict[vol.Optional(CONF_STATE_CLASS)] = selector.SelectSelector(
            selector.SelectSelectorConfig(options=["measurement", "total", "total_increasing"], mode=selector.SelectSelectorMode.DROPDOWN)
        )
        schema_dict.update(self._device_assignment_schema(entity))

        return self.async_show_form(
            step_id="reconfigure_sensor",
            data_schema=vol.Schema(schema_dict),
            errors=errors,
        )

    async def async_step_reconfigure_binary_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Reconfigure a binary sensor entity."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if not self._resolve_device_assignment(user_input, current_data=self._entity_data):
                errors[CONF_ENTITY_DEVICE_NAME] = "device_name_required"
            else:
                new_data = dict(self._entity_data)
                new_data.update(user_input)

                # Remove empty optional fields to allow clearing
                self._remove_empty_optional_fields(new_data, CONF_DEVICE_CLASS)
                self._remove_cleared_optional_fields(new_data, user_input, CONF_DEVICE_CLASS)

                subentry = self._get_reconfigure_subentry()
                new_title = f"{user_input[CONF_NAME]} (Binary Sensor)"

                # Update device name if changed (legacy one-device-per-entity only)
                old_name = self._entity_data.get(CONF_NAME)
                new_name = user_input[CONF_NAME]
                if subentry.unique_id and CONF_ENTITY_DEVICE_ID not in self._entity_data:
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
            **self._device_assignment_schema(entity),
        }
        schema_dict[vol.Optional(CONF_DEVICE_CLASS)] = selector.SelectSelector(
            selector.SelectSelectorConfig(options=BINARY_SENSOR_DEVICE_CLASSES, mode=selector.SelectSelectorMode.DROPDOWN)
        )

        data_schema = self.add_suggested_values_to_schema(
            vol.Schema(schema_dict),
            entity,
        )

        return self.async_show_form(
            step_id="reconfigure_binary_sensor",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_reconfigure_light(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Reconfigure a light entity."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if not self._resolve_device_assignment(user_input, current_data=self._entity_data):
                errors[CONF_ENTITY_DEVICE_NAME] = "device_name_required"
            else:
                new_data = dict(self._entity_data)
                new_data.update(user_input)
                subentry = self._get_reconfigure_subentry()
                new_title = f"{user_input[CONF_NAME]} (Light)"

                # Update device name if changed (legacy one-device-per-entity only)
                old_name = self._entity_data.get(CONF_NAME)
                new_name = user_input[CONF_NAME]
                if subentry.unique_id and CONF_ENTITY_DEVICE_ID not in self._entity_data:
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
            **self._device_assignment_schema(entity),
        }
        existing_brightness_var = entity.get("adsvar_brightness")
        if existing_brightness_var:
            light_schema[vol.Optional("adsvar_brightness", default=existing_brightness_var)] = cv.string
        else:
            light_schema[vol.Optional("adsvar_brightness")] = cv.string

        return self.async_show_form(
            step_id="reconfigure_light",
            data_schema=vol.Schema(light_schema),
            errors=errors,
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
            elif not self._resolve_device_assignment(user_input, current_data=self._entity_data):
                errors[CONF_ENTITY_DEVICE_NAME] = "device_name_required"
            else:
                new_data = dict(self._entity_data)
                new_data.update(user_input)

                # Remove empty optional fields to allow clearing
                self._remove_empty_optional_fields(new_data, CONF_DEVICE_CLASS)
                self._remove_cleared_optional_fields(new_data, user_input, CONF_DEVICE_CLASS)

                subentry = self._get_reconfigure_subentry()
                new_title = f"{user_input[CONF_NAME]} (Cover)"

                # Update device name if changed (legacy one-device-per-entity only)
                old_name = self._entity_data.get(CONF_NAME)
                new_name = user_input[CONF_NAME]
                if subentry.unique_id and CONF_ENTITY_DEVICE_ID not in self._entity_data:
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

        schema_dict[vol.Optional(CONF_DEVICE_CLASS)] = selector.SelectSelector(
            selector.SelectSelectorConfig(options=COVER_DEVICE_CLASSES, mode=selector.SelectSelectorMode.DROPDOWN)
        )
        schema_dict.update(self._device_assignment_schema(entity))

        return self.async_show_form(
            step_id="reconfigure_cover",
            data_schema=vol.Schema(schema_dict),
            errors=errors,
        )

    async def async_step_reconfigure_valve(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Reconfigure a valve entity."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if not self._resolve_device_assignment(user_input, current_data=self._entity_data):
                errors[CONF_ENTITY_DEVICE_NAME] = "device_name_required"
            else:
                new_data = dict(self._entity_data)
                new_data.update(user_input)

                # Remove empty optional fields to allow clearing
                self._remove_empty_optional_fields(new_data, CONF_DEVICE_CLASS)
                self._remove_cleared_optional_fields(new_data, user_input, CONF_DEVICE_CLASS)

                subentry = self._get_reconfigure_subentry()
                new_title = f"{user_input[CONF_NAME]} (Valve)"

                # Update device name if changed (legacy one-device-per-entity only)
                old_name = self._entity_data.get(CONF_NAME)
                new_name = user_input[CONF_NAME]
                if subentry.unique_id and CONF_ENTITY_DEVICE_ID not in self._entity_data:
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
        schema_dict[vol.Optional(CONF_DEVICE_CLASS)] = selector.SelectSelector(
            selector.SelectSelectorConfig(options=VALVE_DEVICE_CLASSES, mode=selector.SelectSelectorMode.DROPDOWN)
        )
        schema_dict.update(self._device_assignment_schema(entity))

        return self.async_show_form(
            step_id="reconfigure_valve",
            data_schema=vol.Schema(schema_dict),
            errors=errors,
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
            elif not self._resolve_device_assignment(user_input, current_data=self._entity_data):
                errors[CONF_ENTITY_DEVICE_NAME] = "device_name_required"
            else:
                new_data = dict(self._entity_data)
                new_data.update(user_input)
                new_data["options"] = options
                subentry = self._get_reconfigure_subentry()
                new_title = f"{user_input[CONF_NAME]} (Select)"

                # Update device name if changed (legacy one-device-per-entity only)
                old_name = self._entity_data.get(CONF_NAME)
                new_name = user_input[CONF_NAME]
                if subentry.unique_id and CONF_ENTITY_DEVICE_ID not in self._entity_data:
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
                    **self._device_assignment_schema(entity),
                }
            ),
            errors=errors,
        )

    # ── Entity Options ──────────────────────────────────────────────

    async def async_step_entity_options(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Configure entity options like icon, entity_category, etc."""
        if user_input is not None:
            subentry = self._get_reconfigure_subentry()
            new_data = dict(subentry.data)
            
            # Remove empty optional fields to allow clearing
            self._remove_empty_optional_fields(
                user_input, CONF_ENTITY_ICON, CONF_ENTITY_CATEGORY, CONF_ENTITY_PICTURE
            )
            
            # Update only the entity option fields
            for key in [CONF_ENTITY_ICON, CONF_ENTITY_CATEGORY, CONF_ENTITY_PICTURE]:
                if key in user_input:
                    new_data[key] = user_input[key]
                elif key in new_data:
                    # Remove the key if it's not in user input (was cleared)
                    del new_data[key]
            
            self.hass.config_entries.async_update_subentry(
                self.entry, subentry, data=MappingProxyType(new_data)
            )
            return self.async_abort(reason="entity_options_updated")
        
        # Get current entity data
        subentry = self._get_reconfigure_subentry()
        entity = dict(subentry.data)
        
        # Define entity category options
        entity_category_options = [
            "",  # None/cleared
            "config",
            "diagnostic",
        ]
        
        # Build the schema with current values as defaults
        schema_dict: dict[Any, Any] = {
            vol.Optional(CONF_ENTITY_ICON): selector.IconSelector(
                selector.IconSelectorConfig()
            ),
            vol.Optional(CONF_ENTITY_CATEGORY): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=entity_category_options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(CONF_ENTITY_PICTURE): cv.string,
        }
        
        # Use add_suggested_values_to_schema to populate defaults
        data_schema = self.add_suggested_values_to_schema(
            vol.Schema(schema_dict),
            entity,
        )
        
        return self.async_show_form(
            step_id="entity_options",
            data_schema=data_schema,
        )


class AdsOptionsFlowHandler(OptionsFlow):
    """Handle hub-level device and entity management options."""

    _entity_data: dict[str, Any]

    _remove_empty_optional_fields = staticmethod(
        AdsEntitySubentryFlowHandler._remove_empty_optional_fields
    )
    _remove_cleared_optional_fields = staticmethod(
        AdsEntitySubentryFlowHandler._remove_cleared_optional_fields
    )
    _resolve_device_assignment = staticmethod(
        AdsEntitySubentryFlowHandler._resolve_device_assignment
    )
    _get_device_assignment_options = AdsEntitySubentryFlowHandler._get_device_assignment_options
    _device_assignment_schema = AdsEntitySubentryFlowHandler._device_assignment_schema
    _update_device_name_if_changed = AdsEntitySubentryFlowHandler._update_device_name_if_changed

    async_step_reconfigure = AdsEntitySubentryFlowHandler.async_step_reconfigure
    async_step_reconfigure_switch = AdsEntitySubentryFlowHandler.async_step_reconfigure_switch
    async_step_reconfigure_sensor = AdsEntitySubentryFlowHandler.async_step_reconfigure_sensor
    async_step_reconfigure_binary_sensor = (
        AdsEntitySubentryFlowHandler.async_step_reconfigure_binary_sensor
    )
    async_step_reconfigure_light = AdsEntitySubentryFlowHandler.async_step_reconfigure_light
    async_step_reconfigure_cover = AdsEntitySubentryFlowHandler.async_step_reconfigure_cover
    async_step_reconfigure_valve = AdsEntitySubentryFlowHandler.async_step_reconfigure_valve
    async_step_reconfigure_select = AdsEntitySubentryFlowHandler.async_step_reconfigure_select

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._selected_device_id: str | None = None
        self._selected_subentry_id: str | None = None

    @property
    def entry(self) -> ConfigEntry:
        """Compatibility property expected by reconfigure helpers."""
        return self.config_entry

    def _get_reconfigure_subentry(self):
        """Return the currently selected subentry for reconfigure helpers."""
        if not self._selected_subentry_id:
            raise ValueError("No entity selected")
        subentry = self.config_entry.subentries.get(self._selected_subentry_id)
        if subentry is None:
            raise ValueError("Selected entity no longer exists")
        return subentry

    def _entity_subentries(self) -> list[tuple[str, Any]]:
        """Return entity subentries for this config entry."""
        return [
            (subentry_id, subentry)
            for subentry_id, subentry in self.config_entry.subentries.items()
            if subentry.subentry_type == SUBENTRY_TYPE_ENTITY
        ]

    def _device_entities_map(self) -> dict[str, list[tuple[str, Any]]]:
        """Map device identifiers to entity subentries."""
        device_map: dict[str, list[tuple[str, Any]]] = {}
        for subentry_id, subentry in self._entity_subentries():
            device_id = subentry.data.get(CONF_ENTITY_DEVICE_ID) or subentry.unique_id
            if not device_id:
                continue
            device_map.setdefault(device_id, []).append((subentry_id, subentry))
        return device_map

    def _get_registry_device_labels(self) -> dict[str, str]:
        """Get current registry labels keyed by ADS device identifier."""
        labels: dict[str, str] = {}
        device_registry = dr.async_get(self.hass)
        for device in device_registry.devices.values():
            if self.config_entry.entry_id not in device.config_entries:
                continue
            for domain, identifier in device.identifiers:
                if domain != DOMAIN:
                    continue
                labels[identifier] = device.name_by_user or device.name or identifier
                break
        return labels

    def _get_device_selection_options(self) -> list[dict[str, str]]:
        """Return selectable device list for options step."""
        device_map = self._device_entities_map()
        labels = self._get_registry_device_labels()
        all_device_ids = set(device_map).union(labels)
        options: list[dict[str, str]] = []
        for device_id in all_device_ids:
            label = labels.get(device_id)
            if not label:
                entities = device_map.get(device_id, [])
                if entities:
                    first_entity = entities[0][1]
                    label = (
                        first_entity.data.get(CONF_ENTITY_DEVICE_NAME)
                        or first_entity.data.get(CONF_NAME)
                        or device_id
                    )
                else:
                    label = device_id
            options.append({"label": label, "value": device_id})
        options.sort(key=lambda item: item["label"].lower())
        return options

    def _device_name_for_id(self, device_id: str) -> str:
        """Resolve a display name for a specific ADS device ID."""
        labels = self._get_registry_device_labels()
        if device_id in labels:
            return labels[device_id]
        entities = self._device_entities_map().get(device_id, [])
        if entities:
            first_entity = entities[0][1]
            return (
                first_entity.data.get(CONF_ENTITY_DEVICE_NAME)
                or first_entity.data.get(CONF_NAME)
                or DEFAULT_MIGRATED_DEVICE_NAME
            )
        return device_id

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Step 1: select device."""
        errors: dict[str, str] = {}
        options = self._get_device_selection_options()

        if user_input is not None:
            selected_device_id = user_input.get(CONF_SELECTED_DEVICE_ID)
            if selected_device_id:
                self._selected_device_id = selected_device_id
                return await self.async_step_device_actions()
            errors[CONF_SELECTED_DEVICE_ID] = "required"

        default_device = (
            self._selected_device_id
            if self._selected_device_id
            else (options[0]["value"] if options else "")
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SELECTED_DEVICE_ID, default=default_device): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
            errors=errors,
        )

    def _entity_select_options(self, device_id: str) -> list[dict[str, str]]:
        """Build entity selector options for a selected device."""
        options: list[dict[str, str]] = [{"label": "(No entity selected)", "value": ""}]
        entities = self._device_entities_map().get(device_id, [])
        for subentry_id, subentry in sorted(
            entities, key=lambda item: item[1].title.lower()
        ):
            options.append({"label": subentry.title, "value": subentry_id})
        return options

    def _rename_device(self, device_id: str, new_name: str) -> None:
        """Rename device in registry and persist name to all assigned entities."""
        device_registry = dr.async_get(self.hass)
        device = device_registry.async_get_device(identifiers={(DOMAIN, device_id)})
        if device:
            if device.name_by_user:
                device_registry.async_update_device(device.id, name_by_user=new_name)
            else:
                device_registry.async_update_device(device.id, name=new_name)

        for _, subentry in self._device_entities_map().get(device_id, []):
            new_data = dict(subentry.data)
            new_data[CONF_ENTITY_DEVICE_NAME] = new_name
            self.hass.config_entries.async_update_subentry(
                self.config_entry,
                subentry,
                data=MappingProxyType(new_data),
            )

    def _delete_empty_device(self, device_id: str) -> None:
        """Delete an empty device from the registry."""
        device_registry = dr.async_get(self.hass)
        device = device_registry.async_get_device(identifiers={(DOMAIN, device_id)})
        if not device:
            return
        device_registry.async_update_device(
            device.id,
            remove_config_entry_id=self.config_entry.entry_id,
        )

    async def async_step_device_actions(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 2/3: select entity, rename device, or delete empty device."""
        if not self._selected_device_id:
            return await self.async_step_init()

        errors: dict[str, str] = {}
        current_name = self._device_name_for_id(self._selected_device_id)
        entities = self._device_entities_map().get(self._selected_device_id, [])
        entity_options = self._entity_select_options(self._selected_device_id)

        if user_input is not None:
            selected_subentry_id = user_input.get(CONF_SELECTED_ENTITY_SUBENTRY_ID)
            if selected_subentry_id:
                self._selected_subentry_id = selected_subentry_id
                return await self.async_step_reconfigure()

            requested_action = user_input.get(CONF_DEVICE_ACTION, "")
            new_device_name = (user_input.get(CONF_ENTITY_DEVICE_NAME) or "").strip()
            wants_delete = requested_action == OPTION_DELETE_DEVICE

            if wants_delete:
                if entities:
                    errors["base"] = "device_has_entities"
                elif not user_input.get(CONF_CONFIRM_DELETE):
                    errors[CONF_CONFIRM_DELETE] = "delete_confirmation_required"
                else:
                    self._delete_empty_device(self._selected_device_id)
                    return self.async_create_entry(title="", data={})
            elif new_device_name and new_device_name != current_name:
                self._rename_device(self._selected_device_id, new_device_name)
                return self.async_create_entry(title="", data={})
            else:
                errors["base"] = "no_action_selected"

        return self.async_show_form(
            step_id="device_actions",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_SELECTED_ENTITY_SUBENTRY_ID, default=""): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=entity_options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(CONF_ENTITY_DEVICE_NAME, default=current_name): cv.string,
                    vol.Optional(CONF_DEVICE_ACTION, default=""): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"label": "(None)", "value": ""},
                                {"label": "Delete device", "value": OPTION_DELETE_DEVICE},
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(CONF_CONFIRM_DELETE, default=False): cv.boolean,
                }
            ),
            errors=errors,
        )
