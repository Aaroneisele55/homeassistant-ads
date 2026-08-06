"""Test the config flow for the ADS Custom integration."""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ads_custom.config_flow import (
    AdsConfigFlow,
    AdsEntitySubentryFlowHandler,
    AdsOptionsFlowHandler,
    DEVICE_OPTION_CREATE_NEW,
    OPTION_DELETE_EMPTY_DEVICES,
    OPTION_MOVE_ENTITIES,
)
from custom_components.ads_custom.entity import resolve_device_name, to_suggested_object_id


class TestDeviceClassLists:
    """Tests for device class lists."""

    def test_binary_sensor_device_classes_includes_none_option(self):
        """Test that binary sensor device classes list includes (None) option as first element."""
        config_flow_path = Path(__file__).parent.parent / "custom_components" / "ads_custom" / "config_flow.py"
        with open(config_flow_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())

        # Find the BINARY_SENSOR_DEVICE_CLASSES assignment
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "BINARY_SENSOR_DEVICE_CLASSES":
                        # Get the first element
                        if isinstance(node.value, ast.List):
                            first_elem = node.value.elts[0]
                            # Should be a dict with "label" and "value" keys
                            assert isinstance(first_elem, ast.Dict)
                            # Extract keys and values
                            keys = [k.value for k in first_elem.keys if isinstance(k, ast.Constant)]
                            values = [v.value for v in first_elem.values if isinstance(v, ast.Constant)]
                            assert "label" in keys
                            assert "value" in keys
                            label_idx = keys.index("label")
                            value_idx = keys.index("value")
                            assert values[label_idx] == "(None)"
                            assert values[value_idx] == ""
                            return
        pytest.fail("BINARY_SENSOR_DEVICE_CLASSES not found in config_flow.py")

    def test_sensor_device_classes_includes_none_option(self):
        """Test that sensor device classes list includes (None) option as first element."""
        config_flow_path = Path(__file__).parent.parent / "custom_components" / "ads_custom" / "config_flow.py"
        with open(config_flow_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "SENSOR_DEVICE_CLASSES":
                        if isinstance(node.value, ast.List):
                            first_elem = node.value.elts[0]
                            assert isinstance(first_elem, ast.Dict)
                            keys = [k.value for k in first_elem.keys if isinstance(k, ast.Constant)]
                            values = [v.value for v in first_elem.values if isinstance(v, ast.Constant)]
                            assert "label" in keys
                            assert "value" in keys
                            label_idx = keys.index("label")
                            value_idx = keys.index("value")
                            assert values[label_idx] == "(None)"
                            assert values[value_idx] == ""
                            return
        pytest.fail("SENSOR_DEVICE_CLASSES not found in config_flow.py")

    def test_cover_device_classes_includes_none_option(self):
        """Test that cover device classes list includes (None) option as first element."""
        config_flow_path = Path(__file__).parent.parent / "custom_components" / "ads_custom" / "config_flow.py"
        with open(config_flow_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "COVER_DEVICE_CLASSES":
                        if isinstance(node.value, ast.List):
                            first_elem = node.value.elts[0]
                            assert isinstance(first_elem, ast.Dict)
                            keys = [k.value for k in first_elem.keys if isinstance(k, ast.Constant)]
                            values = [v.value for v in first_elem.values if isinstance(v, ast.Constant)]
                            assert "label" in keys
                            assert "value" in keys
                            label_idx = keys.index("label")
                            value_idx = keys.index("value")
                            assert values[label_idx] == "(None)"
                            assert values[value_idx] == ""
                            return
        pytest.fail("COVER_DEVICE_CLASSES not found in config_flow.py")

    def test_valve_device_classes_includes_none_option(self):
        """Test that valve device classes list includes (None) option as first element."""
        config_flow_path = Path(__file__).parent.parent / "custom_components" / "ads_custom" / "config_flow.py"
        with open(config_flow_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "VALVE_DEVICE_CLASSES":
                        if isinstance(node.value, ast.List):
                            first_elem = node.value.elts[0]
                            assert isinstance(first_elem, ast.Dict)
                            keys = [k.value for k in first_elem.keys if isinstance(k, ast.Constant)]
                            values = [v.value for v in first_elem.values if isinstance(v, ast.Constant)]
                            assert "label" in keys
                            assert "value" in keys
                            label_idx = keys.index("label")
                            value_idx = keys.index("value")
                            assert values[label_idx] == "(None)"
                            assert values[value_idx] == ""
                            return
        pytest.fail("VALVE_DEVICE_CLASSES not found in config_flow.py")

    @pytest.mark.parametrize(
        "constant_name",
        [
            "BINARY_SENSOR_DEVICE_CLASSES",
            "SENSOR_DEVICE_CLASSES",
            "COVER_DEVICE_CLASSES",
            "VALVE_DEVICE_CLASSES",
        ],
    )
    def test_all_device_class_options_are_dicts(self, constant_name: str):
        """Test that all device class options are in dict format for proper SelectSelector validation."""
        config_flow_path = Path(__file__).parent.parent / "custom_components" / "ads_custom" / "config_flow.py"
        with open(config_flow_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == constant_name:
                        if isinstance(node.value, ast.List):
                            # Check all elements are dicts
                            for elem in node.value.elts:
                                assert isinstance(elem, ast.Dict), f"All options in {constant_name} must be dicts"
                            return
        pytest.fail(f"{constant_name} not found in config_flow.py")


class TestRemoveEmptyOptionalFields:
    """Tests for _remove_empty_optional_fields helper method."""

    _remove_empty_optional_fields = staticmethod(
        AdsEntitySubentryFlowHandler._remove_empty_optional_fields
    )

    def test_removes_none_value(self):
        """Test that None values are removed."""
        data = {"field1": "value", "field2": None, "field3": "other"}
        self._remove_empty_optional_fields(data, "field2")
        assert "field2" not in data
        assert data == {"field1": "value", "field3": "other"}

    def test_removes_empty_string(self):
        """Test that empty strings are removed."""
        data = {"field1": "value", "field2": "", "field3": "other"}
        self._remove_empty_optional_fields(data, "field2")
        assert "field2" not in data
        assert data == {"field1": "value", "field3": "other"}

    def test_removes_whitespace_only_string(self):
        """Test that whitespace-only strings are removed."""
        data = {"field1": "value", "field2": "   ", "field3": "other"}
        self._remove_empty_optional_fields(data, "field2")
        assert "field2" not in data
        assert data == {"field1": "value", "field3": "other"}

    def test_removes_empty_list(self):
        """Test that empty lists are removed."""
        data = {"field1": "value", "field2": [], "field3": "other"}
        self._remove_empty_optional_fields(data, "field2")
        assert "field2" not in data
        assert data == {"field1": "value", "field3": "other"}

    def test_removes_empty_dict(self):
        """Test that empty dicts are removed."""
        data = {"field1": "value", "field2": {}, "field3": "other"}
        self._remove_empty_optional_fields(data, "field2")
        assert "field2" not in data
        assert data == {"field1": "value", "field3": "other"}

    def test_preserves_zero(self):
        """Test that zero (0) values are preserved."""
        data = {"field1": "value", "field2": 0, "field3": "other"}
        self._remove_empty_optional_fields(data, "field2")
        assert "field2" in data
        assert data["field2"] == 0

    def test_preserves_false(self):
        """Test that False values are preserved."""
        data = {"field1": "value", "field2": False, "field3": "other"}
        self._remove_empty_optional_fields(data, "field2")
        assert "field2" in data
        assert data["field2"] is False

    def test_preserves_valid_string(self):
        """Test that non-empty strings are preserved."""
        data = {"field1": "value", "field2": "temperature", "field3": "other"}
        self._remove_empty_optional_fields(data, "field2")
        assert "field2" in data
        assert data["field2"] == "temperature"

    def test_handles_missing_field(self):
        """Test that missing fields are handled gracefully."""
        data = {"field1": "value", "field3": "other"}
        # Should not raise an error
        self._remove_empty_optional_fields(data, "field2")
        assert data == {"field1": "value", "field3": "other"}

    def test_handles_multiple_fields(self):
        """Test that multiple fields can be processed at once."""
        data = {
            "field1": "value",
            "field2": "",
            "field3": None,
            "field4": "other",
            "field5": "  ",
        }
        self._remove_empty_optional_fields(
            data, "field2", "field3", "field5"
        )
        assert data == {"field1": "value", "field4": "other"}


class TestRemoveClearedOptionalFields:
    """Tests for _remove_cleared_optional_fields helper method."""

    _remove_cleared_optional_fields = staticmethod(
        AdsEntitySubentryFlowHandler._remove_cleared_optional_fields
    )

    def test_removes_old_value_when_absent_from_user_input(self):
        """Test that old device_class is removed when user selects (None)."""
        old_data = {"adsvar": "GVL.Sensor", "name": "Test", "device_class": "battery"}
        user_input = {"adsvar": "GVL.Sensor", "name": "Test"}
        merged = dict(old_data)
        merged.update(user_input)
        self._remove_cleared_optional_fields(merged, user_input, "device_class")
        assert "device_class" not in merged

    def test_preserves_value_when_present_in_user_input(self):
        """Test that device_class is preserved when user selects a new value."""
        old_data = {"adsvar": "GVL.Sensor", "name": "Test", "device_class": "battery"}
        user_input = {"adsvar": "GVL.Sensor", "name": "Test", "device_class": "door"}
        merged = dict(old_data)
        merged.update(user_input)
        self._remove_cleared_optional_fields(merged, user_input, "device_class")
        assert merged["device_class"] == "door"

    def test_no_error_when_field_not_in_old_data(self):
        """Test that missing fields in old data are handled gracefully."""
        old_data = {"adsvar": "GVL.Sensor", "name": "Test"}
        user_input = {"adsvar": "GVL.Sensor", "name": "Test"}
        merged = dict(old_data)
        merged.update(user_input)
        self._remove_cleared_optional_fields(merged, user_input, "device_class")
        assert "device_class" not in merged

    def test_handles_multiple_fields(self):
        """Test that multiple optional fields can be cleared at once."""
        old_data = {
            "name": "Test",
            "device_class": "battery",
            "state_class": "measurement",
        }
        user_input = {"name": "Test"}
        merged = dict(old_data)
        merged.update(user_input)
        self._remove_cleared_optional_fields(
            merged, user_input, "device_class", "state_class"
        )
        assert "device_class" not in merged
        assert "state_class" not in merged

    def test_clears_only_absent_fields(self):
        """Test that only absent fields are cleared, present ones preserved."""
        old_data = {
            "name": "Test",
            "device_class": "battery",
            "state_class": "measurement",
        }
        user_input = {"name": "Test", "state_class": "total"}
        merged = dict(old_data)
        merged.update(user_input)
        self._remove_cleared_optional_fields(
            merged, user_input, "device_class", "state_class"
        )
        assert "device_class" not in merged
        assert merged["state_class"] == "total"


class TestReconfigureForms:
    """Regression tests for reconfigure forms to ensure clearable fields work correctly.
    
    These tests verify that optional clearable fields (device_class, state_class) do NOT
    have default= parameters in vol.Optional(), and that suggested_values is used instead.
    This prevents the bug where defaults would prevent clearing fields.
    """

    @staticmethod
    def _get_config_flow_tree() -> ast.Module:
        """Load and parse the config_flow.py file."""
        config_flow_path = (
            Path(__file__).parent.parent
            / "custom_components"
            / "ads_custom"
            / "config_flow.py"
        )
        with open(config_flow_path, "r", encoding="utf-8") as f:
            return ast.parse(f.read())

    @staticmethod
    def _get_function_node(tree: ast.Module, function_name: str) -> ast.AsyncFunctionDef | ast.FunctionDef | None:
        """Find a function definition by name in the AST, including async methods."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
                return node
        return None

    @staticmethod
    def _find_optional_field_in_function(
        func_node: ast.AsyncFunctionDef | ast.FunctionDef, field_name: str
    ) -> tuple[bool, bool]:
        """Check if a field is defined with vol.Optional and if it has a default.
        
        Returns:
            Tuple of (field_found, has_default)
        """
        for node in ast.walk(func_node):
            candidate_calls: list[ast.Call] = []

            # Look for subscript assignments like schema_dict[vol.Optional(...)]
            if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Call):
                candidate_calls.append(node.slice)

            # Also look for dict keys like {vol.Optional(...): selector.SelectSelector(...)}
            if isinstance(node, ast.Dict):
                for key in node.keys:
                    if isinstance(key, ast.Call):
                        candidate_calls.append(key)

            for call in candidate_calls:
                # Check if this is vol.Optional
                if (
                    isinstance(call.func, ast.Attribute)
                    and isinstance(call.func.value, ast.Name)
                    and call.func.value.id == "vol"
                    and call.func.attr == "Optional"
                ):
                    # Check if first argument is the field we're looking for
                    if call.args:
                        first_arg = call.args[0]
                        field_matches = False

                        # Handle both Name nodes (CONF_DEVICE_CLASS) and string literals
                        if isinstance(first_arg, ast.Name) and first_arg.id == field_name:
                            field_matches = True
                        elif isinstance(first_arg, ast.Constant) and first_arg.value == field_name:
                            field_matches = True

                        if field_matches:
                            # Check if there's a default= keyword argument
                            has_default = any(
                                kw.arg == "default" for kw in call.keywords
                            )
                            return True, has_default
        return False, False

    def test_reconfigure_sensor_device_class_has_no_default(self):
        """Test that device_class in reconfigure_sensor has no default parameter."""
        tree = self._get_config_flow_tree()
        func = self._get_function_node(tree, "async_step_reconfigure_sensor")
        assert func is not None, "async_step_reconfigure_sensor not found"

        found, has_default = self._find_optional_field_in_function(
            func, "CONF_DEVICE_CLASS"
        )
        assert found, "CONF_DEVICE_CLASS not found in async_step_reconfigure_sensor"
        assert not has_default, (
            "CONF_DEVICE_CLASS must not have default= parameter in "
            "async_step_reconfigure_sensor (breaks clearing functionality)"
        )

    def test_reconfigure_sensor_state_class_has_no_default(self):
        """Test that state_class in reconfigure_sensor has no default parameter."""
        tree = self._get_config_flow_tree()
        func = self._get_function_node(tree, "async_step_reconfigure_sensor")
        assert func is not None, "async_step_reconfigure_sensor not found"

        found, has_default = self._find_optional_field_in_function(
            func, "CONF_STATE_CLASS"
        )
        assert found, "CONF_STATE_CLASS not found in async_step_reconfigure_sensor"
        assert not has_default, (
            "CONF_STATE_CLASS must not have default= parameter in "
            "async_step_reconfigure_sensor (breaks clearing functionality)"
        )

    def test_reconfigure_binary_sensor_device_class_has_no_default(self):
        """Test that device_class in reconfigure_binary_sensor has no default parameter."""
        tree = self._get_config_flow_tree()
        func = self._get_function_node(tree, "async_step_reconfigure_binary_sensor")
        assert func is not None, "async_step_reconfigure_binary_sensor not found"

        found, has_default = self._find_optional_field_in_function(
            func, "CONF_DEVICE_CLASS"
        )
        assert found, "CONF_DEVICE_CLASS not found in async_step_reconfigure_binary_sensor"
        assert not has_default, (
            "CONF_DEVICE_CLASS must not have default= parameter in "
            "async_step_reconfigure_binary_sensor (breaks clearing functionality)"
        )

    def test_reconfigure_cover_device_class_has_no_default(self):
        """Test that device_class in reconfigure_cover has no default parameter."""
        tree = self._get_config_flow_tree()
        func = self._get_function_node(tree, "async_step_reconfigure_cover")
        assert func is not None, "async_step_reconfigure_cover not found"

        found, has_default = self._find_optional_field_in_function(
            func, "CONF_DEVICE_CLASS"
        )
        assert found, "CONF_DEVICE_CLASS not found in async_step_reconfigure_cover"
        assert not has_default, (
            "CONF_DEVICE_CLASS must not have default= parameter in "
            "async_step_reconfigure_cover (breaks clearing functionality)"
        )

    def test_reconfigure_valve_device_class_has_no_default(self):
        """Test that device_class in reconfigure_valve has no default parameter."""
        tree = self._get_config_flow_tree()
        func = self._get_function_node(tree, "async_step_reconfigure_valve")
        assert func is not None, "async_step_reconfigure_valve not found"

        found, has_default = self._find_optional_field_in_function(
            func, "CONF_DEVICE_CLASS"
        )
        assert found, "CONF_DEVICE_CLASS not found in async_step_reconfigure_valve"
        assert not has_default, (
            "CONF_DEVICE_CLASS must not have default= parameter in "
            "async_step_reconfigure_valve (breaks clearing functionality)"
        )


class TestDeviceAssignmentSupport:
    """Tests for configurable entity-to-device assignment support."""

    _config_flow_ast_cache: ast.Module | None = None

    @classmethod
    def _get_config_flow_tree(cls) -> ast.Module:
        """Load and parse config_flow.py once and reuse the AST."""
        if cls._config_flow_ast_cache is None:
            config_flow_path = (
                Path(__file__).parent.parent
                / "custom_components"
                / "ads_custom"
                / "config_flow.py"
            )
            with open(config_flow_path, "r", encoding="utf-8") as file:
                cls._config_flow_ast_cache = ast.parse(file.read())
        return cls._config_flow_ast_cache

    @staticmethod
    def _get_function_node(tree: ast.Module, function_name: str) -> ast.AsyncFunctionDef | None:
        """Find an async function definition by name."""
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == function_name:
                return node
        return None

    @staticmethod
    def _function_references_name(func_node: ast.AsyncFunctionDef, name: str) -> bool:
        """Return True if function references a given variable name."""
        return any(
            (isinstance(node, ast.Name) and node.id == name)
            or (isinstance(node, ast.Attribute) and node.attr == name)
            for node in ast.walk(func_node)
        )

    @pytest.mark.parametrize(
        "function_name",
        [
            "async_step_configure_switch",
            "async_step_configure_sensor",
            "async_step_configure_binary_sensor",
            "async_step_configure_light",
            "async_step_configure_cover",
            "async_step_configure_valve",
            "async_step_configure_select",
            "async_step_reconfigure_switch",
            "async_step_reconfigure_sensor",
            "async_step_reconfigure_binary_sensor",
            "async_step_reconfigure_light",
            "async_step_reconfigure_cover",
            "async_step_reconfigure_valve",
            "async_step_reconfigure_select",
        ],
    )
    def test_device_assignment_fields_used_in_entity_forms(self, function_name: str):
        """Ensure each add/reconfigure form uses device assignment fields."""
        tree = self._get_config_flow_tree()
        func = self._get_function_node(tree, function_name)
        assert func is not None, f"{function_name} not found"
        assert self._function_references_name(func, "_device_assignment_schema"), (
            f"{function_name} should include device assignment schema"
        )

    def test_device_name_validation_error_exists(self):
        """Ensure the device-name-required validation error key is present."""
        tree = self._get_config_flow_tree()
        assert any(
            isinstance(node, ast.Constant) and node.value == "device_name_required"
            for node in ast.walk(tree)
        ), "device_name_required error key not found in config_flow.py"


class TestResolveDeviceAssignment:
    """Tests for _resolve_device_assignment helper behavior."""

    def test_existing_device_selection_clears_new_device_name(self):
        """Selecting existing device should keep device id and clear new device name."""
        user_input = {
            "entity_device_id": "existing-device",
            "entity_device_name": "Should be removed",
        }

        result = AdsEntitySubentryFlowHandler._resolve_device_assignment(user_input)

        assert result is True
        assert user_input["entity_device_id"] == "existing-device"
        assert "entity_device_name" not in user_input

    def test_create_new_device_requires_name(self):
        """Creating a new device without name should fail validation."""
        user_input = {"entity_device_id": DEVICE_OPTION_CREATE_NEW}

        result = AdsEntitySubentryFlowHandler._resolve_device_assignment(user_input)

        assert result is False

    def test_reconfigure_legacy_uses_unique_id_fallback(self):
        """Legacy reconfigure should reuse unique_id when entity_device_id is absent."""
        user_input = {}
        current_data = {"unique_id": "legacy-entity-id"}

        result = AdsEntitySubentryFlowHandler._resolve_device_assignment(
            user_input,
            current_data=current_data,
        )

        assert result is True
        assert user_input["entity_device_id"] == "legacy-entity-id"

    def test_new_entity_requires_explicit_device_selection(self):
        """New entities must explicitly choose existing device or create new."""
        user_input = {}
        result = AdsEntitySubentryFlowHandler._resolve_device_assignment(user_input)
        assert result is False


class TestLegacyDeviceRenameSync:
    """Tests for legacy device rename synchronization during reconfigure."""

    def test_legacy_device_rename_syncs_only_when_entity_stays_on_implicit_device(self):
        """Only the implicit legacy device should follow an entity rename."""
        flow = AdsEntitySubentryFlowHandler()
        flow._entity_data = {"unique_id": "legacy-device"}

        assert flow._should_update_legacy_device_name({"entity_device_id": "legacy-device"}) is True
        assert flow._should_update_legacy_device_name({"entity_device_id": "other-device"}) is False

    def test_explicit_device_assignment_never_syncs_legacy_device_name(self):
        """Entities already assigned to a device must not rename their legacy device."""
        flow = AdsEntitySubentryFlowHandler()
        flow._entity_data = {"unique_id": "legacy-device", "entity_device_id": "existing-device"}

        assert flow._should_update_legacy_device_name({"entity_device_id": "existing-device"}) is False

    @pytest.mark.asyncio
    async def test_reconfigure_sensor_reassignment_does_not_rename_target_device(self):
        """Assigning a legacy entity to an existing device should not rename that device."""
        flow = AdsEntitySubentryFlowHandler()
        flow._entity_data = {
            "unique_id": "legacy-device",
            "entity_type": "sensor",
            "adsvar": "GVL.Test",
            "name": "Legacy Entity",
        }
        flow.hass = MagicMock()
        flow._config_entry = MagicMock()
        flow._config_entry.entry_id = "entry-id"
        flow.handler = MagicMock(config_entry=flow._config_entry)
        flow.hass.config_entries.async_update_subentry = MagicMock()
        flow._get_reconfigure_subentry = MagicMock(return_value=MagicMock(unique_id="legacy-device"))
        flow._update_device_name_if_changed = MagicMock()
        flow.async_abort = MagicMock(return_value={"type": "abort"})

        result = await flow.async_step_reconfigure_sensor(
            {
                "adsvar": "GVL.Test",
                "name": "Renamed Entity",
                "entity_device_id": "existing-device",
            }
        )

        assert result["type"] == "abort"
        flow._update_device_name_if_changed.assert_not_called()
        flow.hass.config_entries.async_update_subentry.assert_called_once()
        updated_data = flow.hass.config_entries.async_update_subentry.call_args.kwargs["data"]
        assert updated_data["entity_device_id"] == "existing-device"
        assert "entity_device_name" not in updated_data


class TestHubOptionsFlowSupport:
    """Tests for config-entry options flow support."""

    def test_config_flow_returns_hub_options_flow_handler(self):
        """Config flow should expose AdsOptionsFlowHandler for config entry options."""
        flow = AdsConfigFlow.async_get_options_flow(MagicMock())
        assert isinstance(flow, AdsOptionsFlowHandler)


class TestDeviceRegistryMembershipHandling:
    """Tests for device registry membership and naming behavior."""

    def test_device_selection_includes_subentry_linked_devices(self, monkeypatch):
        """Devices linked only through subentries should still appear in the picker."""
        flow = AdsOptionsFlowHandler()
        flow._config_entry = MagicMock()
        flow._config_entry.entry_id = "entry-id"
        flow._config_entry.subentries = {
            "subentry-1": MagicMock(
                subentry_type="entity",
                data={"entity_device_id": "subentry-device"},
                unique_id="entity-1",
                title="Subentry entity",
            )
        }
        flow.hass = MagicMock()

        direct_device = MagicMock()
        direct_device.id = "direct-registry-id"
        direct_device.identifiers = {("ads_custom", "direct-device")}
        direct_device.config_entries = {"entry-id"}
        direct_device.config_entries_subentries = {}
        direct_device.name_by_user = None
        direct_device.name = "Direct device"

        subentry_device = MagicMock()
        subentry_device.id = "subentry-registry-id"
        subentry_device.identifiers = {("ads_custom", "subentry-device")}
        subentry_device.config_entries = set()
        subentry_device.config_entries_subentries = {"entry-id": {"subentry-1"}}
        subentry_device.name_by_user = None
        subentry_device.name = "Subentry device"

        foreign_device = MagicMock()
        foreign_device.id = "foreign-registry-id"
        foreign_device.identifiers = {("ads_custom", "foreign-device")}
        foreign_device.config_entries = {"other-entry"}
        foreign_device.config_entries_subentries = {}
        foreign_device.name_by_user = None
        foreign_device.name = "Foreign device"

        registry = MagicMock()
        registry.devices = {
            direct_device.id: direct_device,
            subentry_device.id: subentry_device,
            foreign_device.id: foreign_device,
        }

        monkeypatch.setattr("custom_components.ads_custom.config_flow.dr.async_get", lambda hass: registry)

        options = flow._get_device_selection_options()
        values = {option["value"] for option in options}

        assert "direct-device" in values
        assert "subentry-device" in values
        assert "foreign-device" not in values

    def test_resolve_device_name_prefers_existing_registry_name(self, monkeypatch):
        """Existing devices should keep their registry name instead of the fallback."""
        device = MagicMock()
        device.name_by_user = None
        device.name = "Existing device"

        registry = MagicMock()
        registry.async_get_device.return_value = device

        monkeypatch.setattr("custom_components.ads_custom.entity.dr.async_get", lambda hass: registry)

        resolved_name = resolve_device_name(MagicMock(), "device-id", "Fallback name", "entry-id")

        assert resolved_name == "Existing device"

    def test_to_suggested_object_id_transliterates_umlauts(self):
        """Umlauts should be transliterated before slugification."""
        assert to_suggested_object_id("Kühlung ein") == "kuehlung_ein"

    def test_to_suggested_object_id_transliterates_sharp_s(self):
        """ß should be transliterated to ss before slugification."""
        assert to_suggested_object_id("Straße") == "strasse"


class TestDeleteEmptyDevicesSupport:
    """Tests for bulk empty-device cleanup in the hub options flow."""

    def test_device_actions_menu_includes_delete_all_empty_devices(self):
        """The device actions menu should expose the bulk delete action."""
        config_flow_path = Path(__file__).parent.parent / "custom_components" / "ads_custom" / "config_flow.py"
        with open(config_flow_path, "r", encoding="utf-8") as file:
            source = file.read()

        assert "Delete all empty devices" in source
        assert "OPTION_DELETE_EMPTY_DEVICES" in source

    def test_delete_empty_devices_removes_only_unassigned_devices(self, monkeypatch):
        """Bulk deletion should only remove devices that have no entity subentries."""
        flow = AdsOptionsFlowHandler()
        flow._config_entry = MagicMock()
        flow._config_entry.entry_id = "entry-id"
        flow._config_entry.subentries = {
            "assigned": MagicMock(
                subentry_type="entity",
                data={"entity_device_id": "assigned-device"},
                unique_id="assigned-entity",
                title="Assigned entity",
            )
        }
        flow.hass = MagicMock()

        assigned_device = MagicMock()
        assigned_device.id = "assigned-registry-id"
        assigned_device.identifiers = {("ads_custom", "assigned-device")}
        assigned_device.config_entries = {"entry-id"}

        empty_device = MagicMock()
        empty_device.id = "empty-registry-id"
        empty_device.identifiers = {("ads_custom", "empty-device")}
        empty_device.config_entries = {"entry-id"}

        other_entry_device = MagicMock()
        other_entry_device.id = "other-registry-id"
        other_entry_device.identifiers = {("ads_custom", "other-device")}
        other_entry_device.config_entries = {"other-entry"}

        registry = MagicMock()
        registry.devices = {
            assigned_device.id: assigned_device,
            empty_device.id: empty_device,
            other_entry_device.id: other_entry_device,
        }
        registry.async_get_device.side_effect = lambda identifiers: {
            frozenset({("ads_custom", "assigned-device")}): assigned_device,
            frozenset({("ads_custom", "empty-device")}): empty_device,
            frozenset({("ads_custom", "other-device")}): other_entry_device,
        }.get(frozenset(identifiers))

        monkeypatch.setattr("custom_components.ads_custom.config_flow.dr.async_get", lambda hass: registry)

        deleted_count = flow._delete_empty_devices()

        assert deleted_count == 1
        registry.async_update_device.assert_called_once_with(
            empty_device.id,
            remove_config_entry_id="entry-id",
        )

    def test_delete_empty_devices_option_constant_has_expected_value(self):
        """The bulk delete action constant should remain stable."""
        assert OPTION_DELETE_EMPTY_DEVICES == "__delete_empty_devices__"


class TestMoveEntitiesSupport:
    """Tests for bulk entity move support in the hub options flow."""

    def test_device_actions_menu_includes_move_entities_action(self):
        """The device actions menu should expose the bulk move action."""
        config_flow_path = Path(__file__).parent.parent / "custom_components" / "ads_custom" / "config_flow.py"
        with open(config_flow_path, "r", encoding="utf-8") as file:
            source = file.read()

        assert "Move entities to this device" in source
        assert "OPTION_MOVE_ENTITIES" in source

    def test_move_entities_step_uses_multi_select(self):
        """The bulk move step should allow selecting multiple entities."""
        config_flow_path = Path(__file__).parent.parent / "custom_components" / "ads_custom" / "config_flow.py"
        with open(config_flow_path, "r", encoding="utf-8") as file:
            tree = ast.parse(file.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "async_step_move_entities":
                assert any(
                    isinstance(keyword, ast.keyword)
                    and keyword.arg == "multiple"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value is True
                    for keyword in ast.walk(node)
                ), "async_step_move_entities must set multiple=True on the selector"
                return

        pytest.fail("async_step_move_entities not found in config_flow.py")

    @pytest.mark.asyncio
    async def test_device_actions_routes_to_move_entities_step(self):
        """Choosing the move action should open the bulk move step."""
        flow = AdsOptionsFlowHandler()
        flow._selected_device_id = "target-device"
        flow._device_name_for_id = MagicMock(return_value="Target device")
        flow._device_entities_map = MagicMock(return_value={})
        flow._entity_select_options = MagicMock(return_value=[])
        flow.async_step_move_entities = AsyncMock(return_value={"type": "form", "step_id": "move_entities"})

        result = await flow.async_step_device_actions({"device_action": OPTION_MOVE_ENTITIES})

        assert result == {"type": "form", "step_id": "move_entities"}
        flow.async_step_move_entities.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_move_entities_updates_selected_subentries(self, monkeypatch):
        """The bulk move step should rewrite every selected entity to the target device."""
        flow = AdsOptionsFlowHandler()
        flow._config_entry = MagicMock()
        flow._config_entry.entry_id = "entry-id"
        flow._selected_device_id = "target-device"

        selected_one = MagicMock(
            subentry_type="entity",
            data={"name": "Entity One", "entity_device_id": "source-device-1"},
            unique_id="entity-one",
            title="Entity One",
        )
        selected_two = MagicMock(
            subentry_type="entity",
            data={"name": "Entity Two", "entity_device_id": "source-device-2"},
            unique_id="entity-two",
            title="Entity Two",
        )
        flow._config_entry.subentries = {
            "subentry-one": selected_one,
            "subentry-two": selected_two,
        }
        flow.hass = MagicMock()

        target_device = MagicMock()
        target_device.id = "target-registry-id"
        target_device.identifiers = {("ads_custom", "target-device")}
        target_device.config_entries = {"entry-id"}
        target_device.config_entries_subentries = {}
        target_device.name_by_user = None
        target_device.name = "Target device"

        registry = MagicMock()
        registry.devices = {target_device.id: target_device}

        monkeypatch.setattr("custom_components.ads_custom.config_flow.dr.async_get", lambda hass: registry)

        await flow.async_step_move_entities({"selected_entity_subentry_id": ["subentry-one", "subentry-two"]})

        assert flow.hass.config_entries.async_update_subentry.call_count == 2
        for call in flow.hass.config_entries.async_update_subentry.call_args_list:
            updated_data = call.kwargs["data"]
            assert updated_data["entity_device_id"] == "target-device"
            assert updated_data["entity_device_name"] == "Target device"

    def test_move_entities_option_constant_has_expected_value(self):
        """The bulk move action constant should remain stable."""
        assert OPTION_MOVE_ENTITIES == "__move_entities__"
