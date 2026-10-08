"""Support for Automation Device Specification (ADS)."""

from __future__ import annotations

from collections import namedtuple
import ctypes
import logging
import struct
import threading

import pyads

_LOGGER = logging.getLogger(__name__)

# Tuple to hold data needed for notification
NotificationItem = namedtuple(  # noqa: PYI024
    "NotificationItem", "hnotify huser name plc_datatype callback subscription_id"
)


class AdsHub:
    """Representation of an ADS connection."""

    def __init__(self, ads_client):
        """Initialize the ADS hub."""
        self._client = ads_client
        self._client.open()

        # All ADS devices are registered here
        self._devices = []
        self._notification_items = {}
        self._notification_subscriptions = {}
        self._next_subscription_id = 1
        self._lock = threading.Lock()

    def shutdown(self, *args, **kwargs):
        """Shutdown ADS connection."""

        _LOGGER.debug("Shutting down ADS")
        for notification_item in self._notification_items.values():
            _LOGGER.debug(
                "Deleting device notification %d, %d",
                notification_item.hnotify,
                notification_item.huser,
            )
            try:
                self._client.del_device_notification(
                    notification_item.hnotify, notification_item.huser
                )
            except pyads.ADSError as err:
                _LOGGER.error(err)
        try:
            self._client.close()
        except pyads.ADSError as err:
            _LOGGER.error(err)

    def _register_notification_locked(
        self, subscription_id, name, plc_datatype, callback
    ):
        """Register a notification while lock is held."""
        attr = pyads.NotificationAttrib(ctypes.sizeof(plc_datatype))
        hnotify, huser = self._client.add_device_notification(
            name, attr, self._device_notification_callback
        )
        hnotify = int(hnotify)
        self._notification_items[hnotify] = NotificationItem(
            hnotify, huser, name, plc_datatype, callback, subscription_id
        )
        _LOGGER.debug("Added device notification %d for variable %s", hnotify, name)

    def _reconnect_locked(self):
        """Reconnect ADS client and restore notifications while lock is held."""
        _LOGGER.warning("ADS connection lost; attempting reconnect")
        try:
            self._client.close()
        except pyads.ADSError as err:
            _LOGGER.debug("Error closing ADS connection during reconnect: %s", err)

        try:
            self._client.open()
        except pyads.ADSError as err:
            _LOGGER.error("Failed to reconnect ADS client: %s", err)
            return False

        self._notification_items.clear()
        for (
            subscription_id,
            (name, plc_datatype, callback),
        ) in self._notification_subscriptions.items():
            try:
                self._register_notification_locked(
                    subscription_id, name, plc_datatype, callback
                )
            except pyads.ADSError as err:
                _LOGGER.error(
                    "Error restoring notification for %s after reconnect: %s",
                    name,
                    err,
                )
        _LOGGER.info(
            "ADS reconnect succeeded; restored %d notification subscriptions",
            len(self._notification_items),
        )
        return True

    def register_device(self, device):
        """Register a new device."""
        self._devices.append(device)

    def write_by_name(self, name, value, plc_datatype):
        """Write a value to the device."""

        with self._lock:
            try:
                return self._client.write_by_name(name, value, plc_datatype)
            except pyads.ADSError as err:
                _LOGGER.error("Error writing %s: %s", name, err)
                if not self._reconnect_locked():
                    return None
                try:
                    return self._client.write_by_name(name, value, plc_datatype)
                except pyads.ADSError as retry_err:
                    _LOGGER.error(
                        "Error writing %s after ADS reconnect: %s", name, retry_err
                    )
                    return None

    def read_by_name(self, name, plc_datatype):
        """Read a value from the device."""

        with self._lock:
            try:
                return self._client.read_by_name(name, plc_datatype)
            except pyads.ADSError as err:
                _LOGGER.error("Error reading %s: %s", name, err)
                if not self._reconnect_locked():
                    return None
                try:
                    return self._client.read_by_name(name, plc_datatype)
                except pyads.ADSError as retry_err:
                    _LOGGER.error(
                        "Error reading %s after ADS reconnect: %s", name, retry_err
                    )
                    return None

    def add_device_notification(self, name, plc_datatype, callback):
        """Add a notification to the ADS devices."""

        with self._lock:
            subscription_id = self._next_subscription_id
            self._next_subscription_id += 1
            self._notification_subscriptions[subscription_id] = (
                name,
                plc_datatype,
                callback,
            )
            try:
                self._register_notification_locked(
                    subscription_id, name, plc_datatype, callback
                )
            except pyads.ADSError as err:
                _LOGGER.error("Error subscribing to %s: %s", name, err)
                self._reconnect_locked()

    def _device_notification_callback(self, notification, name):
        """Handle device notifications."""
        contents = notification.contents
        hnotify = int(contents.hNotification)
        _LOGGER.debug("Received notification %d", hnotify)

        # Get dynamically sized data array
        data_size = contents.cbSampleSize
        data_address = (
            ctypes.addressof(contents)
            + pyads.structs.SAdsNotificationHeader.data.offset
        )
        data = (ctypes.c_ubyte * data_size).from_address(data_address)

        # Acquire notification item
        with self._lock:
            notification_item = self._notification_items.get(hnotify)

        if not notification_item:
            _LOGGER.error("Unknown device notification handle: %d", hnotify)
            return

        # Data parsing based on PLC data type
        plc_datatype = notification_item.plc_datatype
        unpack_formats = {
            pyads.PLCTYPE_BYTE: "<B",  # BYTE is unsigned (0-255)
            pyads.PLCTYPE_INT: "<h",
            pyads.PLCTYPE_UINT: "<H",
            pyads.PLCTYPE_SINT: "<b",  # SINT is signed (-128 to 127)
            pyads.PLCTYPE_USINT: "<B",
            pyads.PLCTYPE_DINT: "<i",
            pyads.PLCTYPE_UDINT: "<I",
            pyads.PLCTYPE_WORD: "<H",
            pyads.PLCTYPE_DWORD: "<I",
            pyads.PLCTYPE_LREAL: "<d",
            pyads.PLCTYPE_REAL: "<f",
            pyads.PLCTYPE_TOD: "<i",  # Treat as DINT
            pyads.PLCTYPE_DATE: "<i",  # Treat as DINT
            pyads.PLCTYPE_DT: "<i",  # Treat as DINT
            pyads.PLCTYPE_TIME: "<i",  # Treat as DINT
        }

        if plc_datatype == pyads.PLCTYPE_BOOL:
            value = bool(struct.unpack("<?", bytearray(data))[0])
        elif plc_datatype == pyads.PLCTYPE_STRING:
            value = (
                bytearray(data).split(b"\x00", 1)[0].decode("utf-8", errors="ignore")
            )
        elif plc_datatype in unpack_formats:
            value = struct.unpack(unpack_formats[plc_datatype], bytearray(data))[0]
        else:
            value = bytearray(data)
            _LOGGER.warning("No callback available for this datatype")

        notification_item.callback(notification_item.name, value)
