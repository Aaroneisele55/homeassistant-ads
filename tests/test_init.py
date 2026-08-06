"""Tests for the ADS Custom __init__ module helpers."""

from __future__ import annotations

import ctypes
from unittest.mock import MagicMock

import pytest
import voluptuous as vol

from custom_components.ads_custom.const import (
    CONF_ADS_VAR,
    CONF_ENTITY_DEVICE_ID,
    CONF_ENTITY_DEVICE_NAME,
    DOMAIN,
    SUBENTRY_TYPE_ENTITY,
    AdsType,
)


class TestCollectYamlEntities:
    """Tests for the _collect_yaml_entities helper."""

    def _collect(self, config):
        """Import and call _collect_yaml_entities."""
        from custom_components.ads_custom import _collect_yaml_entities

        return _collect_yaml_entities(config)

    def test_empty_config(self):
        """No platform sections yields no entities."""
        assert self._collect({}) == []

    def test_single_sensor(self):
        """A single sensor platform entry is collected."""
        config = {
            "sensor": [
                {
                    "platform": DOMAIN,
                    CONF_ADS_VAR: "GVL.temperature",
                    "adstype": "int",
                    "name": "Temperature",
                    "unique_id": "temp_1",
                }
            ]
        }
        entities = self._collect(config)
        assert len(entities) == 1
        ent = entities[0]
        assert ent["entity_type"] == "sensor"
        assert ent[CONF_ADS_VAR] == "GVL.temperature"
        assert ent["name"] == "Temperature"
        assert ent["unique_id"] == "temp_1"

    def test_multiple_platforms(self):
        """Entities are collected from multiple platform sections."""
        config = {
            "sensor": [{"platform": DOMAIN, CONF_ADS_VAR: "GVL.s1", "name": "S1", "unique_id": "s1"}],
            "binary_sensor": [{"platform": DOMAIN, CONF_ADS_VAR: "GVL.bs1", "name": "BS1", "unique_id": "bs1"}],
            "switch": [{"platform": DOMAIN, CONF_ADS_VAR: "GVL.sw1", "name": "SW1", "unique_id": "sw1"}],
        }
        entities = self._collect(config)
        types = {e["entity_type"] for e in entities}
        assert types == {"sensor", "binary_sensor", "switch"}

    def test_ignores_other_platforms(self):
        """Entries not matching domain are skipped."""
        config = {
            "sensor": [
                {"platform": "other_integration", CONF_ADS_VAR: "x"},
                {"platform": DOMAIN, CONF_ADS_VAR: "GVL.ok", "name": "OK", "unique_id": "ok"},
            ]
        }
        entities = self._collect(config)
        assert len(entities) == 1

    def test_auto_generates_unique_id(self):
        """Entities without unique_id get one generated."""
        config = {
            "switch": [{"platform": DOMAIN, CONF_ADS_VAR: "GVL.sw", "name": "SW"}]
        }
        entities = self._collect(config)
        assert len(entities) == 1
        assert "unique_id" in entities[0]
        assert len(entities[0]["unique_id"]) == 32  # uuid4 hex

    def test_enum_value_converted_to_string(self):
        """AdsType enum values should be serialized as strings."""
        config = {
            "sensor": [
                {
                    "platform": DOMAIN,
                    CONF_ADS_VAR: "GVL.v",
                    "adstype": AdsType.LREAL,
                    "name": "V",
                    "unique_id": "v1",
                }
            ]
        }
        entities = self._collect(config)
        assert entities[0]["adstype"] == "lreal"

    def test_non_list_platform_config(self):
        """A single dict (not wrapped in list) should still work."""
        config = {
            "switch": {"platform": DOMAIN, CONF_ADS_VAR: "GVL.sw", "name": "SW", "unique_id": "sw1"},
        }
        entities = self._collect(config)
        assert len(entities) == 1


class TestAdsTypemap:
    """Tests for the ADS_TYPEMAP mapping."""

    def test_all_ads_types_mapped(self):
        """Every AdsType member must have a mapping to a pyads PLC type."""
        from custom_components.ads_custom import ADS_TYPEMAP

        for ads_type in AdsType:
            assert ads_type in ADS_TYPEMAP, f"ADS_TYPEMAP missing {ads_type}"

    def test_typemap_values_are_ctypes(self):
        """Each mapped value should be a ctypes type (pyads PLC type)."""
        from custom_components.ads_custom import ADS_TYPEMAP

        for ads_type, plc_type in ADS_TYPEMAP.items():
            assert isinstance(plc_type, type) and (
                issubclass(plc_type, ctypes.Structure)
                or issubclass(type(plc_type), type(ctypes.c_int))
            ), f"ADS_TYPEMAP[{ads_type}] = {plc_type} is not a valid ctypes type"


class TestConfigSchema:
    """Tests for the YAML CONFIG_SCHEMA."""

    def test_valid_minimal_config(self):
        """Minimal valid configuration should pass validation."""
        from custom_components.ads_custom import CONFIG_SCHEMA

        config = {DOMAIN: {"device": "5.23.48.159.1.1"}}
        result = CONFIG_SCHEMA(config)
        assert result[DOMAIN]["device"] == "5.23.48.159.1.1"
        assert result[DOMAIN]["port"] == 48898  # default

    def test_valid_full_config(self):
        """Full configuration with all optional fields."""
        from custom_components.ads_custom import CONFIG_SCHEMA

        config = {
            DOMAIN: {
                "device": "5.23.48.159.1.1",
                "ip_address": "192.168.1.100",
                "port": 851,
            }
        }
        result = CONFIG_SCHEMA(config)
        assert result[DOMAIN]["ip_address"] == "192.168.1.100"
        assert result[DOMAIN]["port"] == 851

    def test_missing_device_raises(self):
        """Configuration without required 'device' key should fail."""
        from custom_components.ads_custom import CONFIG_SCHEMA

        with pytest.raises(vol.MultipleInvalid):
            CONFIG_SCHEMA({DOMAIN: {}})


class TestServiceSchema:
    """Tests for the write_data_by_name service schema."""

    def test_valid_service_call(self):
        """Valid service data should pass validation."""
        from custom_components.ads_custom import SCHEMA_SERVICE_WRITE_DATA_BY_NAME

        data = {
            "adstype": "int",
            "value": 42,
            "adsvar": "GVL.setpoint",
        }
        result = SCHEMA_SERVICE_WRITE_DATA_BY_NAME(data)
        assert result["adstype"] == AdsType.INT
        assert result["value"] == 42
        assert result["adsvar"] == "GVL.setpoint"

    def test_missing_adsvar_raises(self):
        """Missing adsvar should raise validation error."""
        from custom_components.ads_custom import SCHEMA_SERVICE_WRITE_DATA_BY_NAME

        with pytest.raises(vol.MultipleInvalid):
            SCHEMA_SERVICE_WRITE_DATA_BY_NAME({"adstype": "int", "value": 1})

    def test_invalid_adstype_raises(self):
        """Unknown adstype should raise validation error."""
        from custom_components.ads_custom import SCHEMA_SERVICE_WRITE_DATA_BY_NAME

        with pytest.raises(vol.MultipleInvalid):
            SCHEMA_SERVICE_WRITE_DATA_BY_NAME(
                {"adstype": "nonexistent", "value": 1, "adsvar": "x"}
            )


class TestLegacyDefaultDeviceMigration:
    """Tests for legacy entity default-device migration."""

    @pytest.mark.asyncio
    async def test_unassigned_entities_are_grouped_under_one_default_device(self):
        """Entities without entity_device_id should get shared default device assignment."""
        from custom_components.ads_custom import (
            _async_migrate_legacy_unassigned_entities_to_default_device,
        )

        subentry_unassigned = MagicMock()
        subentry_unassigned.subentry_type = SUBENTRY_TYPE_ENTITY
        subentry_unassigned.data = {"name": "Legacy Entity"}

        subentry_assigned = MagicMock()
        subentry_assigned.subentry_type = SUBENTRY_TYPE_ENTITY
        subentry_assigned.data = {CONF_ENTITY_DEVICE_ID: "existing-device"}

        hub_entry = MagicMock()
        hub_entry.entry_id = "hub-entry-id"
        hub_entry.title = "ADS (Hub)"
        hub_entry.data = {}
        hub_entry.subentries = {
            "legacy-subentry": subentry_unassigned,
            "assigned-subentry": subentry_assigned,
        }

        hass = MagicMock()
        hass.config_entries.async_entries.return_value = [hub_entry]

        await _async_migrate_legacy_unassigned_entities_to_default_device(hass)

        hass.config_entries.async_update_subentry.assert_called_once()
        _, updated_subentry = hass.config_entries.async_update_subentry.call_args.args[:2]
        updated_data = hass.config_entries.async_update_subentry.call_args.kwargs["data"]

        assert updated_subentry is subentry_unassigned
        assert (
            updated_data[CONF_ENTITY_DEVICE_ID]
            == "hub-entry-id-default-device"
        )
        assert updated_data[CONF_ENTITY_DEVICE_NAME] == "Default ADS Device"


class Test20268DeviceMigration:
    """Tests for the 2026.8 single-config-entry device migration."""

    @pytest.mark.asyncio
    async def test_grouped_subentry_entities_keep_their_shared_device(self, monkeypatch):
        """Grouped device subentries should migrate each nested entity without flattening the list."""
        from custom_components.ads_custom import _async_migrate_entity_config_entries_for_hub
        import custom_components.ads_custom as ads_init

        grouped_entity = {
            "entity_type": "sensor",
            "name": "Temperature",
            "unique_id": "temperature-entity",
            CONF_ADS_VAR: "GVL.temperature",
        }

        subentry = MagicMock()
        subentry.subentry_type = SUBENTRY_TYPE_ENTITY
        subentry.unique_id = "shared-device-id"
        subentry.title = "Shared Device"
        subentry.data = {
            CONF_ENTITY_DEVICE_ID: "shared-device-id",
            CONF_ENTITY_DEVICE_NAME: "Shared Device",
            "entities": [grouped_entity],
        }

        hub_entry = MagicMock()
        hub_entry.entry_id = "hub-entry-id"
        hub_entry.title = "ADS Hub"
        hub_entry.subentries = {"subentry-id": subentry}

        entity_registry = MagicMock()
        entity_registry.async_get_entity_id.return_value = "sensor.temperature"
        entity_registry.entities = {
            "sensor.temperature": MagicMock(
                entity_id="sensor.temperature",
                config_entry_id="other-entry",
                config_subentry_id="other-subentry",
            )
        }

        device = MagicMock()
        device.name = "Shared Device"

        device_registry = MagicMock()
        device_registry.async_get_device_by_identifier.return_value = device

        hass = MagicMock()
        hass.config_entries.async_update_subentry = MagicMock()

        monkeypatch.setattr(ads_init, "er", MagicMock(async_get=MagicMock(return_value=entity_registry)))
        monkeypatch.setattr(ads_init, "dr", MagicMock(async_get=MagicMock(return_value=device_registry)))
        monkeypatch.setattr(ads_init, "async_ensure_device_subentry", MagicMock())

        await _async_migrate_entity_config_entries_for_hub(hass, hub_entry)

        hass.config_entries.async_update_subentry.assert_not_called()
        entity_registry.async_update_entity.assert_called_once_with(
            "sensor.temperature",
            config_entry_id="hub-entry-id",
            config_subentry_id="subentry-id",
        )

    @pytest.mark.asyncio
    async def test_existing_entity_device_ids_are_rewritten_to_subentry_ids(self, monkeypatch):
        """Legacy flat subentries should be normalized into grouped entity lists."""
        from custom_components.ads_custom import _async_migrate_entity_config_entries_for_hub
        import custom_components.ads_custom.device_registry_compat as compat

        subentry = MagicMock()
        subentry.subentry_type = SUBENTRY_TYPE_ENTITY
        subentry.unique_id = "subentry-unique-id"
        subentry.title = "Legacy Entity"
        subentry.data = {
            CONF_ENTITY_DEVICE_ID: "shared-device-id",
            "name": "Legacy Entity",
        }

        hub_entry = MagicMock()
        hub_entry.entry_id = "hub-entry-id"
        hub_entry.title = "ADS Hub"
        hub_entry.subentries = {"subentry-id": subentry}

        entity_registry = MagicMock()
        entity_registry.async_get_entity_id.return_value = None

        device = MagicMock()
        device.name = "Legacy Entity"

        device_registry = MagicMock()
        device_registry.async_get_device_by_identifier.return_value = device

        monkeypatch.setattr(compat, "SINGLE_CONFIG_ENTRY_DEVICES", True)

        hass = MagicMock()
        hass.config_entries.async_update_subentry = MagicMock()

        import custom_components.ads_custom as ads_init

        ads_init.er.async_get = MagicMock(return_value=entity_registry)
        ads_init.dr.async_get = MagicMock(return_value=device_registry)

        await _async_migrate_entity_config_entries_for_hub(hass, hub_entry)

        device_registry.async_get_device_by_identifier.assert_called_once_with(
            (DOMAIN, "shared-device-id"), "hub-entry-id"
        )
        hass.config_entries.async_update_subentry.assert_called_once()
        updated_data = hass.config_entries.async_update_subentry.call_args.kwargs["data"]
        assert updated_data[CONF_ENTITY_DEVICE_ID] == "shared-device-id"
        assert updated_data[CONF_ENTITY_DEVICE_NAME] == "Legacy Entity"
        assert updated_data["entities"][0]["name"] == "Legacy Entity"
