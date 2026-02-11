"""Tests for the ADS Cover platform opening/closing state detection."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pyads

from custom_components.ads_custom.cover import (
    AdsCover,
    STATE_KEY_POSITION,
    STATE_KEY_PREV_POSITION,
    _MOVEMENT_TIMEOUT,
)


def _make_cover(
    ads_var_position: str | None = None,
    ads_var_position_type: str = "byte",
    inverted: bool = False,
    ads_var_stop: str | None = None,
) -> tuple[AdsCover, MagicMock]:
    """Create an AdsCover with a mock hub, returning (cover, hub_mock)."""
    hub = MagicMock()
    cover = AdsCover(
        ads_hub=hub,
        ads_var_closed_state=None,
        ads_var_position=ads_var_position,
        ads_var_position_type=ads_var_position_type,
        ads_var_pos_set="GVL.cover_set_pos",
        ads_var_open="GVL.cover_open",
        ads_var_close="GVL.cover_close",
        ads_var_stop=ads_var_stop,
        inverted=inverted,
        name="Test Cover",
        device_class=None,
        unique_id="test_cover_1",
    )
    return cover, hub


class TestAdsCoverOpeningClosingStates:
    """Tests for AdsCover is_opening and is_closing properties."""

    def test_is_opening_none_without_position_var(self):
        """is_opening should be None if no position variable is configured."""
        cover, _ = _make_cover(ads_var_position=None)
        assert cover.is_opening is None

    def test_is_closing_none_without_position_var(self):
        """is_closing should be None if no position variable is configured."""
        cover, _ = _make_cover(ads_var_position=None)
        assert cover.is_closing is None

    def test_is_opening_none_without_prev_position(self):
        """is_opening should be None if previous position is not available."""
        cover, _ = _make_cover(ads_var_position="GVL.position")
        cover._state_dict[STATE_KEY_POSITION] = 50
        cover._state_dict[STATE_KEY_PREV_POSITION] = None
        assert cover.is_opening is None

    def test_is_closing_none_without_prev_position(self):
        """is_closing should be None if previous position is not available."""
        cover, _ = _make_cover(ads_var_position="GVL.position")
        cover._state_dict[STATE_KEY_POSITION] = 50
        cover._state_dict[STATE_KEY_PREV_POSITION] = None
        assert cover.is_closing is None

    def test_is_opening_true_normal_mode(self):
        """is_opening should be True when position is increasing (normal mode)."""
        cover, _ = _make_cover(ads_var_position="GVL.position", inverted=False)
        cover._state_dict[STATE_KEY_PREV_POSITION] = 30
        cover._state_dict[STATE_KEY_POSITION] = 50
        assert cover.is_opening is True
        assert cover.is_closing is False

    def test_is_closing_true_normal_mode(self):
        """is_closing should be True when position is decreasing (normal mode)."""
        cover, _ = _make_cover(ads_var_position="GVL.position", inverted=False)
        cover._state_dict[STATE_KEY_PREV_POSITION] = 70
        cover._state_dict[STATE_KEY_POSITION] = 40
        assert cover.is_closing is True
        assert cover.is_opening is False

    def test_is_opening_true_inverted_mode(self):
        """is_opening should be True when position is decreasing toward 0 (inverted mode)."""
        cover, _ = _make_cover(ads_var_position="GVL.position", inverted=True)
        cover._state_dict[STATE_KEY_PREV_POSITION] = 70
        cover._state_dict[STATE_KEY_POSITION] = 40
        assert cover.is_opening is True
        assert cover.is_closing is False

    def test_is_closing_true_inverted_mode(self):
        """is_closing should be True when position is increasing toward 100 (inverted mode)."""
        cover, _ = _make_cover(ads_var_position="GVL.position", inverted=True)
        cover._state_dict[STATE_KEY_PREV_POSITION] = 30
        cover._state_dict[STATE_KEY_POSITION] = 60
        assert cover.is_closing is True
        assert cover.is_opening is False

    def test_neither_opening_nor_closing_when_stopped(self):
        """Both should be False when position hasn't changed."""
        cover, _ = _make_cover(ads_var_position="GVL.position", inverted=False)
        cover._state_dict[STATE_KEY_PREV_POSITION] = 50
        cover._state_dict[STATE_KEY_POSITION] = 50
        assert cover.is_opening is False
        assert cover.is_closing is False

    def test_not_closing_when_fully_closed_normal_mode(self):
        """is_closing should be False when cover reaches position 0 (normal mode)."""
        cover, _ = _make_cover(ads_var_position="GVL.position", inverted=False)
        cover._state_dict[STATE_KEY_PREV_POSITION] = 5
        cover._state_dict[STATE_KEY_POSITION] = 0
        assert cover.is_closing is False
        assert cover.is_closed is True

    def test_not_opening_when_fully_open_normal_mode(self):
        """is_opening should be False when cover reaches position 100 (normal mode)."""
        cover, _ = _make_cover(ads_var_position="GVL.position", inverted=False)
        cover._state_dict[STATE_KEY_PREV_POSITION] = 95
        cover._state_dict[STATE_KEY_POSITION] = 100
        assert cover.is_opening is False
        assert cover.is_closed is False

    def test_not_closing_when_fully_closed_inverted_mode(self):
        """is_closing should be False when cover reaches position 100 (inverted mode)."""
        cover, _ = _make_cover(ads_var_position="GVL.position", inverted=True)
        cover._state_dict[STATE_KEY_PREV_POSITION] = 95
        cover._state_dict[STATE_KEY_POSITION] = 100
        assert cover.is_closing is False
        assert cover.is_closed is True

    def test_not_opening_when_fully_open_inverted_mode(self):
        """is_opening should be False when cover reaches position 0 (inverted mode)."""
        cover, _ = _make_cover(ads_var_position="GVL.position", inverted=True)
        cover._state_dict[STATE_KEY_PREV_POSITION] = 5
        cover._state_dict[STATE_KEY_POSITION] = 0
        assert cover.is_opening is False
        assert cover.is_closed is False


class TestAdsCoverPositionProperties:
    """Tests for AdsCover position-related properties."""

    def test_current_cover_position_normal_mode(self):
        """current_cover_position should return position as-is in normal mode."""
        cover, _ = _make_cover(ads_var_position="GVL.position", inverted=False)
        cover._state_dict[STATE_KEY_POSITION] = 75
        assert cover.current_cover_position == 75

    def test_current_cover_position_inverted_mode(self):
        """current_cover_position should invert position in inverted mode."""
        cover, _ = _make_cover(ads_var_position="GVL.position", inverted=True)
        cover._state_dict[STATE_KEY_POSITION] = 75
        assert cover.current_cover_position == 25

    def test_is_closed_normal_mode(self):
        """is_closed should be True when position is 0 in normal mode."""
        cover, _ = _make_cover(ads_var_position="GVL.position", inverted=False)
        cover._state_dict[STATE_KEY_POSITION] = 0
        assert cover.is_closed is True

    def test_is_closed_inverted_mode(self):
        """is_closed should be True when position is 100 in inverted mode."""
        cover, _ = _make_cover(ads_var_position="GVL.position", inverted=True)
        cover._state_dict[STATE_KEY_POSITION] = 100
        assert cover.is_closed is True

    def test_is_not_closed_normal_mode(self):
        """is_closed should be False when position is not 0 in normal mode."""
        cover, _ = _make_cover(ads_var_position="GVL.position", inverted=False)
        cover._state_dict[STATE_KEY_POSITION] = 50
        assert cover.is_closed is False

    def test_is_not_closed_inverted_mode(self):
        """is_closed should be False when position is not 100 in inverted mode."""
        cover, _ = _make_cover(ads_var_position="GVL.position", inverted=True)
        cover._state_dict[STATE_KEY_POSITION] = 50
        assert cover.is_closed is False


class TestAdsCoverActions:
    """Tests for AdsCover action methods."""

    def test_set_cover_position_normal_mode(self):
        """set_cover_position should write position as-is in normal mode."""
        cover, hub = _make_cover(ads_var_position="GVL.position", inverted=False)
        cover.set_cover_position(position=75)
        hub.write_by_name.assert_called_once_with(
            "GVL.cover_set_pos", 75, pyads.PLCTYPE_BYTE
        )

    def test_set_cover_position_inverted_mode(self):
        """set_cover_position should invert position in inverted mode."""
        cover, hub = _make_cover(ads_var_position="GVL.position", inverted=True)
        cover.set_cover_position(position=75)
        hub.write_by_name.assert_called_once_with(
            "GVL.cover_set_pos", 25, pyads.PLCTYPE_BYTE
        )

    def test_open_cover_writes_true(self):
        """open_cover should write True to the open variable."""
        cover, hub = _make_cover(ads_var_position="GVL.position")
        cover.open_cover()
        hub.write_by_name.assert_any_call("GVL.cover_open", True, pyads.PLCTYPE_BOOL)

    def test_close_cover_writes_true(self):
        """close_cover should write True to the close variable."""
        cover, hub = _make_cover(ads_var_position="GVL.position")
        cover.close_cover()
        hub.write_by_name.assert_any_call("GVL.cover_close", True, pyads.PLCTYPE_BOOL)

    def test_stop_cover_resets_movement_state(self):
        """stop_cover should reset prev_position so is_opening/is_closing return False."""
        cover, hub = _make_cover(
            ads_var_position="GVL.position", ads_var_stop="GVL.cover_stop"
        )
        cover._state_dict[STATE_KEY_PREV_POSITION] = 30
        cover._state_dict[STATE_KEY_POSITION] = 50
        # Cover appears to be opening
        assert cover.is_opening is True
        # Stop the cover
        cover.stop_cover()
        # After stop, prev_position == current_position → not moving
        assert cover.is_opening is False
        assert cover.is_closing is False


class TestAdsCoverMovementTimeout:
    """Tests for movement timeout detection at intermediate positions."""

    def test_is_opening_false_after_timeout(self):
        """is_opening should be False when no position update arrives within timeout."""
        cover, _ = _make_cover(ads_var_position="GVL.position", inverted=False)
        cover._state_dict[STATE_KEY_PREV_POSITION] = 30
        cover._state_dict[STATE_KEY_POSITION] = 50
        # Simulate position update that happened long ago
        cover._position_last_updated = 0.0
        with patch("custom_components.ads_custom.cover.time") as mock_time:
            mock_time.monotonic.return_value = _MOVEMENT_TIMEOUT + 1.0
            assert cover.is_opening is False

    def test_is_closing_false_after_timeout(self):
        """is_closing should be False when no position update arrives within timeout."""
        cover, _ = _make_cover(ads_var_position="GVL.position", inverted=False)
        cover._state_dict[STATE_KEY_PREV_POSITION] = 70
        cover._state_dict[STATE_KEY_POSITION] = 50
        # Simulate position update that happened long ago
        cover._position_last_updated = 0.0
        with patch("custom_components.ads_custom.cover.time") as mock_time:
            mock_time.monotonic.return_value = _MOVEMENT_TIMEOUT + 1.0
            assert cover.is_closing is False

    def test_is_opening_true_within_timeout(self):
        """is_opening should still be True when position update is recent."""
        cover, _ = _make_cover(ads_var_position="GVL.position", inverted=False)
        cover._state_dict[STATE_KEY_PREV_POSITION] = 30
        cover._state_dict[STATE_KEY_POSITION] = 50
        # Simulate recent position update
        cover._position_last_updated = 100.0
        with patch("custom_components.ads_custom.cover.time") as mock_time:
            mock_time.monotonic.return_value = 100.5  # 0.5s < timeout
            assert cover.is_opening is True

    def test_timeout_not_triggered_without_timestamp(self):
        """Timeout should not trigger if no position update timestamp exists."""
        cover, _ = _make_cover(ads_var_position="GVL.position", inverted=False)
        cover._state_dict[STATE_KEY_PREV_POSITION] = 30
        cover._state_dict[STATE_KEY_POSITION] = 50
        cover._position_last_updated = None
        # Without timestamp, should still report opening based on direction
        assert cover.is_opening is True
