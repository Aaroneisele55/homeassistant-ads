"""Entity options flow for ADS Custom entities."""

from __future__ import annotations
from typing import Any
from homeassistant.helpers.entity import EntityOptionsFlow
from homeassistant.helpers import selector
import voluptuous as vol

from .const import CONF_ENTITY_ICON, CONF_ENTITY_CATEGORY, CONF_ENTITY_PICTURE

class AdsEntityOptionsFlowHandler(EntityOptionsFlow):
    """Handle entity options flow for ADS entities."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        errors = {}
        entity = self.entity
        options = self.options or {}
        entity_type = getattr(entity, 'platform', None) or getattr(entity, 'entity_type', None) or entity.__class__.__name__.lower()

        # Helper to get default from options, then entity, then fallback
        def get_default(key, fallback=None):
            return options.get(key, getattr(entity, key, fallback))

        # Common fields for all entities
        schema_dict = {
            vol.Optional(
                CONF_ENTITY_ICON, default=get_default(CONF_ENTITY_ICON)
            ): selector.IconSelector(selector.IconSelectorConfig()),
            vol.Optional(
                CONF_ENTITY_CATEGORY, default=get_default(CONF_ENTITY_CATEGORY)
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["", "config", "diagnostic"],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(
                CONF_ENTITY_PICTURE, default=get_default(CONF_ENTITY_PICTURE)
            ): str,
        }

        # Entity-type-specific fields
        if entity_type == "sensor":
            from .const import CONF_ADS_VAR, AdsType
            from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
            from homeassistant.const import CONF_DEVICE_CLASS, CONF_UNIT_OF_MEASUREMENT
            schema_dict.update({
                vol.Required(
                    CONF_ADS_VAR, default=get_default(CONF_ADS_VAR, "")
                ): str,
                vol.Optional(
                    "ads_type", default=get_default("ads_type", AdsType.INT)
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[t.value for t in AdsType],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_DEVICE_CLASS, default=get_default(CONF_DEVICE_CLASS)
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["", "apparent_power", "aqi", "atmospheric_pressure", "battery", "carbon_dioxide", "carbon_monoxide", "current", "data_rate", "data_size", "date", "distance", "duration", "energy", "energy_storage", "enum", "frequency", "gas", "humidity", "illuminance", "irradiance", "moisture", "monetary", "nitrogen_dioxide", "nitrogen_monoxide", "nitrous_oxide", "ozone", "ph", "pm1", "pm10", "pm25", "power", "power_factor", "precipitation", "precipitation_intensity", "pressure", "reactive_power", "signal_strength", "sound_pressure", "speed", "sulphur_dioxide", "temperature", "timestamp", "volatile_organic_compounds", "volatile_organic_compounds_parts", "voltage", "volume", "volume_flow_rate", "volume_storage", "water", "weight", "wind_speed"],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    "state_class", default=get_default("state_class")
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["", "measurement", "total", "total_increasing"],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_UNIT_OF_MEASUREMENT, default=get_default(CONF_UNIT_OF_MEASUREMENT)
                ): str,
            })
        elif entity_type == "binary_sensor":
            from .const import CONF_ADS_VAR, AdsType
            from homeassistant.components.binary_sensor import BinarySensorDeviceClass
            from homeassistant.const import CONF_DEVICE_CLASS
            schema_dict.update({
                vol.Required(
                    CONF_ADS_VAR, default=get_default(CONF_ADS_VAR, "")
                ): str,
                vol.Optional(
                    "ads_type", default=get_default("ads_type", AdsType.BOOL)
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[AdsType.BOOL, AdsType.REAL],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_DEVICE_CLASS, default=get_default(CONF_DEVICE_CLASS)
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["", "battery", "battery_charging", "carbon_monoxide", "cold", "connectivity", "door", "garage_door", "gas", "heat", "light", "lock", "moisture", "motion", "moving", "occupancy", "opening", "plug", "power", "presence", "problem", "running", "safety", "smoke", "sound", "tamper", "update", "vibration", "window"],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            })
        elif entity_type == "switch":
            from .const import CONF_ADS_VAR
            schema_dict.update({
                vol.Required(
                    CONF_ADS_VAR, default=get_default(CONF_ADS_VAR, "")
                ): str,
            })
        elif entity_type == "light":
            from .const import CONF_ADS_VAR
            schema_dict.update({
                vol.Required(
                    CONF_ADS_VAR, default=get_default(CONF_ADS_VAR, "")
                ): str,
                vol.Optional(
                    "adsvar_brightness", default=get_default("adsvar_brightness")
                ): str,
                vol.Optional(
                    "adsvar_brightness_scale", default=get_default("adsvar_brightness_scale", 255)
                ): int,
                vol.Optional(
                    "adsvar_brightness_type", default=get_default("adsvar_brightness_type", "byte")
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["byte", "uint"],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            })
        elif entity_type == "cover":
            from .const import CONF_ADS_VAR
            schema_dict.update({
                vol.Optional("adsvar", default=get_default("adsvar")): str,
                vol.Optional("adsvar_position", default=get_default("adsvar_position")): str,
                vol.Optional("adsvar_position_type", default=get_default("adsvar_position_type", "byte")):
                    selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=["byte", "uint"],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                vol.Optional("adsvar_set_position", default=get_default("adsvar_set_position")): str,
                vol.Optional("adsvar_open", default=get_default("adsvar_open")): str,
                vol.Optional("adsvar_close", default=get_default("adsvar_close")): str,
                vol.Optional("adsvar_stop", default=get_default("adsvar_stop")): str,
                vol.Optional("inverted", default=get_default("inverted", False)): bool,
            })
        elif entity_type == "valve":
            from .const import CONF_ADS_VAR
            from homeassistant.components.valve import ValveDeviceClass
            from homeassistant.const import CONF_DEVICE_CLASS
            schema_dict.update({
                vol.Required(CONF_ADS_VAR, default=get_default(CONF_ADS_VAR, "")): str,
                vol.Optional(CONF_DEVICE_CLASS, default=get_default(CONF_DEVICE_CLASS)): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["", "gas", "water"],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            })
        elif entity_type == "select":
            from .const import CONF_ADS_VAR
            schema_dict.update({
                vol.Required(CONF_ADS_VAR, default=get_default(CONF_ADS_VAR, "")): str,
                vol.Required("options", default=get_default("options", [])): str,
            })

        if user_input is not None:
            # Remove empty optional fields
            for key in list(schema_dict.keys()):
                if key in user_input and (user_input[key] is None or user_input[key] == ""):
                    user_input.pop(key)
            return self.async_create_entry(title=entity.name or entity.entity_id, data=user_input)

        schema = vol.Schema(schema_dict)
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
