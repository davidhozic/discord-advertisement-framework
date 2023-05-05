"""
Module used for object conversion.
"""
from typing import Union, List, get_type_hints
from contextlib import suppress

import decimal
import asyncio

import _discord as discord


__all__ = (
    "convert_to_dict",
)

# Only take the following attributes from these types
CONVERSION_ATTR_OVERRIDE = {
    discord.Client: ["_connection", "http"],
    discord.HTTPClient: ["token"],
    discord.state.ConnectionState: ["user"],
    discord.ClientUser: ["display_name"],
    asyncio.Lock: [],
    asyncio.Semaphore: [],
    asyncio.Task: [],
    discord.Guild: ["id"],
}

# Skip the following attributes
CONVERSION_ATTR_SKIP = {"parent"}


def convert_to_dict(object_: object):
    """
    Converts an object into ObjectInfo.

    Parameters
    ---------------
    object_: object
        The object to convert.
    """
    def _convert_json_slots(object_):
        data_conv = {}

        attrs = CONVERSION_ATTR_OVERRIDE.get(
            type(object_),
            object_.__dict__ if hasattr(object_, "__dict__") and len(object_.__dict__) else object_.__slots__
        )
        for k in attrs:
            if k in CONVERSION_ATTR_SKIP:
                continue

            with suppress(Exception):
                value = getattr(object_, k)
                if value is object_:
                    data_conv[k] = value
                else:
                    data_conv[k] = convert_to_dict(value)

        return data_conv

    object_type = type(object_)
    if object_type in {int, float, str, bool, decimal.Decimal, type(None)}:
        if object_type is decimal.Decimal:
            object_ = float(object_)

        return object_

    if isinstance(object_, (set, list, tuple)):
        object_ = [convert_to_dict(value) for value in object_]
        return object_

    return _convert_json_slots(object_)
