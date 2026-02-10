"""Tests for the ADS Custom __init__ module helpers."""

from __future__ import annotations

import ctypes

import pytest
import voluptuous as vol

from custom_components.ads_custom.const import CONF_ADS_VAR, DOMAIN, AdsType


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
