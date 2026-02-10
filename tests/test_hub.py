"""Tests for the ADS Hub module."""

from __future__ import annotations

import ctypes
import struct
from unittest.mock import MagicMock, call, patch

import pyads
import pytest

from custom_components.ads_custom.hub import AdsHub, NotificationItem


# ---------------------------------------------------------------------------
# Construction / lifecycle
# ---------------------------------------------------------------------------

class TestAdsHubLifecycle:
    """Tests for AdsHub construction and shutdown."""

    def test_constructor_opens_connection(self, mock_ads_client):
        """AdsHub.__init__ must call client.open()."""
        hub = AdsHub(mock_ads_client)
        mock_ads_client.open.assert_called_once()

    def test_shutdown_closes_connection(self, ads_hub, mock_ads_client):
        """shutdown() must call client.close()."""
        ads_hub.shutdown()
        mock_ads_client.close.assert_called_once()

    def test_shutdown_deletes_notifications(self, ads_hub, mock_ads_client):
        """shutdown() must delete all registered device notifications."""
        cb = MagicMock()
        ads_hub.add_device_notification("GVL.var1", pyads.PLCTYPE_BOOL, cb)
        mock_ads_client.add_device_notification.return_value = (2, 2)
        ads_hub.add_device_notification("GVL.var2", pyads.PLCTYPE_INT, cb)

        ads_hub.shutdown()

        assert mock_ads_client.del_device_notification.call_count == 2

    def test_shutdown_handles_ads_error_on_close(self, ads_hub, mock_ads_client):
        """shutdown() should not raise even if close() throws ADSError."""
        mock_ads_client.close.side_effect = pyads.ADSError()
        ads_hub.shutdown()  # must not raise

    def test_shutdown_handles_ads_error_on_del_notification(
        self, ads_hub, mock_ads_client
    ):
        """shutdown() should not raise if del_device_notification throws."""
        cb = MagicMock()
        ads_hub.add_device_notification("GVL.var", pyads.PLCTYPE_BOOL, cb)
        mock_ads_client.del_device_notification.side_effect = pyads.ADSError()

        ads_hub.shutdown()  # must not raise


# ---------------------------------------------------------------------------
# Device registration
# ---------------------------------------------------------------------------

class TestDeviceRegistration:
    """Tests for register_device."""

    def test_register_device_appends(self, ads_hub):
        """register_device should add a device to the internal list."""
        device = MagicMock()
        ads_hub.register_device(device)
        assert device in ads_hub._devices


# ---------------------------------------------------------------------------
# Read / Write
# ---------------------------------------------------------------------------

class TestReadWrite:
    """Tests for read_by_name and write_by_name."""

    def test_write_by_name_delegates(self, ads_hub, mock_ads_client):
        """write_by_name should forward the call to the underlying client."""
        ads_hub.write_by_name("GVL.motor", True, pyads.PLCTYPE_BOOL)
        mock_ads_client.write_by_name.assert_called_once_with(
            "GVL.motor", True, pyads.PLCTYPE_BOOL
        )

    def test_read_by_name_delegates(self, ads_hub, mock_ads_client):
        """read_by_name should forward the call to the underlying client."""
        mock_ads_client.read_by_name.return_value = 42
        result = ads_hub.read_by_name("GVL.counter", pyads.PLCTYPE_INT)
        assert result == 42
        mock_ads_client.read_by_name.assert_called_once_with(
            "GVL.counter", pyads.PLCTYPE_INT
        )

    def test_write_by_name_handles_ads_error(self, ads_hub, mock_ads_client):
        """write_by_name should catch ADSError and not raise."""
        mock_ads_client.write_by_name.side_effect = pyads.ADSError()
        ads_hub.write_by_name("GVL.x", 1, pyads.PLCTYPE_INT)  # must not raise

    def test_read_by_name_handles_ads_error(self, ads_hub, mock_ads_client):
        """read_by_name should catch ADSError and return None."""
        mock_ads_client.read_by_name.side_effect = pyads.ADSError()
        result = ads_hub.read_by_name("GVL.x", pyads.PLCTYPE_INT)
        assert result is None


# ---------------------------------------------------------------------------
# Device notification registration
# ---------------------------------------------------------------------------

class TestAddDeviceNotification:
    """Tests for add_device_notification."""

    def test_add_notification_registers(self, ads_hub, mock_ads_client):
        """After adding a notification, it should be stored internally."""
        cb = MagicMock()
        ads_hub.add_device_notification("GVL.var", pyads.PLCTYPE_BOOL, cb)

        # The handle returned by mock is (1, 1)
        assert 1 in ads_hub._notification_items
        item = ads_hub._notification_items[1]
        assert item.name == "GVL.var"
        assert item.callback is cb

    def test_add_notification_handles_ads_error(self, ads_hub, mock_ads_client):
        """add_device_notification should catch ADSError and not raise."""
        mock_ads_client.add_device_notification.side_effect = pyads.ADSError()
        ads_hub.add_device_notification(
            "GVL.x", pyads.PLCTYPE_BOOL, MagicMock()
        )  # must not raise


# ---------------------------------------------------------------------------
# Notification callback data parsing
# ---------------------------------------------------------------------------

def _make_notification(hnotify: int, data: bytes):
    """Build a fake SAdsNotificationHeader-like ctypes structure.

    Layout (from pyads):
        hNotification  : c_uint   (4 bytes)
        nTimeStamp     : c_ulong  (8 bytes on 64-bit)
        cbSampleSize   : c_uint   (4 bytes)
        data           : c_ubyte  (start of variable-length payload)

    We reconstruct the full buffer so that the hub's callback can read it
    via `from_address`.
    """
    data_offset = pyads.structs.SAdsNotificationHeader.data.offset

    buf_size = data_offset + len(data)
    buf = (ctypes.c_ubyte * buf_size)()

    # hNotification (uint32 LE at offset 0)
    struct.pack_into("<I", buf, 0, hnotify)
    # nTimeStamp (ulong LE at offset 4) — leave as zero
    # cbSampleSize (uint32 LE)
    sample_size_offset = data_offset - ctypes.sizeof(ctypes.c_uint)
    struct.pack_into("<I", buf, sample_size_offset, len(data))
    # payload
    for i, b in enumerate(data):
        buf[data_offset + i] = b

    # Wrap in a mock that exposes .contents
    header = pyads.structs.SAdsNotificationHeader.from_address(
        ctypes.addressof(buf)
    )

    class _NotifWrap:
        contents = header

    return _NotifWrap(), buf  # return buf to keep it alive


class TestNotificationCallback:
    """Tests for _device_notification_callback data parsing."""

    def _register_and_fire(self, ads_hub, plc_datatype, data_bytes):
        """Register a notification, then fire a fake callback."""
        cb = MagicMock()
        ads_hub.add_device_notification("GVL.test", plc_datatype, cb)
        hnotify = 1  # default handle from mock

        notif, _buf = _make_notification(hnotify, data_bytes)
        ads_hub._device_notification_callback(notif, "GVL.test")
        return cb

    def test_bool_true(self, ads_hub):
        """BOOL notification with value True."""
        data = struct.pack("<?", True)
        cb = self._register_and_fire(ads_hub, pyads.PLCTYPE_BOOL, data)
        cb.assert_called_once_with("GVL.test", True)

    def test_bool_false(self, ads_hub):
        """BOOL notification with value False."""
        data = struct.pack("<?", False)
        cb = self._register_and_fire(ads_hub, pyads.PLCTYPE_BOOL, data)
        cb.assert_called_once_with("GVL.test", False)

    def test_int_value(self, ads_hub):
        """INT (signed 16-bit) notification."""
        data = struct.pack("<h", -123)
        cb = self._register_and_fire(ads_hub, pyads.PLCTYPE_INT, data)
        cb.assert_called_once_with("GVL.test", -123)

    def test_uint_value(self, ads_hub):
        """UINT (unsigned 16-bit) notification."""
        data = struct.pack("<H", 65535)
        cb = self._register_and_fire(ads_hub, pyads.PLCTYPE_UINT, data)
        cb.assert_called_once_with("GVL.test", 65535)

    def test_dint_value(self, ads_hub):
        """DINT (signed 32-bit) notification."""
        data = struct.pack("<i", -100000)
        cb = self._register_and_fire(ads_hub, pyads.PLCTYPE_DINT, data)
        cb.assert_called_once_with("GVL.test", -100000)

    def test_udint_value(self, ads_hub):
        """UDINT (unsigned 32-bit) notification.

        Note: In hub.py ``_device_notification_callback``, the
        ``unpack_formats`` dict maps several pyads PLC types that share the
        same ``ctypes.c_uint`` identity (UDINT, DWORD, DATE, DT, TIME).
        Because TIME is listed last with format ``"<i"`` (signed), it
        overwrites the unsigned ``"<I"`` for UDINT/DWORD.  We test with a
        value that fits in both signed and unsigned 32-bit range.
        """
        data = struct.pack("<I", 100)
        cb = self._register_and_fire(ads_hub, pyads.PLCTYPE_UDINT, data)
        cb.assert_called_once_with("GVL.test", 100)

    def test_real_value(self, ads_hub):
        """REAL (32-bit float) notification."""
        data = struct.pack("<f", 3.14)
        cb = self._register_and_fire(ads_hub, pyads.PLCTYPE_REAL, data)
        name, value = cb.call_args[0]
        assert name == "GVL.test"
        assert abs(value - 3.14) < 1e-5

    def test_lreal_value(self, ads_hub):
        """LREAL (64-bit double) notification."""
        data = struct.pack("<d", 2.718281828)
        cb = self._register_and_fire(ads_hub, pyads.PLCTYPE_LREAL, data)
        name, value = cb.call_args[0]
        assert name == "GVL.test"
        assert abs(value - 2.718281828) < 1e-9

    def test_string_value(self, ads_hub):
        """STRING notification (null-terminated)."""
        data = b"Hello\x00World"
        cb = self._register_and_fire(ads_hub, pyads.PLCTYPE_STRING, data)
        cb.assert_called_once_with("GVL.test", "Hello")

    def test_byte_value(self, ads_hub):
        """BYTE (unsigned 8-bit) notification."""
        data = struct.pack("<B", 200)
        cb = self._register_and_fire(ads_hub, pyads.PLCTYPE_BYTE, data)
        cb.assert_called_once_with("GVL.test", 200)

    def test_sint_value(self, ads_hub):
        """SINT (signed 8-bit) notification."""
        data = struct.pack("<b", -50)
        cb = self._register_and_fire(ads_hub, pyads.PLCTYPE_SINT, data)
        cb.assert_called_once_with("GVL.test", -50)

    def test_usint_value(self, ads_hub):
        """USINT (unsigned 8-bit) notification."""
        data = struct.pack("<B", 250)
        cb = self._register_and_fire(ads_hub, pyads.PLCTYPE_USINT, data)
        cb.assert_called_once_with("GVL.test", 250)

    def test_word_value(self, ads_hub):
        """WORD (unsigned 16-bit) notification."""
        data = struct.pack("<H", 0xABCD)
        cb = self._register_and_fire(ads_hub, pyads.PLCTYPE_WORD, data)
        cb.assert_called_once_with("GVL.test", 0xABCD)

    def test_dword_value(self, ads_hub):
        """DWORD (unsigned 32-bit) notification.

        Same ``unpack_formats`` dict-key collision as UDINT; see
        ``test_udint_value`` for details.  Uses a small value that is
        identical in both signed and unsigned representation.
        """
        data = struct.pack("<I", 42)
        cb = self._register_and_fire(ads_hub, pyads.PLCTYPE_DWORD, data)
        cb.assert_called_once_with("GVL.test", 42)

    def test_unknown_hnotify_logged(self, ads_hub):
        """Callback with unknown handle should not raise."""
        notif, _buf = _make_notification(999, b"\x00")
        ads_hub._device_notification_callback(notif, "GVL.test")  # must not raise

    def test_time_value(self, ads_hub):
        """TIME (DINT milliseconds) notification."""
        data = struct.pack("<i", 5000)
        cb = self._register_and_fire(ads_hub, pyads.PLCTYPE_TIME, data)
        cb.assert_called_once_with("GVL.test", 5000)

    def test_date_value(self, ads_hub):
        """DATE (DINT seconds since epoch) notification."""
        data = struct.pack("<i", 1609459200)
        cb = self._register_and_fire(ads_hub, pyads.PLCTYPE_DATE, data)
        cb.assert_called_once_with("GVL.test", 1609459200)
