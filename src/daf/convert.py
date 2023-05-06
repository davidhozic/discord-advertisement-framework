"""
Module used for object conversion.
"""
from typing import Union
from contextlib import suppress

import decimal
import importlib

import _discord as discord
import asyncio
import array
import datetime as dt

from . import client
from . import guild
from . import message
from .logging import sql


__all__ = (
    "convert_to_dict",
    "update_from_dict"
)

# Only take the following attributes from these types
# _type: {
#     "attrs": type.__slots__,
#     "attrs_restore": {
#         "tasks": [],
#         "_client": lambda account: discord.Client(intents=account.intents),
#         "_update_sem": asyncio.Semaphore(1)
#     },
#     "attrs_convert": {},
# },

LAMBDA_TYPE = type(lambda x: x)
CONVERSION_ATTRS = {
    client.ACCOUNT: {
        "attrs": client.ACCOUNT.__slots__,
        "attrs_restore": {
            "tasks": [],
            "_client": lambda account: discord.Client(intents=account.intents),
            "_update_sem": asyncio.Semaphore(1)
        },
    },
    guild.AutoGUILD: {
        "attrs": guild.AutoGUILD.__slots__,
        "attrs_restore": {
            "_safe_sem": asyncio.Semaphore(1),
            "parent": None,
            "guild_query_iter": None
        },
    },
    message.AutoCHANNEL: {
        "attrs": message.AutoCHANNEL.__slots__,
        "attrs_restore": {
            "parent": None,
        },
    }
}


# Guilds
CONVERSION_ATTRS[guild.GUILD] = {
    "attrs": guild.GUILD.__slots__,
    "attrs_restore": {
        "update_semaphore": asyncio.Semaphore(1),
        "parent": None
    },
    "attrs_convert": {
        "_apiobject": lambda guild: guild._apiobject.id
    },
}

CONVERSION_ATTRS[guild.USER] = CONVERSION_ATTRS[guild.GUILD].copy()
CONVERSION_ATTRS[guild.USER]["attrs"] = guild.USER.__slots__

# Messages
CONVERSION_ATTRS[message.TextMESSAGE] = {
    "attrs": message.TextMESSAGE.__slots__,
    "attrs_restore": {
        "update_semaphore": asyncio.Semaphore(1),
        "parent": None,
        "sent_messages": {}
    },
    "attrs_convert": {
        "channels": lambda message: [(x if isinstance(x, int) else x.id) for x in message.channels]
    },
}

CONVERSION_ATTRS[message.VoiceMESSAGE] = {
    "attrs": message.VoiceMESSAGE.__slots__,
    "attrs_restore": {
        "update_semaphore": asyncio.Semaphore(1),
        "parent": None,
    },
    "attrs_convert": {
        "channels": (
            lambda message_:
                [(x if isinstance(x, int) else x.id) for x in message_.channels] 
                if not isinstance(message_.channels, message.AutoCHANNEL) 
                else message_.channels
        )
    },
}


CONVERSION_ATTRS[message.DirectMESSAGE] = {
    "attrs": message.DirectMESSAGE.__slots__,
    "attrs_restore": {
        "update_semaphore": asyncio.Semaphore(1),
        "parent": None,
        "previous_message": None,
        "dm_channel": None
    },
    "attrs_convert": {
        "channels": lambda message: [(x if isinstance(x, int) else x.id) for x in message.channels]
    },
}


def convert_to_dict(object_: object) -> dict:
    """
    Converts an object into ObjectInfo.

    Parameters
    ---------------
    object_: object
        The object to convert.
    """
    def _convert_json_slots(object_):
        data_conv = {}
        type_object = type(object_)
        attrs = CONVERSION_ATTRS.get(type_object)
        if attrs is None:
            return object_  # Keep as it is

        (
            attrs,
            attrs_restore,
            attrs_convert,
            skip
        ) = (
            attrs["attrs"],
            attrs.get("attrs_restore", {}),
            attrs.get("attrs_convert", {}),
            attrs.get("skip", [])
        )
        for k in attrs:
            # Manually set during restored or is a class attribute
            if k in attrs_restore or k in skip:
                continue

            if k in attrs_convert:
                value = attrs_convert[k]
                if isinstance(value, LAMBDA_TYPE):
                    value = value(object_)
            else:
                value = getattr(object_, k)

            try:
                data_conv[k] = convert_to_dict(value)
            except NotImplementedError:
                continue  # This attr is to be skipped

        return {"object_type": f"{type_object.__module__}.{type_object.__name__}", "data": data_conv}

    def _convert_json_dict(object_: dict):
        data_conv = {}
        for k, v in object_.items():
            try:
                data_conv[k] = convert_to_dict(v)
            except NotImplementedError:
                continue  # This attr is to be skipped

        return data_conv

    object_type = type(object_)
    if object_type in {int, float, str, bool, decimal.Decimal, type(None)}:
        if object_type is decimal.Decimal:
            object_ = float(object_)

        return object_

    if isinstance(object_, (set, list, tuple)):
        try:
            object_ = [convert_to_dict(value) for value in object_]
            return object_
        except NotImplementedError:
            return []

    if isinstance(object_, dict):
        return _convert_json_dict(object_)

    return _convert_json_slots(object_)


def update_from_dict(d: Union[dict, list]):
    """

    Parameters
    ---------------
    object_: object
        The object to convert.
    """
    if isinstance(d, list):
        _return = []
        for value in d:
            _return.append(update_from_dict(value) if isinstance(value, dict) else value)

        return _return

    if "object_type" not in d:  # It's a normal dictionary
        return d

    path = d["object_type"].split(".")
    module_path, class_name = '.'.join(path[:-1]), path[-1]
    module = importlib.import_module(module_path)
    class_ = getattr(module, class_name)

    try:
        if issubclass(class_, array.array):
            _return = array.array.__new__(class_, 'Q')
        else:
            _return = object.__new__(class_)

        for k, v in d["data"].items():
            if isinstance(v, (dict, list)):
                v = update_from_dict(v)

            with suppress(Exception):
                setattr(_return, k, v)

        return _return
    except Exception as exc:
        return None
