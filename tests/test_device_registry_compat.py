"""Tests for device_registry_compat.

The Home Assistant package available in this test environment predates
2026.8, so SINGLE_CONFIG_ENTRY_DEVICES is False when these run "for real".
These tests monkeypatch the module-level flag to exercise both code
paths regardless of which HA version is actually installed.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import custom_components.ads_custom.device_registry_compat as compat


class TestDeviceBelongsToEntry:
    def test_new_model_matches_on_config_entry_id(self, monkeypatch):
        monkeypatch.setattr(compat, "SINGLE_CONFIG_ENTRY_DEVICES", True)
        device = MagicMock(config_entry_id="entry-1")
        assert compat.device_belongs_to_entry(device, "entry-1") is True
        assert compat.device_belongs_to_entry(device, "entry-2") is False

    def test_old_model_matches_direct_or_subentry_association(self, monkeypatch):
        monkeypatch.setattr(compat, "SINGLE_CONFIG_ENTRY_DEVICES", False)
        direct = MagicMock(config_entries={"entry-1"}, config_entries_subentries={})
        assert compat.device_belongs_to_entry(direct, "entry-1") is True

        via_subentry = MagicMock(
            config_entries=set(), config_entries_subentries={"entry-1": {"sub-1"}}
        )
        assert compat.device_belongs_to_entry(via_subentry, "entry-1") is True

        unrelated = MagicMock(config_entries=set(), config_entries_subentries={})
        assert compat.device_belongs_to_entry(unrelated, "entry-1") is False

    def test_none_device_never_belongs(self, monkeypatch):
        monkeypatch.setattr(compat, "SINGLE_CONFIG_ENTRY_DEVICES", True)
        assert compat.device_belongs_to_entry(None, "entry-1") is False


class TestGetDeviceByIdentifier:
    def test_new_model_uses_scoped_lookup(self, monkeypatch):
        monkeypatch.setattr(compat, "SINGLE_CONFIG_ENTRY_DEVICES", True)
        registry = MagicMock()
        compat.async_get_device_by_identifier(registry, "ads_custom", "dev-1", "entry-1")
        registry.async_get_device_by_identifier.assert_called_once_with(
            ("ads_custom", "dev-1"), "entry-1"
        )
        registry.async_get_device.assert_not_called()

    def test_old_model_uses_global_identifier_lookup(self, monkeypatch):
        monkeypatch.setattr(compat, "SINGLE_CONFIG_ENTRY_DEVICES", False)
        registry = MagicMock()
        compat.async_get_device_by_identifier(registry, "ads_custom", "dev-1", "entry-1")
        registry.async_get_device.assert_called_once_with(
            identifiers={("ads_custom", "dev-1")}
        )
        registry.async_get_device_by_identifier.assert_not_called()


class TestEnsureDeviceSubentry:
    def test_new_model_moves_device_when_needed(self, monkeypatch):
        monkeypatch.setattr(compat, "SINGLE_CONFIG_ENTRY_DEVICES", True)
        registry = MagicMock()
        device = MagicMock(id="dev-id", config_entry_id="old-entry", config_subentry_id=None)
        compat.async_ensure_device_subentry(registry, device, "entry-1", "sub-1")
        registry.async_update_device.assert_called_once_with(
            "dev-id", new_config_entry_id="entry-1", new_config_subentry_id="sub-1"
        )

    def test_new_model_is_noop_when_already_correct(self, monkeypatch):
        monkeypatch.setattr(compat, "SINGLE_CONFIG_ENTRY_DEVICES", True)
        registry = MagicMock()
        device = MagicMock(id="dev-id", config_entry_id="entry-1", config_subentry_id="sub-1")
        compat.async_ensure_device_subentry(registry, device, "entry-1", "sub-1")
        registry.async_update_device.assert_not_called()

    def test_old_model_adds_missing_subentry_association(self, monkeypatch):
        monkeypatch.setattr(compat, "SINGLE_CONFIG_ENTRY_DEVICES", False)
        registry = MagicMock()
        device = MagicMock(
            id="dev-id",
            config_entries={"entry-1"},
            config_entries_subentries={},
        )
        compat.async_ensure_device_subentry(registry, device, "entry-1", "sub-1")
        registry.async_update_device.assert_called_once_with(
            "dev-id", add_config_entry_id="entry-1", add_config_subentry_id="sub-1"
        )

    def test_old_model_fixes_duplicate_display(self, monkeypatch):
        monkeypatch.setattr(compat, "SINGLE_CONFIG_ENTRY_DEVICES", False)
        registry = MagicMock()
        device = MagicMock(
            id="dev-id",
            identifiers={("ads_custom", "dev-1")},
            config_entries={"entry-1"},
            config_entries_subentries={"entry-1": {"sub-1"}},
        )
        registry.async_get_device.return_value = device

        compat.async_ensure_device_subentry(registry, device, "entry-1", "sub-1")

        assert registry.async_update_device.call_count == 2
        first_call, second_call = registry.async_update_device.call_args_list
        assert first_call.kwargs == {"remove_config_entry_id": "entry-1"}
        assert second_call.kwargs == {
            "add_config_entry_id": "entry-1",
            "add_config_subentry_id": "sub-1",
        }


class TestDetachDeviceFromEntry:
    def test_new_model_removes_device_outright(self, monkeypatch):
        monkeypatch.setattr(compat, "SINGLE_CONFIG_ENTRY_DEVICES", True)
        registry = MagicMock()
        device = MagicMock(id="dev-id")
        compat.async_detach_device_from_entry(registry, device, "entry-1")
        registry.async_remove_device.assert_called_once_with("dev-id")
        registry.async_update_device.assert_not_called()

    def test_old_model_only_drops_the_one_config_entry(self, monkeypatch):
        monkeypatch.setattr(compat, "SINGLE_CONFIG_ENTRY_DEVICES", False)
        registry = MagicMock()
        device = MagicMock(id="dev-id")
        compat.async_detach_device_from_entry(registry, device, "entry-1")
        registry.async_update_device.assert_called_once_with(
            "dev-id", remove_config_entry_id="entry-1"
        )
        registry.async_remove_device.assert_not_called()
