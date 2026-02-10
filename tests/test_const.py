"""Tests for the ADS Custom constants module."""

from __future__ import annotations

from custom_components.ads_custom.const import (
    CONF_ADS_VAR,
    DOMAIN,
    STATE_KEY_STATE,
    SUBENTRY_TYPE_ENTITY,
    AdsType,
)


class TestAdsType:
    """Tests for the AdsType enum."""

    def test_all_expected_types_exist(self):
        """Verify every documented PLC type is present."""
        expected = [
            "BOOL", "BYTE", "INT", "UINT", "SINT", "USINT",
            "DINT", "UDINT", "WORD", "DWORD", "LREAL", "REAL",
            "STRING", "TIME", "DATE", "DATE_AND_TIME", "TOD",
        ]
        for name in expected:
            assert hasattr(AdsType, name), f"AdsType.{name} is missing"

    def test_enum_values_are_lowercase_strings(self):
        """Each AdsType value should be a lowercase string usable in YAML."""
        for member in AdsType:
            assert isinstance(member.value, str)
            assert member.value == member.value.lower()

    def test_enum_count(self):
        """Guard against accidentally removing a type."""
        assert len(AdsType) == 17

    def test_ads_type_is_str_enum(self):
        """AdsType members should be usable as plain strings."""
        assert str(AdsType.BOOL) == "bool"
        assert f"{AdsType.INT}" == "int"


class TestConstants:
    """Tests for module-level constants."""

    def test_domain(self):
        """Domain must match manifest."""
        assert DOMAIN == "ads_custom"

    def test_conf_ads_var(self):
        assert CONF_ADS_VAR == "adsvar"

    def test_state_key_state(self):
        assert STATE_KEY_STATE == "state"

    def test_subentry_type_entity(self):
        assert SUBENTRY_TYPE_ENTITY == "entity"
