"""Support for Automation Device Specification (ADS)."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from homeassistant.util.hass_dict import HassKey

if TYPE_CHECKING:
    from .hub import AdsHub

DOMAIN = "ads_custom"

CONF_ADS_VAR = "adsvar"

SUBENTRY_TYPE_ENTITY = "entity"

# All entities live under a single subentry per hub, identified by this
# fixed unique_id. Individual entities are distinguished by their own
# "unique_id" field within that subentry's "entities" list, and are grouped
# into different devices via the per-entity CONF_ENTITY_DEVICE_ID field.
SINGLE_SUBENTRY_UNIQUE_ID = "entities"
SINGLE_SUBENTRY_TITLE = "Entities"

STATE_KEY_STATE = "state"

# Entity option configuration keys
CONF_ENTITY_ICON = "icon"
CONF_ENTITY_CATEGORY = "entity_category"
CONF_ENTITY_PICTURE = "entity_picture"
CONF_ENTITY_DEVICE_ID = "entity_device_id"
CONF_ENTITY_DEVICE_NAME = "entity_device_name"


class AdsType(StrEnum):
    """Supported Types."""

    BOOL = "bool"
    BYTE = "byte"
    INT = "int"
    UINT = "uint"
    SINT = "sint"
    USINT = "usint"
    DINT = "dint"
    UDINT = "udint"
    WORD = "word"
    DWORD = "dword"
    LREAL = "lreal"
    REAL = "real"
    STRING = "string"
    TIME = "time"
    DATE = "date"
    DATE_AND_TIME = "dt"
    TOD = "tod"
