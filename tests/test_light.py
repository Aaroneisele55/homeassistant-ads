"""Tests for the ADS Light platform brightness scaling logic."""

from __future__ import annotations

from unittest.mock import MagicMock, call

import pyads

from custom_components.ads_custom.light import AdsLight


def _make_light(
    brightness_var: str | None = None,
    brightness_scale: int = 255,
    brightness_type: str = "byte",
) -> tuple[AdsLight, MagicMock]:
    """Create an AdsLight with a mock hub, returning (light, hub_mock)."""
    hub = MagicMock()
    light = AdsLight(
        ads_hub=hub,
        ads_var_enable="GVL.light_on",
        ads_var_brightness=brightness_var,
        brightness_scale=brightness_scale,
        brightness_type=brightness_type,
        name="Test Light",
        unique_id="test_light_1",
    )
    return light, hub


class TestAdsLightTurnOn:
    """Tests for AdsLight.turn_on brightness scaling."""

    def test_turn_on_no_brightness_var(self):
        """turn_on without brightness var should only write the enable flag."""
        light, hub = _make_light(brightness_var=None)
        light.turn_on()
        hub.write_by_name.assert_called_once_with(
            "GVL.light_on", True, pyads.PLCTYPE_BOOL
        )

    def test_turn_on_with_brightness_default_scale(self):
        """turn_on with brightness=128, scale=255 should write 128."""
        light, hub = _make_light(
            brightness_var="GVL.brightness", brightness_scale=255
        )
        light.turn_on(brightness=128)

        assert hub.write_by_name.call_count == 2
        hub.write_by_name.assert_any_call(
            "GVL.light_on", True, pyads.PLCTYPE_BOOL
        )
        hub.write_by_name.assert_any_call(
            "GVL.brightness", 128, pyads.PLCTYPE_BYTE
        )

    def test_turn_on_with_brightness_scale_100(self):
        """turn_on with brightness=255, scale=100 should write 100."""
        light, hub = _make_light(
            brightness_var="GVL.brightness", brightness_scale=100
        )
        light.turn_on(brightness=255)

        hub.write_by_name.assert_any_call(
            "GVL.brightness", 100, pyads.PLCTYPE_BYTE
        )

    def test_turn_on_with_brightness_scale_100_half(self):
        """turn_on with brightness=127, scale=100 should write ~49."""
        light, hub = _make_light(
            brightness_var="GVL.brightness", brightness_scale=100
        )
        light.turn_on(brightness=127)

        # int(127 * 100 / 255) = 49
        hub.write_by_name.assert_any_call(
            "GVL.brightness", 49, pyads.PLCTYPE_BYTE
        )

    def test_turn_on_uses_uint_plctype(self):
        """When brightness_type is 'uint', PLCTYPE_UINT should be used."""
        light, hub = _make_light(
            brightness_var="GVL.brightness",
            brightness_type="uint",
        )
        light.turn_on(brightness=200)

        hub.write_by_name.assert_any_call(
            "GVL.brightness", 200, pyads.PLCTYPE_UINT
        )

    def test_turn_on_without_brightness_kwarg(self):
        """turn_on without brightness kwarg should only write enable."""
        light, hub = _make_light(brightness_var="GVL.brightness")
        light.turn_on()

        hub.write_by_name.assert_called_once_with(
            "GVL.light_on", True, pyads.PLCTYPE_BOOL
        )


class TestAdsLightTurnOff:
    """Tests for AdsLight.turn_off."""

    def test_turn_off_writes_false(self):
        """turn_off should write False to the enable variable."""
        light, hub = _make_light()
        light.turn_off()
        hub.write_by_name.assert_called_once_with(
            "GVL.light_on", False, pyads.PLCTYPE_BOOL
        )


class TestAdsLightProperties:
    """Tests for AdsLight state properties."""

    def test_is_on_none_initially(self):
        """is_on should be None before any state update."""
        light, _ = _make_light()
        assert light.is_on is None

    def test_brightness_none_initially(self):
        """brightness should be None before any state update."""
        light, _ = _make_light(brightness_var="GVL.brightness")
        assert light.brightness is None

    def test_color_mode_brightness(self):
        """When brightness var is set, color_mode should be BRIGHTNESS."""
        from homeassistant.components.light import ColorMode

        light, _ = _make_light(brightness_var="GVL.brightness")
        assert light.color_mode == ColorMode.BRIGHTNESS

    def test_color_mode_onoff(self):
        """Without brightness var, color_mode should be ONOFF."""
        from homeassistant.components.light import ColorMode

        light, _ = _make_light(brightness_var=None)
        assert light.color_mode == ColorMode.ONOFF
