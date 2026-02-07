"""Config flow for ADS Custom integration."""

from __future__ import annotations

import logging
from typing import Any

import pyads
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE, CONF_IP_ADDRESS, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

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


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ADS Custom."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
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
