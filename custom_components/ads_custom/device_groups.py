"""Helpers for device-centric ADS subentries."""

from __future__ import annotations

from typing import Any, Iterable, TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.const import CONF_NAME, CONF_UNIQUE_ID
from types import MappingProxyType

from .const import (
    CONF_ENTITY_DEVICE_ID,
    CONF_ENTITY_DEVICE_NAME,
    SINGLE_SUBENTRY_TITLE,
    SINGLE_SUBENTRY_UNIQUE_ID,
    SUBENTRY_TYPE_ENTITY,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

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


def get_single_entities_subentry(entry: ConfigEntry) -> ConfigSubentry | None:
    """Return the single subentry holding all entities for this hub, if any."""
    for subentry in entry.subentries.values():
        if subentry.subentry_type != SUBENTRY_TYPE_ENTITY:
            continue
        if subentry.unique_id == SINGLE_SUBENTRY_UNIQUE_ID:
            return subentry
    return None


def async_get_or_create_single_entities_subentry(
    hass: "HomeAssistant", entry: ConfigEntry
) -> ConfigSubentry:
    """Return the single entities subentry for a hub, creating it if needed."""
    subentry = get_single_entities_subentry(entry)
    if subentry is not None:
        return subentry

    subentry = ConfigSubentry(
        data=MappingProxyType({"entities": []}),
        subentry_type=SUBENTRY_TYPE_ENTITY,
        title=SINGLE_SUBENTRY_TITLE,
        unique_id=SINGLE_SUBENTRY_UNIQUE_ID,
    )
    hass.config_entries.async_add_subentry(entry, subentry)
    return get_single_entities_subentry(entry) or subentry


def async_add_entity_to_single_subentry(
    hass: "HomeAssistant",
    entry: ConfigEntry,
    entity_data: dict[str, Any],
) -> None:
    """Append an entity config to the hub's single entities subentry."""
    subentry = async_get_or_create_single_entities_subentry(hass, entry)
    entities = iter_entity_configs(dict(subentry.data))
    entities.append(entity_data)
    new_data = with_entity_configs(dict(subentry.data), entities)
    hass.config_entries.async_update_subentry(
        entry, subentry, data=MappingProxyType(new_data)
    )


def async_replace_entity_in_single_subentry(
    hass: "HomeAssistant",
    entry: ConfigEntry,
    unique_id: str,
    new_entity_data: dict[str, Any],
) -> bool:
    """Replace an existing entity (by unique_id) in the single subentry."""
    subentry = get_single_entities_subentry(entry)
    if subentry is None:
        return False

    entities = iter_entity_configs(dict(subentry.data))
    for index, entity in enumerate(entities):
        if (entity.get(CONF_UNIQUE_ID) or entity.get("unique_id")) == unique_id:
            entities[index] = new_entity_data
            new_data = with_entity_configs(dict(subentry.data), entities)
            hass.config_entries.async_update_subentry(
                entry, subentry, data=MappingProxyType(new_data)
            )
            return True
    return False


def async_remove_entity_from_single_subentry(
    hass: "HomeAssistant", entry: ConfigEntry, unique_id: str
) -> bool:
    """Remove an entity (by unique_id) from the single subentry."""
    subentry = get_single_entities_subentry(entry)
    if subentry is None:
        return False

    entities = iter_entity_configs(dict(subentry.data))
    filtered = [
        entity
        for entity in entities
        if (entity.get(CONF_UNIQUE_ID) or entity.get("unique_id")) != unique_id
    ]
    if len(filtered) == len(entities):
        return False

    new_data = with_entity_configs(dict(subentry.data), filtered)
    hass.config_entries.async_update_subentry(
        entry, subentry, data=MappingProxyType(new_data)
    )
    return True
