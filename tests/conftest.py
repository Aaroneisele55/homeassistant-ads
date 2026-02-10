"""Shared fixtures for ADS Custom integration tests."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Patch missing Home Assistant APIs that are unavailable in older HA versions.
# ConfigSubentry was added in a later HA release; this shim allows tests to
# run against the version of HA installable on Python 3.12.
# This must happen before any custom_components imports.
# ---------------------------------------------------------------------------
import homeassistant.config_entries as _ce

if not hasattr(_ce, "ConfigSubentry"):

    class _ConfigSubentry:  # noqa: D101
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    _ce.ConfigSubentry = _ConfigSubentry  # type: ignore[attr-defined]

# ---------------------------------------------------------------------------

from unittest.mock import MagicMock

import pyads
import pytest


@pytest.fixture
def mock_ads_client():
    """Return a mock pyads Connection that does not open a real connection."""
    client = MagicMock(spec=pyads.Connection)
    # add_device_notification returns (handle, user_handle)
    client.add_device_notification.return_value = (1, 1)
    return client


@pytest.fixture
def ads_hub(mock_ads_client):
    """Return an AdsHub wired to the mock client."""
    from custom_components.ads_custom.hub import AdsHub

    hub = AdsHub(mock_ads_client)
    return hub
