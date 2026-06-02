"""Helpers for working with ADS subentry data models."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from homeassistant.config_entries import ConfigEntry

from .const import CONF_DEVICE_ENTITIES, CONF_ENTITY_DEVICE_ID, CONF_ENTITY_DEVICE_NAME


def _device_id_for_subentry(subentry: Any) -> str | None:
    """Resolve the represented device id for a subentry."""

    return subentry.data.get(CONF_ENTITY_DEVICE_ID) or subentry.unique_id


def _device_name_for_subentry(subentry: Any, fallback: str | None = None) -> str | None:
    """Resolve the represented device name for a subentry."""

    return subentry.data.get(CONF_ENTITY_DEVICE_NAME) or subentry.title or fallback


def iter_subentry_entities(entry: ConfigEntry) -> Iterable[tuple[str, Any, str | None, str | None, dict[str, Any]]]:
    """Yield normalized entity data for both legacy and device-grouped subentries."""

    for subentry_id, subentry in entry.subentries.items():
        data = subentry.data
        device_id = _device_id_for_subentry(subentry)
        device_name = _device_name_for_subentry(subentry)

        entities = data.get(CONF_DEVICE_ENTITIES)
        if isinstance(entities, list):
            for entity_data in entities:
                if not isinstance(entity_data, dict):
                    continue
                entity_copy = dict(entity_data)
                entity_copy.setdefault(CONF_ENTITY_DEVICE_ID, device_id)
                if device_name:
                    entity_copy.setdefault(CONF_ENTITY_DEVICE_NAME, device_name)
                yield subentry_id, subentry, device_id, device_name, entity_copy
            continue

        yield subentry_id, subentry, device_id, device_name, dict(data)
