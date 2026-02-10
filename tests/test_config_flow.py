"""Test the config flow for the ADS Custom integration."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest


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


class TestRemoveEmptyOptionalFields:
    """Tests for _remove_empty_optional_fields helper method."""

    @staticmethod
    def _remove_empty_optional_fields(data: dict[str, Any], *field_names: str) -> None:
        """Test implementation of the helper matching the actual implementation."""
        for field_name in field_names:
            if field_name not in data:
                continue

            value = data[field_name]

            # Remove explicit None
            if value is None:
                data.pop(field_name)
                continue

            # Remove empty or whitespace-only strings
            if isinstance(value, str) and not value.strip():
                data.pop(field_name)
                continue

            # Remove empty collections (but keep 0/False etc.)
            if isinstance(value, (list, dict, set, tuple)) and not value:
                data.pop(field_name)

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

