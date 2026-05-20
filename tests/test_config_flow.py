"""Test the config flow for the ADS Custom integration."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from custom_components.ads_custom.config_flow import (
    AdsEntitySubentryFlowHandler,
    DEVICE_OPTION_CREATE_NEW,
)


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
    def _get_config_flow_tree() -> ast.AST:
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
    def _get_function_node(tree: ast.AST, function_name: str) -> ast.AsyncFunctionDef | ast.FunctionDef | None:
        """Find a function definition by name in the AST, including async methods."""
        # Search in top-level and class bodies
        for node in tree.body:
            # Check top-level functions
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
                return node
            # Check class methods
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == function_name:
                        return item
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
            # Look for subscript assignments like schema_dict[vol.Optional(...)]
            if isinstance(node, ast.Subscript):
                if isinstance(node.slice, ast.Call):
                    call = node.slice
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

    _config_flow_ast_cache: ast.AST | None = None

    @classmethod
    def _get_config_flow_tree(cls) -> ast.AST:
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
    def _get_function_node(tree: ast.AST, function_name: str) -> ast.AsyncFunctionDef | None:
        """Find an async function definition by name."""
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.AsyncFunctionDef) and item.name == function_name:
                        return item
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


class TestAdsHubOptionsFlowHandler:
    """Tests for the hub-level AdsHubOptionsFlowHandler options flow."""

    def test_options_flow_handler_importable(self):
        """AdsHubOptionsFlowHandler can be imported from config_flow."""
        from custom_components.ads_custom.config_flow import AdsHubOptionsFlowHandler

        assert AdsHubOptionsFlowHandler is not None

    def test_options_flow_registered_on_config_flow(self):
        """AdsConfigFlow.async_get_options_flow returns AdsHubOptionsFlowHandler instance."""
        from unittest.mock import MagicMock

        from custom_components.ads_custom.config_flow import (
            AdsConfigFlow,
            AdsHubOptionsFlowHandler,
        )

        config_entry = MagicMock()
        handler = AdsConfigFlow.async_get_options_flow(config_entry)
        assert isinstance(handler, AdsHubOptionsFlowHandler)

    def test_options_flow_has_entity_edit_steps(self):
        """AdsHubOptionsFlowHandler exposes async_step_edit_* for all entity types."""
        from custom_components.ads_custom.config_flow import AdsHubOptionsFlowHandler

        entity_types = [
            "switch",
            "sensor",
            "binary_sensor",
            "light",
            "cover",
            "valve",
            "select",
        ]
        for entity_type in entity_types:
            step_name = f"async_step_edit_{entity_type}"
            assert hasattr(AdsHubOptionsFlowHandler, step_name), (
                f"AdsHubOptionsFlowHandler missing {step_name}"
            )

    def test_options_flow_has_hub_connection_step(self):
        """AdsHubOptionsFlowHandler exposes async_step_hub_connection."""
        from custom_components.ads_custom.config_flow import AdsHubOptionsFlowHandler

        assert hasattr(AdsHubOptionsFlowHandler, "async_step_hub_connection")

    def test_options_flow_has_init_step(self):
        """AdsHubOptionsFlowHandler exposes async_step_init."""
        from custom_components.ads_custom.config_flow import AdsHubOptionsFlowHandler

        assert hasattr(AdsHubOptionsFlowHandler, "async_step_init")

    def test_options_flow_init_routes_to_hub_connection_sentinel(self):
        """Selecting __hub_connection__ in init routes to hub_connection step."""
        import asyncio
        from unittest.mock import AsyncMock, MagicMock, patch

        from custom_components.ads_custom.config_flow import (
            AdsHubOptionsFlowHandler,
            _HUB_CONNECTION_SENTINEL,
        )

        handler = AdsHubOptionsFlowHandler()

        # Mock the config entry with no subentries
        mock_entry = MagicMock()
        mock_entry.subentries = {}
        mock_entry.options = {}
        handler._config_entry = mock_entry  # OptionsFlow stores as _config_entry

        # Patch async_step_hub_connection to return a sentinel value
        hub_result = {"type": "form", "step_id": "hub_connection"}
        handler.async_step_hub_connection = AsyncMock(return_value=hub_result)

        # Patch async_show_form to capture what would be shown
        show_form_result = {"type": "form", "step_id": "init"}
        handler.async_show_form = MagicMock(return_value=show_form_result)
        handler.hass = MagicMock()

        # When no user_input, should show the init form
        result = asyncio.get_event_loop().run_until_complete(handler.async_step_init(None))
        assert result["step_id"] == "init"

        # When user selects hub_connection
        result = asyncio.get_event_loop().run_until_complete(
            handler.async_step_init({"selected_item": _HUB_CONNECTION_SENTINEL})
        )
        assert result["step_id"] == "hub_connection"
        handler.async_step_hub_connection.assert_called_once()

    def test_options_flow_init_routes_to_entity_edit(self):
        """Selecting an entity subentry in init routes to the correct edit step."""
        import asyncio
        from unittest.mock import AsyncMock, MagicMock

        from custom_components.ads_custom.config_flow import AdsHubOptionsFlowHandler

        handler = AdsHubOptionsFlowHandler()

        # Create a mock subentry for a switch
        mock_subentry = MagicMock()
        mock_subentry.subentry_id = "abc123"
        mock_subentry.subentry_type = "entity"
        mock_subentry.title = "Pump (Switch)"
        mock_subentry.data = {
            "entity_type": "switch",
            "adsvar": "GVL.Pump",
            "name": "Pump",
            "unique_id": "abc123",
        }

        mock_entry = MagicMock()
        mock_entry.subentries = {"abc123": mock_subentry}
        mock_entry.options = {}
        handler._config_entry = mock_entry

        edit_result = {"type": "form", "step_id": "edit_switch"}
        handler.async_step_edit_switch = AsyncMock(return_value=edit_result)

        show_form_result = {"type": "form", "step_id": "init"}
        handler.async_show_form = MagicMock(return_value=show_form_result)
        handler.hass = MagicMock()
        # Make hass.dr return empty device registry
        import homeassistant.helpers.device_registry as dr
        empty_devices = MagicMock()
        empty_devices.devices = {}

        with patch.object(dr, "async_get", return_value=empty_devices):
            result = asyncio.get_event_loop().run_until_complete(
                handler.async_step_init({"selected_item": "abc123"})
            )

        assert result["step_id"] == "edit_switch"
        handler.async_step_edit_switch.assert_called_once()

    def test_options_flow_init_aborts_for_unknown_entity(self):
        """Selecting a non-existent subentry in init aborts the flow."""
        import asyncio
        from unittest.mock import MagicMock

        from custom_components.ads_custom.config_flow import AdsHubOptionsFlowHandler

        handler = AdsHubOptionsFlowHandler()

        mock_entry = MagicMock()
        mock_entry.subentries = {}
        mock_entry.options = {}
        handler._config_entry = mock_entry

        abort_result = {"type": "abort", "reason": "entity_not_found"}
        handler.async_abort = MagicMock(return_value=abort_result)
        handler.async_show_form = MagicMock(return_value={"type": "form"})
        handler.hass = MagicMock()

        result = asyncio.get_event_loop().run_until_complete(
            handler.async_step_init({"selected_item": "nonexistent"})
        )

        handler.async_abort.assert_called_once_with(reason="entity_not_found")

    def test_options_flow_edit_steps_use_device_assignment_schema(self):
        """Each entity edit step should use device assignment schema (AST check)."""
        import ast
        from pathlib import Path

        config_flow_path = (
            Path(__file__).parent.parent
            / "custom_components"
            / "ads_custom"
            / "config_flow.py"
        )
        with open(config_flow_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())

        edit_steps = [
            "async_step_edit_switch",
            "async_step_edit_sensor",
            "async_step_edit_binary_sensor",
            "async_step_edit_light",
            "async_step_edit_cover",
            "async_step_edit_valve",
            "async_step_edit_select",
        ]

        # Collect all function names in the file
        for step_name in edit_steps:
            func_found = False
            refs_device_schema = False
            for node in ast.walk(tree):
                if (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == step_name
                ):
                    func_found = True
                    for child in ast.walk(node):
                        if isinstance(child, ast.Attribute) and child.attr == "_device_assignment_schema":
                            refs_device_schema = True
                            break
                    break

            assert func_found, f"{step_name} not found in config_flow.py"
            assert refs_device_schema, (
                f"{step_name} should use _device_assignment_schema"
            )
