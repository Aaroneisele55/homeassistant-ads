"""Config flow for ADS Custom integration.

All ADS entities configured through the UI live under a single config
subentry ("Entities") on the hub config entry. Individual entities are
distinguished by their own ``unique_id`` and are grouped into different
devices via a per-entity device assignment (existing device or a newly
created one), rather than one subentry per device or per entity.

Both the native subentry flow (accessible from the "Entities" subentry's
"..." menu) and the hub's options flow expose the same experience: select
an entity (or choose to add a new one), then configure it.
"""

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
from .device_groups import (
    async_add_entity_to_single_subentry,
    async_get_or_create_single_entities_subentry,
    async_remove_entity_from_single_subentry,
    async_replace_entity_in_single_subentry,
    get_single_entities_subentry,
    iter_entity_configs,
)
from .device_registry_compat import (
    async_detach_device_from_entry,
    async_get_device_by_identifier,
    device_belongs_to_entry,
)

_LOGGER = logging.getLogger(__name__)

DEVICE_OPTION_CREATE_NEW = "__create_new__"
DEFAULT_NEW_DEVICE_NAME = "ADS Device"
OPTION_ADD_ENTITY = "__add_entity__"
OPTION_DELETE_EMPTY_DEVICES = "__delete_empty_devices__"

CONF_SELECTED_ENTITY_UNIQUE_ID = "selected_entity_unique_id"
CONF_SELECTED_DEVICE_ID = "selected_device_id"
CONF_DELETE_ENTITY = "delete_entity"
CONF_CONFIRM_DELETE = "confirm_delete"

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

ENTITY_TYPE_TITLES = {
    "binary_sensor": "Binary Sensor",
    "sensor": "Sensor",
    "switch": "Switch",
    "light": "Light",
    "cover": "Cover",
    "valve": "Valve",
    "select": "Select",
}

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
    """Validate the user input allows us to connect."""
    net_id = data[CONF_DEVICE]
    ip_address = data.get(CONF_IP_ADDRESS)
    port = data.get(CONF_PORT, 48898)

    def test_connection():
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
        return {SUBENTRY_TYPE_ENTITY: AdsEntitySubentryFlowHandler}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return AdsOptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input[CONF_DEVICE])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_import(self, import_data: dict[str, Any]) -> ConfigFlowResult:
        device = import_data[CONF_DEVICE]
        await self.async_set_unique_id(device)
        self._abort_if_unique_id_configured()

        connection_data = {
            CONF_DEVICE: device,
            CONF_PORT: import_data.get(CONF_PORT, 48898),
        }
        if CONF_IP_ADDRESS in import_data:
            connection_data[CONF_IP_ADDRESS] = import_data[CONF_IP_ADDRESS]

        entities = import_data.get("entities", [])
        return self.async_create_entry(
            title=f"ADS ({device})",
            data=connection_data,
            options={"entities": entities},
        )


class _EntityStepsMixin:
    """Shared "select an entity, then configure it" steps.

    Used by both the native "Entities" subentry flow and the hub options
    flow so add/edit/delete behave identically no matter which entry point
    the user came in through. All entities are stored in the single
    "Entities" subentry; devices are assigned per-entity.
    """

    hass: HomeAssistant
    _entity_data: dict[str, Any]
    _editing_unique_id: str | None

    @property
    def entry(self) -> ConfigEntry:
        raise NotImplementedError

    def _finish(self, reason: str) -> ConfigFlowResult | SubentryFlowResult:
        raise NotImplementedError

    # ── Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _remove_empty_optional_fields(data: dict[str, Any], *field_names: str) -> None:
        for field_name in field_names:
            if field_name not in data:
                continue
            value = data[field_name]
            if value is None:
                data.pop(field_name)
                continue
            if isinstance(value, str) and not value.strip():
                data.pop(field_name)
                continue
            if isinstance(value, (list, dict, set, tuple)) and not value:
                data.pop(field_name)

    @staticmethod
    def _remove_cleared_optional_fields(
        merged_data: dict[str, Any],
        user_input: dict[str, Any],
        *field_names: str,
    ) -> None:
        for field_name in field_names:
            if field_name in merged_data and field_name not in user_input:
                del merged_data[field_name]

    def _entities(self) -> list[dict[str, Any]]:
        subentry = get_single_entities_subentry(self.entry)
        if subentry is None:
            return []
        return iter_entity_configs(dict(subentry.data))

    def _find_entity(self, unique_id: str) -> dict[str, Any] | None:
        for entity in self._entities():
            if (entity.get(CONF_UNIQUE_ID) or entity.get("unique_id")) == unique_id:
                return dict(entity)
        return None

    def _get_device_assignment_options(self) -> list[dict[str, str]]:
        device_registry = dr.async_get(self.hass)
        options: list[dict[str, str]] = []
        seen_identifiers: set[str] = set()

        for device in device_registry.devices.values():
            if not device_belongs_to_entry(device, self.entry.entry_id):
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

    def _device_assignment_schema(self, current_data: dict[str, Any] | None = None) -> dict[Any, Any]:
        options = self._get_device_assignment_options()
        current_device_id = (current_data or {}).get(CONF_ENTITY_DEVICE_ID)
        default = current_device_id if any(o["value"] == current_device_id for o in options) else DEVICE_OPTION_CREATE_NEW
        return {
            vol.Required(CONF_SELECTED_DEVICE_ID, default=default): selector.SelectSelector(
                selector.SelectSelectorConfig(options=options, mode=selector.SelectSelectorMode.DROPDOWN)
            ),
            vol.Optional(CONF_ENTITY_DEVICE_NAME): cv.string,
        }

    def _entity_options_schema(self) -> dict[Any, Any]:
        return {
            vol.Optional(CONF_ENTITY_ICON): selector.IconSelector(selector.IconSelectorConfig()),
            vol.Optional(CONF_ENTITY_CATEGORY): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["", "config", "diagnostic"],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(CONF_ENTITY_PICTURE): cv.string,
        }

    def _resolve_device_assignment(self, user_input: dict[str, Any]) -> tuple[str, str]:
        """Pop the device-selection fields off user_input and resolve them.

        Returns (device_id, device_name) for the entity being saved.
        """
        selected_device_id = user_input.pop(CONF_SELECTED_DEVICE_ID, None)
        typed_name = (user_input.pop(CONF_ENTITY_DEVICE_NAME, "") or "").strip()

        if not selected_device_id or selected_device_id == DEVICE_OPTION_CREATE_NEW:
            device_name = typed_name or user_input.get(CONF_NAME) or DEFAULT_NEW_DEVICE_NAME
            device_id = uuid.uuid4().hex
            return device_id, device_name

        labels = {opt["value"]: opt["label"] for opt in self._get_device_assignment_options()}
        device_name = typed_name or labels.get(selected_device_id) or selected_device_id
        return selected_device_id, device_name

    def _used_device_ids(self) -> set[str]:
        return {
            device_id
            for entity in self._entities()
            if (device_id := entity.get(CONF_ENTITY_DEVICE_ID))
        }

    def _empty_device_ids(self) -> list[str]:
        """Return identifiers of devices on this entry with no assigned entity."""
        used_device_ids = self._used_device_ids()
        device_registry = dr.async_get(self.hass)
        empty_device_ids: list[str] = []

        for device in device_registry.devices.values():
            if not device_belongs_to_entry(device, self.entry.entry_id):
                continue
            for domain, identifier in device.identifiers:
                if domain != DOMAIN:
                    continue
                if identifier not in used_device_ids:
                    empty_device_ids.append(identifier)
                break

        return empty_device_ids

    def _delete_empty_devices(self) -> int:
        device_registry = dr.async_get(self.hass)
        deleted_count = 0

        for device_id in self._empty_device_ids():
            device = async_get_device_by_identifier(
                device_registry, DOMAIN, device_id, self.entry.entry_id
            )
            if not device:
                continue
            async_detach_device_from_entry(device_registry, device, self.entry.entry_id)
            deleted_count += 1

        return deleted_count

    def _save_entity(
        self,
        *,
        entity_type: str,
        user_input: dict[str, Any],
        extra_data: dict[str, Any] | None = None,
    ) -> ConfigFlowResult | SubentryFlowResult:
        device_id, device_name = self._resolve_device_assignment(user_input)

        entity_data: dict[str, Any] = {CONF_ENTITY_TYPE: entity_type, **user_input}
        if extra_data:
            entity_data.update(extra_data)
        self._remove_empty_optional_fields(
            entity_data, CONF_ENTITY_ICON, CONF_ENTITY_CATEGORY, CONF_ENTITY_PICTURE
        )
        entity_data[CONF_ENTITY_DEVICE_ID] = device_id
        entity_data[CONF_ENTITY_DEVICE_NAME] = device_name

        if self._editing_unique_id:
            entity_data[CONF_UNIQUE_ID] = self._editing_unique_id
            async_replace_entity_in_single_subentry(
                self.hass, self.entry, self._editing_unique_id, entity_data
            )
            return self._finish("reconfigure_successful")

        unique_id = entity_data.get(CONF_UNIQUE_ID) or entity_data.get("unique_id") or uuid.uuid4().hex
        entity_data[CONF_UNIQUE_ID] = unique_id
        async_get_or_create_single_entities_subentry(self.hass, self.entry)
        async_add_entity_to_single_subentry(self.hass, self.entry, entity_data)
        return self._finish("entity_added")

    # ── Add new entity ──────────────────────────────────────────────

    async def async_step_add_entity(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        self._editing_unique_id = None
        self._entity_data = {}
        return self.async_show_menu(
            step_id="add_entity",
            menu_options=[
                "add_switch", "add_sensor", "add_binary_sensor", "add_light",
                "add_cover", "add_valve", "add_select",
            ],
        )

    async def async_step_add_switch(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        return await self.async_step_configure_switch()

    async def async_step_add_sensor(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        return await self.async_step_configure_sensor()

    async def async_step_add_binary_sensor(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        return await self.async_step_configure_binary_sensor()

    async def async_step_add_light(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        return await self.async_step_configure_light()

    async def async_step_add_cover(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        return await self.async_step_configure_cover()

    async def async_step_add_valve(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        return await self.async_step_configure_valve()

    async def async_step_add_select(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        return await self.async_step_configure_select()

    # ── Select an existing entity, then configure/delete it ──────────

    async def async_step_select_entity(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        entities = sorted(
            self._entities(),
            key=lambda e: (e.get(CONF_NAME) or "").lower(),
        )
        empty_device_count = len(self._empty_device_ids())
        options = [{"label": "Add new entity", "value": OPTION_ADD_ENTITY}]
        if empty_device_count:
            options.append(
                {
                    "label": f"Delete all empty devices ({empty_device_count})",
                    "value": OPTION_DELETE_EMPTY_DEVICES,
                }
            )
        options += [
            {
                "label": f"{entity.get(CONF_NAME, 'Entity')} ({ENTITY_TYPE_TITLES.get(entity.get(CONF_ENTITY_TYPE), entity.get(CONF_ENTITY_TYPE))})",
                "value": entity.get(CONF_UNIQUE_ID) or entity.get("unique_id"),
            }
            for entity in entities
        ]

        if user_input is not None:
            selected = user_input.get(CONF_SELECTED_ENTITY_UNIQUE_ID)
            if not selected:
                errors["base"] = "no_entity_selected"
            elif selected == OPTION_ADD_ENTITY:
                return await self.async_step_add_entity()
            elif selected == OPTION_DELETE_EMPTY_DEVICES:
                return await self.async_step_delete_empty_devices()
            else:
                entity = self._find_entity(selected)
                if entity is None:
                    errors["base"] = "entity_not_found"
                elif user_input.get(CONF_DELETE_ENTITY):
                    async_remove_entity_from_single_subentry(self.hass, self.entry, selected)
                    return self._finish("entity_deleted")
                else:
                    self._editing_unique_id = selected
                    self._entity_data = entity
                    return await self._async_step_configure_for_type(entity.get(CONF_ENTITY_TYPE))

        return self.async_show_form(
            step_id="select_entity",
            data_schema=vol.Schema({
                vol.Required(CONF_SELECTED_ENTITY_UNIQUE_ID): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=options, mode=selector.SelectSelectorMode.DROPDOWN)
                ),
                vol.Optional(CONF_DELETE_ENTITY, default=False): cv.boolean,
            }),
            errors=errors,
        )

    async def async_step_delete_empty_devices(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        empty_device_count = len(self._empty_device_ids())

        if user_input is not None:
            if not empty_device_count:
                errors["base"] = "no_empty_devices"
            elif not user_input.get(CONF_CONFIRM_DELETE):
                errors[CONF_CONFIRM_DELETE] = "delete_confirmation_required"
            else:
                deleted_count = self._delete_empty_devices()
                _LOGGER.info(
                    "Deleted %d empty device(s) on hub '%s'",
                    deleted_count,
                    self.entry.title,
                )
                return self._finish("empty_devices_deleted")

        return self.async_show_form(
            step_id="delete_empty_devices",
            data_schema=vol.Schema({
                vol.Optional(CONF_CONFIRM_DELETE, default=False): cv.boolean,
            }),
            description_placeholders={"count": str(empty_device_count)},
            errors=errors,
        )

    async def _async_step_configure_for_type(self, entity_type: str | None) -> SubentryFlowResult:
        mapping = {
            "switch": self.async_step_configure_switch,
            "sensor": self.async_step_configure_sensor,
            "binary_sensor": self.async_step_configure_binary_sensor,
            "light": self.async_step_configure_light,
            "cover": self.async_step_configure_cover,
            "valve": self.async_step_configure_valve,
            "select": self.async_step_configure_select,
        }
        step = mapping.get(entity_type or "")
        if step is None:
            return self._finish("entity_type_not_supported")
        return await step()

    # ── Configure (add or edit) individual entity types ──────────────

    async def async_step_configure_switch(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            return self._save_entity(entity_type="switch", user_input=user_input)

        entity = self._entity_data
        return self.async_show_form(
            step_id="configure_switch",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema({
                    vol.Required(CONF_ADS_VAR): cv.string,
                    vol.Required(CONF_NAME): cv.string,
                    **self._device_assignment_schema(entity),
                    **self._entity_options_schema(),
                }),
                entity,
            ),
            errors=errors,
        )

    async def async_step_configure_sensor(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._remove_empty_optional_fields(user_input, CONF_DEVICE_CLASS, CONF_STATE_CLASS)
            return self._save_entity(entity_type="sensor", user_input=user_input)

        entity = self._entity_data
        return self.async_show_form(
            step_id="configure_sensor",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema({
                    vol.Required(CONF_ADS_VAR): cv.string,
                    vol.Required(CONF_NAME): cv.string,
                    vol.Optional(CONF_ADS_TYPE, default="int"): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=[t.value for t in AdsType], mode=selector.SelectSelectorMode.DROPDOWN)
                    ),
                    vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
                    vol.Optional(CONF_DEVICE_CLASS): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=SENSOR_DEVICE_CLASSES, mode=selector.SelectSelectorMode.DROPDOWN)
                    ),
                    vol.Optional(CONF_STATE_CLASS): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=["measurement", "total", "total_increasing"], mode=selector.SelectSelectorMode.DROPDOWN)
                    ),
                    **self._device_assignment_schema(entity),
                    **self._entity_options_schema(),
                }),
                entity,
            ),
            errors=errors,
        )

    async def async_step_configure_binary_sensor(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._remove_empty_optional_fields(user_input, CONF_DEVICE_CLASS)
            return self._save_entity(entity_type="binary_sensor", user_input=user_input)

        entity = self._entity_data
        return self.async_show_form(
            step_id="configure_binary_sensor",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema({
                    vol.Required(CONF_ADS_VAR): cv.string,
                    vol.Required(CONF_NAME): cv.string,
                    vol.Optional(CONF_ADS_TYPE, default="bool"): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=["bool", "real"], mode=selector.SelectSelectorMode.DROPDOWN)
                    ),
                    vol.Optional(CONF_DEVICE_CLASS): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=BINARY_SENSOR_DEVICE_CLASSES, mode=selector.SelectSelectorMode.DROPDOWN)
                    ),
                    **self._device_assignment_schema(entity),
                    **self._entity_options_schema(),
                }),
                entity,
            ),
            errors=errors,
        )

    async def async_step_configure_light(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            return self._save_entity(entity_type="light", user_input=user_input)

        entity = self._entity_data
        return self.async_show_form(
            step_id="configure_light",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema({
                    vol.Required(CONF_ADS_VAR): cv.string,
                    vol.Required(CONF_NAME): cv.string,
                    vol.Optional("adsvar_brightness"): cv.string,
                    vol.Optional("adsvar_brightness_type", default="byte"): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=["byte", "uint"], mode=selector.SelectSelectorMode.DROPDOWN)
                    ),
                    vol.Optional("adsvar_brightness_scale", default=255): vol.All(
                        vol.Coerce(int), vol.Range(min=1, max=65535)
                    ),
                    **self._device_assignment_schema(entity),
                    **self._entity_options_schema(),
                }),
                entity,
            ),
            errors=errors,
        )

    async def async_step_configure_cover(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            for var in COVER_ADS_VAR_FIELDS:
                if var in user_input and isinstance(user_input[var], str) and not user_input[var].strip():
                    user_input.pop(var)
            self._remove_empty_optional_fields(user_input, CONF_DEVICE_CLASS)
            if not user_input.get(CONF_ADS_VAR) and not user_input.get("adsvar_position"):
                errors["base"] = "no_state_var"
            else:
                return self._save_entity(entity_type="cover", user_input=user_input)

        entity = self._entity_data
        return self.async_show_form(
            step_id="configure_cover",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema({
                    vol.Optional(CONF_ADS_VAR): cv.string,
                    vol.Required(CONF_NAME): cv.string,
                    vol.Optional("adsvar_position"): cv.string,
                    vol.Optional("adsvar_position_type", default="byte"): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=["byte", "uint"], mode=selector.SelectSelectorMode.DROPDOWN)
                    ),
                    vol.Optional("adsvar_set_position"): cv.string,
                    vol.Optional("adsvar_open"): cv.string,
                    vol.Optional("adsvar_close"): cv.string,
                    vol.Optional("adsvar_stop"): cv.string,
                    vol.Optional("inverted", default=False): cv.boolean,
                    vol.Optional(CONF_DEVICE_CLASS): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=COVER_DEVICE_CLASSES, mode=selector.SelectSelectorMode.DROPDOWN)
                    ),
                    **self._device_assignment_schema(entity),
                    **self._entity_options_schema(),
                }),
                entity,
            ),
            errors=errors,
        )

    async def async_step_configure_valve(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._remove_empty_optional_fields(user_input, CONF_DEVICE_CLASS)
            return self._save_entity(entity_type="valve", user_input=user_input)

        entity = self._entity_data
        return self.async_show_form(
            step_id="configure_valve",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema({
                    vol.Required(CONF_ADS_VAR): cv.string,
                    vol.Required(CONF_NAME): cv.string,
                    vol.Optional(CONF_DEVICE_CLASS): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=VALVE_DEVICE_CLASSES, mode=selector.SelectSelectorMode.DROPDOWN)
                    ),
                    **self._device_assignment_schema(entity),
                    **self._entity_options_schema(),
                }),
                entity,
            ),
            errors=errors,
        )

    async def async_step_configure_select(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            options = user_input.get("options", [])
            if isinstance(options, str):
                options = [opt.strip() for opt in options.split(",") if opt.strip()]
            if not options:
                errors["options"] = "no_options"
            else:
                return self._save_entity(
                    entity_type="select",
                    user_input=user_input,
                    extra_data={"options": options},
                )

        entity = self._entity_data
        options_list = entity.get("options", [])
        options_str = ", ".join(options_list) if isinstance(options_list, list) else (str(options_list) if options_list else "")

        return self.async_show_form(
            step_id="configure_select",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema({
                    vol.Required(CONF_ADS_VAR): cv.string,
                    vol.Required(CONF_NAME): cv.string,
                    vol.Required("options"): cv.string,
                    **self._device_assignment_schema(entity),
                    **self._entity_options_schema(),
                }),
                {**entity, "options": options_str},
            ),
            errors=errors,
        )


class AdsEntitySubentryFlowHandler(_EntityStepsMixin, ConfigSubentryFlow):
    """Handle the "Entities" subentry flow (add/select/edit/delete)."""

    def __init__(self) -> None:
        self._entity_data = {}
        self._editing_unique_id = None

    @property
    def entry(self) -> ConfigEntry:
        if hasattr(self, "handler") and hasattr(self.handler, "config_entry"):
            return self.handler.config_entry
        return self._get_entry()

    def _finish(self, reason: str) -> SubentryFlowResult:
        return self.async_abort(reason=reason)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        """Entry point when creating the subentry for the first time."""
        return await self.async_step_add_entity()

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        """Entry point from the subentry's "Reconfigure" menu item."""
        return await self.async_step_select_entity()


class AdsOptionsFlowHandler(_EntityStepsMixin, OptionsFlow):
    """Handle hub-level entity management via the options system.

    This is the primary "select an entity, then configure it" experience:
    the hub's single "Entities" subentry holds every entity, grouped into
    devices per the user's own assignment.
    """

    def __init__(self) -> None:
        self._entity_data = {}
        self._editing_unique_id = None

    @property
    def entry(self) -> ConfigEntry:
        return self.config_entry

    def _finish(self, reason: str) -> ConfigFlowResult:
        return self.async_create_entry(title="", data={})

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return await self.async_step_select_entity(user_input)
