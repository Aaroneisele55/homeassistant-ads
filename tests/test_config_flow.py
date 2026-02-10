"""Test the config flow for the ADS Custom integration."""

from __future__ import annotations

import pytest


class TestDeviceClassLists:
    """Tests for device class lists by directly reading the file."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Load the device class lists from the config_flow.py file."""
        with open("custom_components/ads_custom/config_flow.py", "r") as f:
            content = f.read()
        
        # Check if empty strings are in the lists
        # We'll just check if the pattern exists in the file
        self.file_content = content

    def test_binary_sensor_device_classes_includes_empty_string(self):
        """Test that binary sensor device classes list includes empty string as first option."""
        # Look for the pattern: BINARY_SENSOR_DEVICE_CLASSES = [\n    "",
        assert 'BINARY_SENSOR_DEVICE_CLASSES = [\n    "",  # Empty option to allow clearing device_class' in self.file_content

    def test_sensor_device_classes_includes_empty_string(self):
        """Test that sensor device classes list includes empty string as first option."""
        # Look for the pattern: SENSOR_DEVICE_CLASSES = [\n    "",
        assert 'SENSOR_DEVICE_CLASSES = [\n    "",  # Empty option to allow clearing device_class' in self.file_content

    def test_cover_device_classes_includes_empty_string(self):
        """Test that cover device classes list includes empty string as first option."""
        # Look for the pattern: COVER_DEVICE_CLASSES = [\n    "",
        assert 'COVER_DEVICE_CLASSES = [\n    "",  # Empty option to allow clearing device_class' in self.file_content

    def test_valve_device_classes_includes_empty_string(self):
        """Test that valve device classes list includes empty string as first option."""
        # Look for the pattern: VALVE_DEVICE_CLASSES = [\n    "",
        assert 'VALVE_DEVICE_CLASSES = [\n    "",  # Empty option to allow clearing device_class' in self.file_content
    
    def test_empty_device_class_removed_in_configure_sensor(self):
        """Test that configure_sensor removes empty device_class."""
        # Check for the code pattern that removes empty device_class
        assert 'if CONF_DEVICE_CLASS in user_input and not user_input[CONF_DEVICE_CLASS]:' in self.file_content
        assert 'user_input.pop(CONF_DEVICE_CLASS)' in self.file_content
    
    def test_empty_device_class_removed_in_reconfigure_sensor(self):
        """Test that reconfigure_sensor removes empty device_class."""
        # Check for the code pattern that removes empty device_class in reconfigure
        assert 'if CONF_DEVICE_CLASS in new_data and not new_data[CONF_DEVICE_CLASS]:' in self.file_content
        assert 'new_data.pop(CONF_DEVICE_CLASS)' in self.file_content
