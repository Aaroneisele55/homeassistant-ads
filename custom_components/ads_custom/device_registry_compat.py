"""Compatibility helpers for the Home Assistant device registry.

Home Assistant 2026.8 restricts a device to a single config entry and at
most one config subentry (devices are no longer merged/shared across
config entries). See:
https://developers.home-assistant.io/blog/2026/07/21/device-registry-single-config-entry/

This integration talks to the device registry directly (to keep several
ADS entities grouped as sub-devices under one hub), so it is one of the
integrations affected by that change. These helpers let ads_custom work
correctly on both the pre-2026.8 (multi-config-entry) device model and
the 2026.8+ (single-config-entry) model, without depending on the
deprecated backwards-compatibility shims (which HA removes in 2027.8)
any longer than necessary.
"""

from __future__ import annotations

from typing import Any

from homeassistant.helpers import device_registry as dr

# True once running on a Home Assistant Core that implements the 2026.8
# single-config-entry device registry (DeviceRegistry.async_get_device_by_identifier
# was introduced alongside that change).
SINGLE_CONFIG_ENTRY_DEVICES = hasattr(dr.DeviceRegistry, "async_get_device_by_identifier")


def async_get_device_by_identifier(
    device_registry: dr.DeviceRegistry,
    domain: str,
    identifier: str,
    config_entry_id: str,
) -> dr.DeviceEntry | None:
    """Look up a device by (domain, identifier), scoped to a config entry.

    Uses the new, unambiguous 2026.8 lookup when available (identifiers are
    only unique per config entry from 2026.8 onward); falls back to the
    pre-2026.8 global identifier lookup on older cores.
    """
    if SINGLE_CONFIG_ENTRY_DEVICES:
        return device_registry.async_get_device_by_identifier(
            (domain, identifier), config_entry_id
        )
    return device_registry.async_get_device(identifiers={(domain, identifier)})


def device_belongs_to_entry(device: Any, entry_id: str) -> bool:
    """Return whether a device is linked to the given config entry."""
    if device is None:
        return False
    if SINGLE_CONFIG_ENTRY_DEVICES:
        return device.config_entry_id == entry_id
    # Pre-2026.8: a device could be linked to several config entries,
    # directly and/or via a subentry map.
    if entry_id in getattr(device, "config_entries", ()):
        return True
    subentry_map = getattr(device, "config_entries_subentries", None)
    return bool(isinstance(subentry_map, dict) and subentry_map.get(entry_id))


def async_ensure_device_subentry(
    device_registry: dr.DeviceRegistry,
    device: Any,
    entry_id: str,
    subentry_id: str,
) -> None:
    """Make sure a device is associated with entry_id/subentry_id.

    On 2026.8+ a device only ever has one owning entry and subentry, so
    this simply moves it there. On older cores it adds the association,
    first cleaning up a redundant direct-entry association if one exists
    (mirrors the previous duplicate-device-display fix).
    """
    if SINGLE_CONFIG_ENTRY_DEVICES:
        if device.config_entry_id != entry_id or device.config_subentry_id != subentry_id:
            device_registry.async_update_device(
                device.id,
                new_config_entry_id=entry_id,
                new_config_subentry_id=subentry_id,
            )
        return

    subentry_ids = (device.config_entries_subentries or {}).get(entry_id)
    has_subentry_association = bool(subentry_ids and subentry_id in subentry_ids)
    has_direct_entry_association = entry_id in device.config_entries

    if has_direct_entry_association and has_subentry_association:
        # Redundant direct association next to the proper subentry one.
        # Two calls are required: async_update_device can't add and remove
        # the same entry_id in a single call.
        device_registry.async_update_device(device.id, remove_config_entry_id=entry_id)
        device = device_registry.async_get_device(identifiers=device.identifiers)
        if device is None:
            return
        device_registry.async_update_device(
            device.id, add_config_entry_id=entry_id, add_config_subentry_id=subentry_id
        )
    elif not has_subentry_association:
        device_registry.async_update_device(
            device.id, add_config_entry_id=entry_id, add_config_subentry_id=subentry_id
        )


def async_detach_device_from_entry(
    device_registry: dr.DeviceRegistry, device: Any, entry_id: str
) -> None:
    """Remove a device's association with entry_id.

    On 2026.8+ a device belongs to exactly one config entry, so detaching
    it from that entry means removing the device outright. On older cores
    it means dropping just that one config-entry association (the device
    may still be linked to others).
    """
    if SINGLE_CONFIG_ENTRY_DEVICES:
        device_registry.async_remove_device(device.id)
        return
    device_registry.async_update_device(device.id, remove_config_entry_id=entry_id)
