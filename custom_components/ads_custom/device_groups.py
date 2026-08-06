"""Helpers for device-centric ADS subentries."""

from __future__ import annotations

from typing import Any, Iterable

from homeassistant.const import CONF_NAME

from .const import CONF_ENTITY_DEVICE_ID, CONF_ENTITY_DEVICE_NAME

_DEVICE_RESERVED_KEYS = {CONF_ENTITY_DEVICE_ID, CONF_ENTITY_DEVICE_NAME, "entities"}


def get_device_name(data: dict[str, Any], fallback: str | None = None) -> str | None:
    """Return the device name stored on a device subentry."""
    return data.get(CONF_ENTITY_DEVICE_NAME) or data.get(CONF_NAME) or fallback


def get_device_id(data: dict[str, Any], fallback: str | None = None) -> str | None:
    """Return the device ID stored on a device subentry."""
    return data.get(CONF_ENTITY_DEVICE_ID) or fallback


def iter_entity_configs(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return entity configs stored in a device subentry.

    New-format subentries store a list under ``entities``. Legacy subentries
    stored a single entity config directly on the subentry. This helper
    normalizes both forms to a list of dicts.
    """
    entities = data.get("entities")
    if isinstance(entities, list):
        return [entity for entity in entities if isinstance(entity, dict)]
    return [{key: value for key, value in data.items() if key not in _DEVICE_RESERVED_KEYS}]


def with_entity_configs(
    data: dict[str, Any],
    entities: Iterable[dict[str, Any]],
    *,
    device_id: str | None = None,
    device_name: str | None = None,
) -> dict[str, Any]:
    """Return a copy of data updated with a normalized entity list."""
    new_data = dict(data)
    new_data["entities"] = list(entities)
    if device_id is not None:
        new_data[CONF_ENTITY_DEVICE_ID] = device_id
    if device_name is not None:
        new_data[CONF_ENTITY_DEVICE_NAME] = device_name
    return new_data
