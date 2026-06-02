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
    CONF_DEVICE_ENTITIES,
    CONF_ENTITY_DEVICE_ID,
    CONF_ENTITY_DEVICE_NAME,
    CONF_ENTITY_CATEGORY,
    CONF_ENTITY_ICON,
    CONF_ENTITY_PICTURE,
    DOMAIN,
    AdsType,
    SUBENTRY_TYPE_ENTITY,
)
from .subentry_helpers import iter_subentry_entities

_LOGGER = logging.getLogger(__name__)
DEVICE_OPTION_CREATE_NEW = "__create_new__"
DEFAULT_NEW_DEVICE_NAME = "ADS Device"
DEFAULT_MIGRATED_DEVICE_NAME = "Default ADS Device"
OPTION_DELETE_DEVICE = "__delete_device__"
OPTION_DELETE_EMPTY_DEVICES = "__delete_empty_devices__"
OPTION_MOVE_ENTITIES = "__move_entities__"
CONF_SELECTED_DEVICE_ID = "selected_device_id"
CONF_SELECTED_ENTITY_SUBENTRY_ID = "selected_entity_subentry_id"
CONF_SELECTED_ENTITY_UNIQUE_ID = "selected_entity_unique_id"
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


class AdsEntitySubentryFlowHandler(ConfigSubentryFlow):
    """Handle ADS entity subentry flow for adding/editing entities."""

    _entity_data: dict[str, Any]

    @property
    def entry(self) -> ConfigEntry:
        if hasattr(self, "handler") and hasattr(self.handler, "config_entry"):
            return self.handler.config_entry
        return self._get_entry()

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

    @staticmethod
    def _resolve_device_assignment(
        user_input: dict[str, Any],
        *,
        current_data: dict[str, Any] | None = None,
    ) -> bool:
        selected_device_id = user_input.get(CONF_ENTITY_DEVICE_ID)
        if selected_device_id is None:
            if current_data is not None:
                existing_id = current_data.get(CONF_ENTITY_DEVICE_ID) or current_data.get(CONF_UNIQUE_ID)
                if existing_id:
                    user_input[CONF_ENTITY_DEVICE_ID] = existing_id
                    user_input.pop(CONF_ENTITY_DEVICE_NAME, None)
                    return True
            return False

        if selected_device_id == DEVICE_OPTION_CREATE_NEW:
            new_device_name = (user_input.get(CONF_ENTITY_DEVICE_NAME) or "").strip()
            if not new_device_name:
                return False
            user_input[CONF_ENTITY_DEVICE_ID] = uuid.uuid4().hex
            user_input[CONF_ENTITY_DEVICE_NAME] = new_device_name
            return True

        user_input[CONF_ENTITY_DEVICE_ID] = selected_device_id
        user_input.pop(CONF_ENTITY_DEVICE_NAME, None)
        return True

    def _get_device_assignment_options(self) -> list[dict[str, str]]:
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
        options = self._get_device_assignment_options()
        current_device_id = (
            current_data.get(CONF_ENTITY_DEVICE_ID) if current_data else None
        )
        if current_data and not current_device_id:
            current_device_id = current_data.get(CONF_UNIQUE_ID)

        if current_device_id and all(
            option["value"] != current_device_id for option in options
        ):
            fallback_label = current_data.get(
                CONF_ENTITY_DEVICE_NAME,
                current_data.get(CONF_NAME, current_device_id),
            )
            options.insert(0, {"label": fallback_label, "value": current_device_id})

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
        if not old_name or old_name == new_name:
            return

        device_registry = dr.async_get(self.hass)
        device = device_registry.async_get_device(identifiers={(DOMAIN, subentry_unique_id)})

        if not device:
            _LOGGER.debug("No device found for subentry '%s', skipping device name update", subentry_unique_id)
            return

        current_device_name = device.name_by_user or device.name
        if current_device_name != old_name:
            _LOGGER.debug(
                "Device name '%s' differs from old subentry name '%s', skipping update",
                current_device_name, old_name,
            )
            return

        _LOGGER.info("Subentry '%s' renamed to '%s', updating device", old_name, new_name)

        if device.name_by_user and device.name_by_user == old_name:
            device_registry.async_update_device(device.id, name_by_user=new_name)
        else:
            device_registry.async_update_device(device.id, name=new_name)

    def _should_update_legacy_device_name(self, user_input: dict[str, Any]) -> bool:
        """Return whether a legacy implicit device should follow the entity rename."""

        if self._entity_data.get(CONF_ENTITY_DEVICE_ID):
            return False

        return user_input.get(CONF_ENTITY_DEVICE_ID) == self._entity_data.get(CONF_UNIQUE_ID)

    @staticmethod
    def _entity_title(entity_data: dict[str, Any]) -> str:
        entity_name = entity_data.get(CONF_NAME, "Entity")
        entity_type = str(entity_data.get(CONF_ENTITY_TYPE, "entity")).replace("_", " ").title()
        return f"{entity_name} ({entity_type})"

    def _subentry_entities(self, subentry: Any) -> list[dict[str, Any]]:
        entities = subentry.data.get(CONF_DEVICE_ENTITIES)
        if isinstance(entities, list):
            return [dict(entity) for entity in entities if isinstance(entity, dict)]
        return [dict(subentry.data)]

    def _subentry_device_id(self, subentry: Any) -> str | None:
        return subentry.data.get(CONF_ENTITY_DEVICE_ID) or subentry.unique_id

    def _subentry_device_name(self, subentry: Any, fallback: str | None = None) -> str:
        return (
            subentry.data.get(CONF_ENTITY_DEVICE_NAME)
            or subentry.title
            or fallback
            or DEFAULT_MIGRATED_DEVICE_NAME
        )

    def _resolve_registry_device_name(self, device_id: str, fallback_name: str) -> str:
        device_registry = dr.async_get(self.hass)
        device = device_registry.async_get_device(identifiers={(DOMAIN, device_id)})
        if not device:
            return fallback_name
        return device.name_by_user or device.name or fallback_name

    def _find_device_subentry(self, device_id: str) -> tuple[str, Any] | None:
        for subentry_id, subentry in self.entry.subentries.items():
            if subentry.subentry_type != SUBENTRY_TYPE_ENTITY:
                continue
            if self._subentry_device_id(subentry) == device_id:
                return subentry_id, subentry
        return None

    def _normalize_entity_payload_for_device(
        self,
        entity_data: dict[str, Any],
        *,
        device_id: str,
        device_name: str,
    ) -> dict[str, Any]:
        normalized = dict(entity_data)
        normalized[CONF_ENTITY_DEVICE_ID] = device_id
        normalized[CONF_ENTITY_DEVICE_NAME] = device_name
        return normalized

    def async_create_entry(
        self,
        title: str,
        data: MappingProxyType[str, Any] | dict[str, Any],
        **kwargs: Any,
    ) -> SubentryFlowResult:
        """Create subentries grouped by device while keeping legacy compatibility."""

        payload = dict(data)
        if payload.get(CONF_ENTITY_TYPE):
            device_id = payload.get(CONF_ENTITY_DEVICE_ID)
            if not device_id:
                return self.async_abort(reason="entity_type_not_supported")

            fallback_device_name = payload.get(CONF_ENTITY_DEVICE_NAME) or payload.get(CONF_NAME) or DEFAULT_NEW_DEVICE_NAME
            device_name = self._resolve_registry_device_name(device_id, fallback_device_name)
            normalized_entity = self._normalize_entity_payload_for_device(
                payload,
                device_id=device_id,
                device_name=device_name,
            )

            existing = self._find_device_subentry(device_id)
            if existing is None:
                device_payload = {
                    CONF_ENTITY_DEVICE_ID: device_id,
                    CONF_ENTITY_DEVICE_NAME: device_name,
                    CONF_DEVICE_ENTITIES: [normalized_entity],
                }
                return super().async_create_entry(
                    title=device_name,
                    data=device_payload,
                    unique_id=device_id,
                )

            _, subentry = existing
            entities = self._subentry_entities(subentry)
            entities.append(normalized_entity)
            updated_payload = {
                CONF_ENTITY_DEVICE_ID: device_id,
                CONF_ENTITY_DEVICE_NAME: device_name,
                CONF_DEVICE_ENTITIES: entities,
            }
            self.hass.config_entries.async_update_subentry(
                self.entry,
                subentry,
                data=MappingProxyType(updated_payload),
                title=device_name,
            )
            return self.async_abort(reason="entity_added")

        return super().async_create_entry(title=title, data=payload, **kwargs)

    def _persist_reconfigured_entity(
        self,
        new_entity_data: dict[str, Any],
        *,
        legacy_title: str | None = None,
    ) -> None:
        subentry = self._get_reconfigure_subentry()
        entities = self._subentry_entities(subentry)
        is_device_subentry = isinstance(subentry.data.get(CONF_DEVICE_ENTITIES), list)

        if not is_device_subentry:
            self.hass.config_entries.async_update_subentry(
                self.entry,
                subentry,
                data=MappingProxyType(new_entity_data),
                title=legacy_title,
            )
            return

        selected_unique_id = (
            getattr(self, "_selected_entity_unique_id", None)
            or self._entity_data.get(CONF_UNIQUE_ID)
            or self._entity_data.get("unique_id")
        )
        if not selected_unique_id:
            selected_unique_id = entities[0].get(CONF_UNIQUE_ID) or entities[0].get("unique_id")

        current_device_id = self._subentry_device_id(subentry)
        current_device_name = self._subentry_device_name(subentry, self._entity_data.get(CONF_NAME))
        updated_entity = self._normalize_entity_payload_for_device(
            new_entity_data,
            device_id=current_device_id or new_entity_data.get(CONF_ENTITY_DEVICE_ID),
            device_name=current_device_name,
        )

        replaced = False
        for index, entity in enumerate(entities):
            entity_unique_id = entity.get(CONF_UNIQUE_ID) or entity.get("unique_id")
            if entity_unique_id == selected_unique_id:
                entities[index] = updated_entity
                replaced = True
                break

        if not replaced:
            entities.append(updated_entity)

        updated_payload = {
            CONF_ENTITY_DEVICE_ID: current_device_id,
            CONF_ENTITY_DEVICE_NAME: current_device_name,
            CONF_DEVICE_ENTITIES: entities,
        }
        self.hass.config_entries.async_update_subentry(
            self.entry,
            subentry,
            data=MappingProxyType(updated_payload),
            title=current_device_name,
        )

    # ── Add new entity ──────────────────────────────────────────────

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        return self.async_show_menu(
            step_id="user",
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

    # ── Configure new entities ──────────────────────────────────────

    async def async_step_configure_switch(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            if not self._resolve_device_assignment(user_input):
                errors[CONF_ENTITY_DEVICE_NAME] = "device_name_required"
            else:
                unique_id = uuid.uuid4().hex
                return self.async_create_entry(
                    title=f"{user_input[CONF_NAME]} (Switch)",
                    data={CONF_ENTITY_TYPE: "switch", **user_input, "unique_id": unique_id},
                    unique_id=unique_id,
                )

        return self.async_show_form(
            step_id="configure_switch",
            data_schema=vol.Schema({
                vol.Required(CONF_ADS_VAR): cv.string,
                vol.Required(CONF_NAME): cv.string,
                **self._device_assignment_schema(),
            }),
            errors=errors,
        )

    async def async_step_configure_sensor(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._remove_empty_optional_fields(user_input, CONF_DEVICE_CLASS, CONF_STATE_CLASS)
            if not self._resolve_device_assignment(user_input):
                errors[CONF_ENTITY_DEVICE_NAME] = "device_name_required"
            else:
                unique_id = uuid.uuid4().hex
                return self.async_create_entry(
                    title=f"{user_input[CONF_NAME]} (Sensor)",
                    data={CONF_ENTITY_TYPE: "sensor", **user_input, "unique_id": unique_id},
                    unique_id=unique_id,
                )

        return self.async_show_form(
            step_id="configure_sensor",
            data_schema=vol.Schema({
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
                **self._device_assignment_schema(),
            }),
            errors=errors,
        )

    async def async_step_configure_binary_sensor(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._remove_empty_optional_fields(user_input, CONF_DEVICE_CLASS)
            if not self._resolve_device_assignment(user_input):
                errors[CONF_ENTITY_DEVICE_NAME] = "device_name_required"
            else:
                unique_id = uuid.uuid4().hex
                return self.async_create_entry(
                    title=f"{user_input[CONF_NAME]} (Binary Sensor)",
                    data={CONF_ENTITY_TYPE: "binary_sensor", **user_input, "unique_id": unique_id},
                    unique_id=unique_id,
                )

        return self.async_show_form(
            step_id="configure_binary_sensor",
            data_schema=vol.Schema({
                vol.Required(CONF_ADS_VAR): cv.string,
                vol.Required(CONF_NAME): cv.string,
                vol.Optional(CONF_ADS_TYPE, default="bool"): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=["bool", "real"], mode=selector.SelectSelectorMode.DROPDOWN)
                ),
                vol.Optional(CONF_DEVICE_CLASS): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=BINARY_SENSOR_DEVICE_CLASSES, mode=selector.SelectSelectorMode.DROPDOWN)
                ),
                **self._device_assignment_schema(),
            }),
            errors=errors,
        )

    async def async_step_configure_light(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            if not self._resolve_device_assignment(user_input):
                errors[CONF_ENTITY_DEVICE_NAME] = "device_name_required"
            else:
                unique_id = uuid.uuid4().hex
                return self.async_create_entry(
                    title=f"{user_input[CONF_NAME]} (Light)",
                    data={CONF_ENTITY_TYPE: "light", **user_input, "unique_id": unique_id},
                    unique_id=unique_id,
                )

        return self.async_show_form(
            step_id="configure_light",
            data_schema=vol.Schema({
                vol.Required(CONF_ADS_VAR): cv.string,
                vol.Required(CONF_NAME): cv.string,
                vol.Optional("adsvar_brightness"): cv.string,
                vol.Optional("adsvar_brightness_type", default="byte"): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=["byte", "uint"], mode=selector.SelectSelectorMode.DROPDOWN)
                ),
                vol.Optional("adsvar_brightness_scale", default=255): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=65535)
                ),
                **self._device_assignment_schema(),
            }),
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
            elif not self._resolve_device_assignment(user_input):
                errors[CONF_ENTITY_DEVICE_NAME] = "device_name_required"
            else:
                unique_id = uuid.uuid4().hex
                return self.async_create_entry(
                    title=f"{user_input[CONF_NAME]} (Cover)",
                    data={CONF_ENTITY_TYPE: "cover", **user_input, "unique_id": unique_id},
                    unique_id=unique_id,
                )

        return self.async_show_form(
            step_id="configure_cover",
            data_schema=vol.Schema({
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
                **self._device_assignment_schema(),
            }),
            errors=errors,
        )

    async def async_step_configure_valve(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._remove_empty_optional_fields(user_input, CONF_DEVICE_CLASS)
            if not self._resolve_device_assignment(user_input):
                errors[CONF_ENTITY_DEVICE_NAME] = "device_name_required"
            else:
                unique_id = uuid.uuid4().hex
                return self.async_create_entry(
                    title=f"{user_input[CONF_NAME]} (Valve)",
                    data={CONF_ENTITY_TYPE: "valve", **user_input, "unique_id": unique_id},
                    unique_id=unique_id,
                )

        return self.async_show_form(
            step_id="configure_valve",
            data_schema=vol.Schema({
                vol.Required(CONF_ADS_VAR): cv.string,
                vol.Required(CONF_NAME): cv.string,
                vol.Optional(CONF_DEVICE_CLASS): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=VALVE_DEVICE_CLASSES, mode=selector.SelectSelectorMode.DROPDOWN)
                ),
                **self._device_assignment_schema(),
            }),
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
            elif not self._resolve_device_assignment(user_input):
                errors[CONF_ENTITY_DEVICE_NAME] = "device_name_required"
            else:
                unique_id = uuid.uuid4().hex
                return self.async_create_entry(
                    title=f"{user_input[CONF_NAME]} (Select)",
                    data={CONF_ENTITY_TYPE: "select", **user_input, "options": options, "unique_id": unique_id},
                    unique_id=unique_id,
                )

        return self.async_show_form(
            step_id="configure_select",
            data_schema=vol.Schema({
                vol.Required(CONF_ADS_VAR): cv.string,
                vol.Required(CONF_NAME): cv.string,
                vol.Required("options"): cv.string,
                **self._device_assignment_schema(),
            }),
            errors=errors,
        )

    # ── Reconfigure existing entity ─────────────────────────────────

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        subentry = self._get_reconfigure_subentry()
        entities = self._subentry_entities(subentry)

        if isinstance(subentry.data.get(CONF_DEVICE_ENTITIES), list):
            if user_input is not None:
                selected_unique_id = user_input.get(CONF_SELECTED_ENTITY_UNIQUE_ID)
                if selected_unique_id:
                    self._selected_entity_unique_id = selected_unique_id

            selected_unique_id = getattr(self, "_selected_entity_unique_id", None)
            if not selected_unique_id:
                default_entity = entities[0] if entities else {}
                options = [
                    {
                        "label": self._entity_title(entity_data),
                        "value": entity_data.get(CONF_UNIQUE_ID) or entity_data.get("unique_id"),
                    }
                    for entity_data in entities
                    if entity_data.get(CONF_UNIQUE_ID) or entity_data.get("unique_id")
                ]
                return self.async_show_form(
                    step_id="reconfigure",
                    data_schema=vol.Schema(
                        {
                            vol.Required(
                                CONF_SELECTED_ENTITY_UNIQUE_ID,
                                default=(
                                    default_entity.get(CONF_UNIQUE_ID)
                                    or default_entity.get("unique_id")
                                    or ""
                                ),
                            ): selector.SelectSelector(
                                selector.SelectSelectorConfig(
                                    options=options,
                                    mode=selector.SelectSelectorMode.DROPDOWN,
                                )
                            )
                        }
                    ),
                )

            selected_entity = next(
                (
                    entity_data
                    for entity_data in entities
                    if (entity_data.get(CONF_UNIQUE_ID) or entity_data.get("unique_id")) == selected_unique_id
                ),
                None,
            )
            if selected_entity is None:
                self._selected_entity_unique_id = None
                return await self.async_step_reconfigure()

            self._entity_data = dict(selected_entity)
            self._entity_data.setdefault(CONF_ENTITY_DEVICE_ID, self._subentry_device_id(subentry))
            self._entity_data.setdefault(CONF_ENTITY_DEVICE_NAME, self._subentry_device_name(subentry))
        else:
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

    async def async_step_reconfigure_switch(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            if not self._resolve_device_assignment(user_input, current_data=self._entity_data):
                errors[CONF_ENTITY_DEVICE_NAME] = "device_name_required"
            else:
                new_data = dict(self._entity_data)
                new_data.update(user_input)
                subentry = self._get_reconfigure_subentry()
                new_title = f"{user_input[CONF_NAME]} (Switch)"
                old_name = self._entity_data.get(CONF_NAME)
                new_name = user_input[CONF_NAME]
                if subentry.unique_id and self._should_update_legacy_device_name(user_input):
                    self._update_device_name_if_changed(subentry.unique_id, old_name, new_name)
                self._persist_reconfigured_entity(new_data, legacy_title=new_title)
                return self.async_abort(reason="reconfigure_successful")

        entity = self._entity_data
        return self.async_show_form(
            step_id="reconfigure_switch",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema({
                    vol.Required(CONF_ADS_VAR): cv.string,
                    vol.Required(CONF_NAME): cv.string,
                    **self._device_assignment_schema(entity),
                }),
                entity,
            ),
            errors=errors,
        )

    async def async_step_reconfigure_sensor(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            if not self._resolve_device_assignment(user_input, current_data=self._entity_data):
                errors[CONF_ENTITY_DEVICE_NAME] = "device_name_required"
            else:
                new_data = dict(self._entity_data)
                new_data.update(user_input)
                self._remove_empty_optional_fields(new_data, CONF_DEVICE_CLASS, CONF_STATE_CLASS)
                self._remove_cleared_optional_fields(new_data, user_input, CONF_DEVICE_CLASS, CONF_STATE_CLASS)
                subentry = self._get_reconfigure_subentry()
                new_title = f"{user_input[CONF_NAME]} (Sensor)"
                old_name = self._entity_data.get(CONF_NAME)
                new_name = user_input[CONF_NAME]
                if subentry.unique_id and self._should_update_legacy_device_name(user_input):
                    self._update_device_name_if_changed(subentry.unique_id, old_name, new_name)
                self._persist_reconfigured_entity(new_data, legacy_title=new_title)
                return self.async_abort(reason="reconfigure_successful")

        entity = self._entity_data
        schema_dict: dict[Any, Any] = {
            vol.Required(CONF_ADS_VAR): cv.string,
            vol.Required(CONF_NAME): cv.string,
            vol.Optional(CONF_ADS_TYPE): selector.SelectSelector(
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
        }

        return self.async_show_form(
            step_id="reconfigure_sensor",
            data_schema=self.add_suggested_values_to_schema(vol.Schema(schema_dict), entity),
            errors=errors,
        )

    async def async_step_reconfigure_binary_sensor(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            if not self._resolve_device_assignment(user_input, current_data=self._entity_data):
                errors[CONF_ENTITY_DEVICE_NAME] = "device_name_required"
            else:
                new_data = dict(self._entity_data)
                new_data.update(user_input)
                self._remove_empty_optional_fields(new_data, CONF_DEVICE_CLASS)
                self._remove_cleared_optional_fields(new_data, user_input, CONF_DEVICE_CLASS)
                subentry = self._get_reconfigure_subentry()
                new_title = f"{user_input[CONF_NAME]} (Binary Sensor)"
                old_name = self._entity_data.get(CONF_NAME)
                new_name = user_input[CONF_NAME]
                if subentry.unique_id and self._should_update_legacy_device_name(user_input):
                    self._update_device_name_if_changed(subentry.unique_id, old_name, new_name)
                self._persist_reconfigured_entity(new_data, legacy_title=new_title)
                return self.async_abort(reason="reconfigure_successful")

        entity = self._entity_data
        schema_dict: dict[Any, Any] = {
            vol.Required(CONF_ADS_VAR): cv.string,
            vol.Required(CONF_NAME): cv.string,
            vol.Optional(CONF_ADS_TYPE): selector.SelectSelector(
                selector.SelectSelectorConfig(options=["bool", "real"], mode=selector.SelectSelectorMode.DROPDOWN)
            ),
            vol.Optional(CONF_DEVICE_CLASS): selector.SelectSelector(
                selector.SelectSelectorConfig(options=BINARY_SENSOR_DEVICE_CLASSES, mode=selector.SelectSelectorMode.DROPDOWN)
            ),
            **self._device_assignment_schema(entity),
        }

        return self.async_show_form(
            step_id="reconfigure_binary_sensor",
            data_schema=self.add_suggested_values_to_schema(vol.Schema(schema_dict), entity),
            errors=errors,
        )

    async def async_step_reconfigure_light(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            if not self._resolve_device_assignment(user_input, current_data=self._entity_data):
                errors[CONF_ENTITY_DEVICE_NAME] = "device_name_required"
            else:
                new_data = dict(self._entity_data)
                new_data.update(user_input)
                subentry = self._get_reconfigure_subentry()
                new_title = f"{user_input[CONF_NAME]} (Light)"
                old_name = self._entity_data.get(CONF_NAME)
                new_name = user_input[CONF_NAME]
                if subentry.unique_id and self._should_update_legacy_device_name(user_input):
                    self._update_device_name_if_changed(subentry.unique_id, old_name, new_name)
                self._persist_reconfigured_entity(new_data, legacy_title=new_title)
                return self.async_abort(reason="reconfigure_successful")

        entity = self._entity_data
        schema_dict: dict[Any, Any] = {
            vol.Required(CONF_ADS_VAR): cv.string,
            vol.Required(CONF_NAME): cv.string,
            vol.Optional("adsvar_brightness"): cv.string,
            vol.Optional("adsvar_brightness_type"): selector.SelectSelector(
                selector.SelectSelectorConfig(options=["byte", "uint"], mode=selector.SelectSelectorMode.DROPDOWN)
            ),
            vol.Optional("adsvar_brightness_scale"): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=65535)
            ),
            **self._device_assignment_schema(entity),
        }

        return self.async_show_form(
            step_id="reconfigure_light",
            data_schema=self.add_suggested_values_to_schema(vol.Schema(schema_dict), entity),
            errors=errors,
        )

    async def async_step_reconfigure_cover(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
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
                self._remove_empty_optional_fields(new_data, CONF_DEVICE_CLASS)
                self._remove_cleared_optional_fields(new_data, user_input, CONF_DEVICE_CLASS)
                subentry = self._get_reconfigure_subentry()
                new_title = f"{user_input[CONF_NAME]} (Cover)"
                old_name = self._entity_data.get(CONF_NAME)
                new_name = user_input[CONF_NAME]
                if subentry.unique_id and self._should_update_legacy_device_name(user_input):
                    self._update_device_name_if_changed(subentry.unique_id, old_name, new_name)
                self._persist_reconfigured_entity(new_data, legacy_title=new_title)
                return self.async_abort(reason="reconfigure_successful")

        entity = self._entity_data
        schema_dict: dict[Any, Any] = {
            vol.Required(CONF_NAME): cv.string,
            vol.Optional(CONF_ADS_VAR): cv.string,
            vol.Optional("adsvar_position"): cv.string,
            vol.Optional("adsvar_position_type"): selector.SelectSelector(
                selector.SelectSelectorConfig(options=["byte", "uint"], mode=selector.SelectSelectorMode.DROPDOWN)
            ),
            vol.Optional("adsvar_set_position"): cv.string,
            vol.Optional("adsvar_open"): cv.string,
            vol.Optional("adsvar_close"): cv.string,
            vol.Optional("adsvar_stop"): cv.string,
            vol.Optional("inverted"): cv.boolean,
            vol.Optional(CONF_DEVICE_CLASS): selector.SelectSelector(
                selector.SelectSelectorConfig(options=COVER_DEVICE_CLASSES, mode=selector.SelectSelectorMode.DROPDOWN)
            ),
            **self._device_assignment_schema(entity),
        }

        return self.async_show_form(
            step_id="reconfigure_cover",
            data_schema=self.add_suggested_values_to_schema(vol.Schema(schema_dict), entity),
            errors=errors,
        )

    async def async_step_reconfigure_valve(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            if not self._resolve_device_assignment(user_input, current_data=self._entity_data):
                errors[CONF_ENTITY_DEVICE_NAME] = "device_name_required"
            else:
                new_data = dict(self._entity_data)
                new_data.update(user_input)
                self._remove_empty_optional_fields(new_data, CONF_DEVICE_CLASS)
                self._remove_cleared_optional_fields(new_data, user_input, CONF_DEVICE_CLASS)
                subentry = self._get_reconfigure_subentry()
                new_title = f"{user_input[CONF_NAME]} (Valve)"
                old_name = self._entity_data.get(CONF_NAME)
                new_name = user_input[CONF_NAME]
                if subentry.unique_id and self._should_update_legacy_device_name(user_input):
                    self._update_device_name_if_changed(subentry.unique_id, old_name, new_name)
                self._persist_reconfigured_entity(new_data, legacy_title=new_title)
                return self.async_abort(reason="reconfigure_successful")

        entity = self._entity_data
        schema_dict: dict[Any, Any] = {
            vol.Required(CONF_ADS_VAR): cv.string,
            vol.Required(CONF_NAME): cv.string,
            vol.Optional(CONF_DEVICE_CLASS): selector.SelectSelector(
                selector.SelectSelectorConfig(options=VALVE_DEVICE_CLASSES, mode=selector.SelectSelectorMode.DROPDOWN)
            ),
            **self._device_assignment_schema(entity),
        }

        return self.async_show_form(
            step_id="reconfigure_valve",
            data_schema=self.add_suggested_values_to_schema(vol.Schema(schema_dict), entity),
            errors=errors,
        )

    async def async_step_reconfigure_select(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
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
                old_name = self._entity_data.get(CONF_NAME)
                new_name = user_input[CONF_NAME]
                if subentry.unique_id and self._should_update_legacy_device_name(user_input):
                    self._update_device_name_if_changed(subentry.unique_id, old_name, new_name)
                self._persist_reconfigured_entity(new_data, legacy_title=new_title)
                return self.async_abort(reason="reconfigure_successful")

        entity = self._entity_data
        options = entity.get("options", [])
        options_str = ", ".join(options) if isinstance(options, list) else (str(options) if options else "")

        return self.async_show_form(
            step_id="reconfigure_select",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema({
                    vol.Required(CONF_ADS_VAR): cv.string,
                    vol.Required(CONF_NAME): cv.string,
                    vol.Required("options"): cv.string,
                    **self._device_assignment_schema(entity),
                }),
                {**entity, "options": options_str},
            ),
            errors=errors,
        )

    # ── Entity Options ──────────────────────────────────────────────

    async def async_step_entity_options(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        if user_input is not None:
            new_data = dict(self._entity_data)
            self._remove_empty_optional_fields(user_input, CONF_ENTITY_ICON, CONF_ENTITY_CATEGORY, CONF_ENTITY_PICTURE)
            for key in [CONF_ENTITY_ICON, CONF_ENTITY_CATEGORY, CONF_ENTITY_PICTURE]:
                if key in user_input:
                    new_data[key] = user_input[key]
                elif key in new_data:
                    del new_data[key]
            self._persist_reconfigured_entity(new_data)
            return self.async_abort(reason="entity_options_updated")

        entity = dict(self._entity_data)

        schema_dict: dict[Any, Any] = {
            vol.Optional(CONF_ENTITY_ICON): selector.IconSelector(selector.IconSelectorConfig()),
            vol.Optional(CONF_ENTITY_CATEGORY): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["", "config", "diagnostic"],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(CONF_ENTITY_PICTURE): cv.string,
        }

        return self.async_show_form(
            step_id="entity_options",
            data_schema=self.add_suggested_values_to_schema(vol.Schema(schema_dict), entity),
        )


class AdsOptionsFlowHandler(OptionsFlow):
    """Handle hub-level device and entity management options."""

    _entity_data: dict[str, Any]

    _remove_empty_optional_fields = staticmethod(AdsEntitySubentryFlowHandler._remove_empty_optional_fields)
    _remove_cleared_optional_fields = staticmethod(AdsEntitySubentryFlowHandler._remove_cleared_optional_fields)
    _resolve_device_assignment = staticmethod(AdsEntitySubentryFlowHandler._resolve_device_assignment)
    _entity_title = staticmethod(AdsEntitySubentryFlowHandler._entity_title)
    _subentry_entities = AdsEntitySubentryFlowHandler._subentry_entities
    _subentry_device_id = AdsEntitySubentryFlowHandler._subentry_device_id
    _subentry_device_name = AdsEntitySubentryFlowHandler._subentry_device_name
    _resolve_registry_device_name = AdsEntitySubentryFlowHandler._resolve_registry_device_name
    _persist_reconfigured_entity = AdsEntitySubentryFlowHandler._persist_reconfigured_entity
    _get_device_assignment_options = AdsEntitySubentryFlowHandler._get_device_assignment_options
    _device_assignment_schema = AdsEntitySubentryFlowHandler._device_assignment_schema
    _update_device_name_if_changed = AdsEntitySubentryFlowHandler._update_device_name_if_changed

    async_step_reconfigure = AdsEntitySubentryFlowHandler.async_step_reconfigure
    async_step_reconfigure_switch = AdsEntitySubentryFlowHandler.async_step_reconfigure_switch
    async_step_reconfigure_sensor = AdsEntitySubentryFlowHandler.async_step_reconfigure_sensor
    async_step_reconfigure_binary_sensor = AdsEntitySubentryFlowHandler.async_step_reconfigure_binary_sensor
    async_step_reconfigure_light = AdsEntitySubentryFlowHandler.async_step_reconfigure_light
    async_step_reconfigure_cover = AdsEntitySubentryFlowHandler.async_step_reconfigure_cover
    async_step_reconfigure_valve = AdsEntitySubentryFlowHandler.async_step_reconfigure_valve
    async_step_reconfigure_select = AdsEntitySubentryFlowHandler.async_step_reconfigure_select

    def __init__(self) -> None:
        self._selected_device_id: str | None = None
        self._selected_subentry_id: str | None = None
        self._selected_entity_unique_id: str | None = None

    @property
    def entry(self) -> ConfigEntry:
        return self.config_entry

    def _get_reconfigure_subentry(self):
        if not self._selected_subentry_id:
            raise ValueError("No entity selected")
        subentry = self.config_entry.subentries.get(self._selected_subentry_id)
        if subentry is None:
            raise ValueError("Selected entity no longer exists")
        return subentry

    def _entity_subentries(self) -> list[tuple[str, Any]]:
        return [
            (subentry_id, subentry)
            for subentry_id, subentry in self.config_entry.subentries.items()
            if subentry.subentry_type == SUBENTRY_TYPE_ENTITY
        ]

    def _device_entities_map(self) -> dict[str, list[tuple[str, Any, dict[str, Any]]]]:
        device_map: dict[str, list[tuple[str, Any, dict[str, Any]]]] = {}
        for subentry_id, subentry, device_id, _, entity_data in iter_subentry_entities(self.config_entry):
            if subentry.subentry_type != SUBENTRY_TYPE_ENTITY:
                continue
            if not device_id:
                continue
            device_map.setdefault(device_id, []).append((subentry_id, subentry, entity_data))
        return device_map

    def _device_belongs_to_entry(self, device: Any) -> bool:
        """Return whether a device is linked to this config entry."""

        config_entries = getattr(device, "config_entries", set())
        if self.config_entry.entry_id in config_entries:
            return True

        subentry_map = getattr(device, "config_entries_subentries", None)
        if not isinstance(subentry_map, dict):
            return False

        return bool(subentry_map.get(self.config_entry.entry_id))

    def _get_registry_device_labels(self) -> dict[str, str]:
        labels: dict[str, str] = {}
        device_registry = dr.async_get(self.hass)
        for device in device_registry.devices.values():
            if not self._device_belongs_to_entry(device):
                continue
            for domain, identifier in device.identifiers:
                if domain != DOMAIN:
                    continue
                labels[identifier] = device.name_by_user or device.name or identifier
                break
        return labels

    def _get_device_selection_options(self) -> list[dict[str, str]]:
        device_map = self._device_entities_map()
        labels = self._get_registry_device_labels()
        all_device_ids = set(device_map).union(labels)
        options: list[dict[str, str]] = []
        for device_id in all_device_ids:
            label = labels.get(device_id)
            if not label:
                entities = device_map.get(device_id, [])
                if entities:
                    first_entity_data = entities[0][2]
                    label = (
                        first_entity_data.get(CONF_ENTITY_DEVICE_NAME)
                        or first_entity_data.get(CONF_NAME)
                        or device_id
                    )
                else:
                    label = device_id
            options.append({"label": label, "value": device_id})
        options.sort(key=lambda item: item["label"].lower())
        return options

    def _device_name_for_id(self, device_id: str) -> str:
        labels = self._get_registry_device_labels()
        if device_id in labels:
            return labels[device_id]
        entities = self._device_entities_map().get(device_id, [])
        if entities:
            first_entity_data = entities[0][2]
            return (
                first_entity_data.get(CONF_ENTITY_DEVICE_NAME)
                or first_entity_data.get(CONF_NAME)
                or DEFAULT_MIGRATED_DEVICE_NAME
            )
        return device_id

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
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
            data_schema=vol.Schema({
                vol.Required(CONF_SELECTED_DEVICE_ID, default=default_device): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=options, mode=selector.SelectSelectorMode.DROPDOWN)
                )
            }),
            errors=errors,
        )

    def _entity_select_options(self, device_id: str) -> list[dict[str, str]]:
        options: list[dict[str, str]] = [{"label": "(No entity selected)", "value": ""}]
        entities = self._device_entities_map().get(device_id, [])
        for subentry_id, _, entity_data in sorted(
            entities,
            key=lambda item: self._entity_title(item[2]).lower(),
        ):
            options.append({"label": self._entity_title(entity_data), "value": subentry_id})
        return options

    def _rename_device(self, device_id: str, new_name: str) -> None:
        device_registry = dr.async_get(self.hass)
        device = device_registry.async_get_device(identifiers={(DOMAIN, device_id)})
        if device:
            if device.name_by_user:
                device_registry.async_update_device(device.id, name_by_user=new_name)
            else:
                device_registry.async_update_device(device.id, name=new_name)

        for _, subentry, _ in self._device_entities_map().get(device_id, []):
            new_data = dict(subentry.data)
            new_data[CONF_ENTITY_DEVICE_NAME] = new_name
            entities = new_data.get(CONF_DEVICE_ENTITIES)
            if isinstance(entities, list):
                new_entities: list[dict[str, Any]] = []
                for entity in entities:
                    if not isinstance(entity, dict):
                        continue
                    updated_entity = dict(entity)
                    updated_entity[CONF_ENTITY_DEVICE_NAME] = new_name
                    new_entities.append(updated_entity)
                new_data[CONF_DEVICE_ENTITIES] = new_entities
            self.hass.config_entries.async_update_subentry(
                self.config_entry, subentry, data=MappingProxyType(new_data), title=new_name
            )

    def _move_entities_to_device(self, subentry_ids: list[str], device_id: str) -> int:
        device_name = self._device_name_for_id(device_id)
        moved_count = 0

        for subentry_id in subentry_ids:
            subentry = self.config_entry.subentries.get(subentry_id)
            if not subentry or subentry.subentry_type != SUBENTRY_TYPE_ENTITY:
                continue

            new_data = dict(subentry.data)
            new_data[CONF_ENTITY_DEVICE_ID] = device_id
            new_data[CONF_ENTITY_DEVICE_NAME] = device_name
            self.hass.config_entries.async_update_subentry(
                self.config_entry, subentry, data=MappingProxyType(new_data)
            )
            moved_count += 1

        return moved_count

    def _move_entity_options(self) -> list[dict[str, str]]:
        labels = self._get_registry_device_labels()
        options: list[dict[str, str]] = []

        for subentry_id, subentry in sorted(self._entity_subentries(), key=lambda item: item[1].title.lower()):
            device_id = subentry.data.get(CONF_ENTITY_DEVICE_ID) or subentry.unique_id
            device_name = (
                subentry.data.get(CONF_ENTITY_DEVICE_NAME)
                or labels.get(device_id)
                or device_id
            )
            options.append(
                {
                    "label": f"{subentry.title} [{device_name}]",
                    "value": subentry_id,
                }
            )

        return options

    def _delete_empty_device(self, device_id: str) -> None:
        device_registry = dr.async_get(self.hass)
        device = device_registry.async_get_device(identifiers={(DOMAIN, device_id)})
        if not device:
            return
        subentry_map = getattr(device, "config_entries_subentries", None)
        if isinstance(subentry_map, dict) and subentry_map.get(self.config_entry.entry_id):
            return

        config_entries = getattr(device, "config_entries", set())
        if self.config_entry.entry_id not in config_entries:
            return
        device_registry.async_update_device(
            device.id,
            remove_config_entry_id=self.config_entry.entry_id,
        )

    def _empty_device_ids(self) -> list[str]:
        device_map = self._device_entities_map()
        device_registry = dr.async_get(self.hass)
        empty_device_ids: list[str] = []

        for device in device_registry.devices.values():
            if not self._device_belongs_to_entry(device):
                continue

            for domain, identifier in device.identifiers:
                if domain != DOMAIN:
                    continue

                if identifier not in device_map:
                    empty_device_ids.append(identifier)
                break

        return empty_device_ids

    def _delete_empty_devices(self) -> int:
        deleted_count = 0
        device_registry = dr.async_get(self.hass)

        for device_id in self._empty_device_ids():
            device = device_registry.async_get_device(identifiers={(DOMAIN, device_id)})
            if not device:
                continue

            device_registry.async_update_device(
                device.id,
                remove_config_entry_id=self.config_entry.entry_id,
            )
            deleted_count += 1

        return deleted_count

    async def async_step_device_actions(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
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
            wants_delete_empty_devices = requested_action == OPTION_DELETE_EMPTY_DEVICES
            wants_move_entities = requested_action == OPTION_MOVE_ENTITIES

            if wants_delete_empty_devices:
                empty_device_ids = self._empty_device_ids()
                if not empty_device_ids:
                    errors["base"] = "no_empty_devices"
                elif not user_input.get(CONF_CONFIRM_DELETE):
                    errors[CONF_CONFIRM_DELETE] = "delete_confirmation_required"
                else:
                    self._delete_empty_devices()
                    return self.async_create_entry(title="", data={})
            elif wants_delete:
                if entities:
                    errors["base"] = "device_has_entities"
                elif not user_input.get(CONF_CONFIRM_DELETE):
                    errors[CONF_CONFIRM_DELETE] = "delete_confirmation_required"
                else:
                    self._delete_empty_device(self._selected_device_id)
                    return self.async_create_entry(title="", data={})
            elif wants_move_entities:
                return await self.async_step_move_entities()
            elif new_device_name and new_device_name != current_name:
                self._rename_device(self._selected_device_id, new_device_name)
                return self.async_create_entry(title="", data={})
            else:
                errors["base"] = "no_action_selected"

        return self.async_show_form(
            step_id="device_actions",
            data_schema=vol.Schema({
                vol.Optional(CONF_SELECTED_ENTITY_SUBENTRY_ID, default=""): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=entity_options, mode=selector.SelectSelectorMode.DROPDOWN)
                ),
                vol.Optional(CONF_ENTITY_DEVICE_NAME, default=current_name): cv.string,
                vol.Optional(CONF_DEVICE_ACTION, default=""): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"label": "(None)", "value": ""},
                            {"label": "Move entities to this device", "value": OPTION_MOVE_ENTITIES},
                            {"label": "Delete device", "value": OPTION_DELETE_DEVICE},
                            {"label": "Delete all empty devices", "value": OPTION_DELETE_EMPTY_DEVICES},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_CONFIRM_DELETE, default=False): cv.boolean,
            }),
            errors=errors,
        )

    async def async_step_move_entities(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if not self._selected_device_id:
            return await self.async_step_init()

        errors: dict[str, str] = {}
        entity_options = self._move_entity_options()

        if user_input is not None:
            selected_subentry_ids = user_input.get(CONF_SELECTED_ENTITY_SUBENTRY_ID, [])
            if isinstance(selected_subentry_ids, str):
                selected_subentry_ids = [selected_subentry_ids] if selected_subentry_ids else []

            if not selected_subentry_ids:
                errors["base"] = "no_entities_selected"
            else:
                self._move_entities_to_device(selected_subentry_ids, self._selected_device_id)
                return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="move_entities",
            data_schema=vol.Schema({
                vol.Optional(CONF_SELECTED_ENTITY_SUBENTRY_ID, default=[]): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=entity_options,
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
            errors=errors,
        )
