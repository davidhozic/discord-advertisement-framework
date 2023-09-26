"""
The conversion module is responsible for converting Python objects into different forms.
It is also responsible for doing the reverse, which is converting those other forms back into Python objects.
"""

from typing import Union, Any, Mapping
from contextlib import suppress
from enum import Enum
from inspect import isclass, signature, _empty

from daf.logging.tracing import TraceLEVELS, trace

import decimal
import importlib
import copy
import asyncio
import datetime

import _discord as discord

from .misc import cache, attributes
from .misc.instance_track import *
from . import client
from . import guild
from . import message
from . import logging
from . import web
from . import events


__all__ = (
    "convert_object_to_semi_dict",
    "convert_from_semi_dict"
)


LAMBDA_TYPE = type(lambda x: x)


@cache.cache_result()
def import_class(path: str):
    """
    Imports the class provided by it's ``path``.
    """
    path = path.split(".")
    module_path, class_name = '.'.join(path[:-1]), path[-1]
    try:
        module = importlib.import_module(module_path)
    except Exception as exc:  # Fall back for older versions, try to import from package instead of module
        module_path = module_path.split('.')[0]
        trace(f"Could not import {module_path}, trying {module_path}", TraceLEVELS.WARNING, exc)
        module = importlib.import_module(module_path)

    class_ = getattr(module, class_name)
    return class_


CONVERSION_ATTRS = {
    client.ACCOUNT: {
        "attrs": attributes.get_all_slots(client.ACCOUNT),
        "attrs_restore": {
            "_running": False,
            "_client": None,
            "_ws_task": None,
            "_event_ctrl": events.EventController()
        },
    },
    guild.AutoGUILD: {
        "attrs": attributes.get_all_slots(guild.AutoGUILD),
        "attrs_restore": {
            "guild_query_iter": None,
            "update_semaphore": asyncio.Semaphore(1),
            "parent": None,
            "guild_query_iter": None,
            "_event_ctrl": None,
            "_removal_timer_handle": None,
            "_guild_join_timer_handle": None
        },
    },
    message.AutoCHANNEL: {
        "attrs": attributes.get_all_slots(message.AutoCHANNEL),
        "attrs_restore": {
            "parent": None,
            "removed_channels": set(),
            "channel_getter": None,
        },
    },
    web.SeleniumCLIENT: {
        "attrs": attributes.get_all_slots(web.SeleniumCLIENT),
        "attrs_restore": {
            "driver": None
        }
    },
    web.GuildDISCOVERY: {
        "attrs": attributes.get_all_slots(web.GuildDISCOVERY),
        "attrs_restore": {
            "session": None,
            "browser": None
        }
    },
    logging.LoggerSQL: {
        "attrs": ["_daf_id"]
    },
    logging.LoggerJSON: {
        "attrs": []
    },
    logging.LoggerCSV: {
        "attrs": []
    },
    discord.Embed: {
        "custom_encoder": lambda embed: embed.to_dict(),
        "custom_decoder": lambda value: discord.Embed.from_dict(value),
    },
    discord.Intents: {
        "custom_encoder": lambda intents: intents.value,  # Ignores other keys and calls the lambda to convert
        "custom_decoder": lambda value: discord.Intents._from_value(value),
    },
    datetime.datetime: {
        "custom_encoder": lambda object: object.isoformat(),
        "custom_decoder": lambda string: datetime.datetime.fromisoformat(string)
    },
    datetime.timedelta: {
        "custom_encoder": lambda object: object.total_seconds(),
        "custom_decoder": lambda seconds: datetime.timedelta(seconds=seconds)
    },
    bytes: {
        "custom_encoder": lambda data: data.hex(),
        "custom_decoder": lambda hex_str: bytes.fromhex(hex_str)
    },
    set: {
        "custom_encoder": lambda data: convert_object_to_semi_dict(list(data)),
        "custom_decoder": lambda list_data: set(convert_from_semi_dict(list_data))
    },
    dict: {
        "custom_encoder": lambda data: {k: convert_object_to_semi_dict(v) for k, v in data.items()},
        "custom_decoder": lambda data: {k: convert_from_semi_dict(v) for k, v in data.items()}
    },
    discord.Guild: {
        "attrs": ["name", "id"]
    },
    discord.User: {
        "attrs": ["name", "id"]
    },
    discord.TextChannel: {
        "attrs": ["name", "id", "slowmode_delay"],
    },
    discord.VoiceChannel: {
        "attrs": ["name", "id"],
    }
}
"""
This is a custom conversion dictionary.
It's values are datatypes of objects which cannot be normally converted to JSON, so custom rules are required.

Each value of the dictionary is another dictionary, which defined the rules about the specific datatype conversion.
These can contain the following items:

- "attrs": Iterable of attribute names that will be included in the output JSON-compatible dictionary.
- "attrs_restored": Dictionary of attributes (keys) that are skipped when converting to dict.
   When restoring from dictionary, the object will have these attributes set with the co-responding values.
- "attrs_convert": Dictionary of attributes(keys) that which's values can either be a fixed value of a function.
  The values of this override the object's attribute values. If a function is given, the function is (as parameter) 
  passed the object that is being converted and whatever it returns is used in
  the output dictionary as the attribute value.
- "attrs_skip": Iterable of attributes names that will be completely ignored when converting. They also won't be set
  when restoring from the output dictionary.

2 special items can be used, which override the default conversion logic.
If they are passed, the previously talked about items will be ignored.
These are:

- "custom_encoder": A function that accepts the object being converted as a parameter. It must return a JSON
  serializable object.
- "custom_decoder": A function that accepts the JSON compatible object. It must return the original Python object.
"""

# Guilds
CONVERSION_ATTRS[guild.GUILD] = {
    "attrs": attributes.get_all_slots(guild.GUILD),
    "attrs_restore": {
        "update_semaphore": asyncio.Semaphore(1),
        "parent": None,
        "_removal_timer_handle": None,
        "_event_ctrl": None
    },
}

CONVERSION_ATTRS[guild.USER] = CONVERSION_ATTRS[guild.GUILD].copy()
CONVERSION_ATTRS[guild.USER]["attrs"] = attributes.get_all_slots(guild.USER)

if logging.sql.SQL_INSTALLED:
    def create_decoder(cls):
        """
        Function returns the decoder function which uses the ``cls`` parameter.
        It cannot be passed directly since for loop would update the ``cls`` parameter.
        """
        def decoder_func(data: Mapping):
            def _decode_object_type(cls, data: Mapping):
                new_object = cls.__new__(cls)
                for k, v in data.items():
                    if isinstance(v, (Mapping, list)):
                        v = convert_from_semi_dict(v)

                    new_object.__dict__[k] = v

                return new_object

            return _decode_object_type(cls, data)

        return decoder_func

    sql_ = logging.sql
    ORMBase = sql_.tables.ORMBase
    values = list(sql_.tables.__dict__.values())
    values.remove(ORMBase)
    for cls in values:
        with suppress(TypeError):
            if not issubclass(cls, ORMBase):
                continue

            attrs = list(cls.__init__._sa_original_init.__annotations__.keys())
            if hasattr(cls, "id"):
                attrs.append("id")

            with suppress(ValueError):
                attrs.remove("snowflake")
                attrs.append("snowflake_id")

            CONVERSION_ATTRS[cls] = {
                "attrs": attrs,
                "custom_decoder": create_decoder(cls)
            }

    CONVERSION_ATTRS[sql_.MessageLOG]["attrs"].extend(["id", "timestamp", "success_rate"])
    CONVERSION_ATTRS[sql_.InviteLOG]["attrs"].extend(["id", "timestamp"])

# Messages
CHANNEL_LAMBDA = (
    lambda message_:
        [(x if isinstance(x, int) else x.id) for x in message_.channels]
        if not isinstance(message_.channels, message.AutoCHANNEL)
        else message_.channels
)

CONVERSION_ATTRS[message.TextMESSAGE] = {
    "attrs": attributes.get_all_slots(message.TextMESSAGE),
    "attrs_restore": {
        "update_semaphore": asyncio.Semaphore(1),
        "parent": None,
        "sent_messages": {},
        "channel_getter": None,
        "_event_ctrl": None,
        "_timer_handle": None
    },
    "attrs_convert": {
        "channels": CHANNEL_LAMBDA
    },
}

CONVERSION_ATTRS[message.VoiceMESSAGE] = {
    "attrs": attributes.get_all_slots(message.VoiceMESSAGE),
    "attrs_restore": {
        "update_semaphore": asyncio.Semaphore(1),
        "parent": None,
        "channel_getter": None,
        "_event_ctrl": None,
        "_timer_handle": None
    },
    "attrs_convert": {
        "channels": CHANNEL_LAMBDA
    },
}


CONVERSION_ATTRS[message.DirectMESSAGE] = {
    "attrs": attributes.get_all_slots(message.DirectMESSAGE),
    "attrs_restore": {
        "update_semaphore": asyncio.Semaphore(1),
        "parent": None,
        "previous_message": None,
        "dm_channel": None,
        "_event_ctrl": None,
        "_timer_handle": None
    },
}


def convert_object_to_semi_dict(to_convert: Any, only_ref: bool = False) -> Mapping:
    """
    Converts an object into dict.

    Parameters
    ---------------
    to_convert: Any
        The object to convert.
    only_ref: bool
        If True, the object will be replaced with a ObjectReference instance containing only the object_id.
    """
    def _convert_json_slots(to_convert):
        type_object = type(to_convert)
        attrs = CONVERSION_ATTRS.get(type_object)
        if attrs is None:
            # No custom rules defined, try to convert normally with either vars or __slots__
            try:
                attrs = {"attrs": attributes.get_all_slots(type_object) if hasattr(to_convert, "__slots__") else vars(to_convert)}
            except TypeError:
                return to_convert  # Not structured object or does not have overrides defined, return the object itself

        # Check if custom conversion function is requested
        if (encoder_func := attrs.get("custom_encoder")) is not None:
            data_conv = encoder_func(to_convert)
        else:
            # No custom conversion function provided, use the normal rules
            data_conv = {}
            (
                attrs,
                attrs_restore,
                attrs_convert,
                skip
            ) = (
                attrs["attrs"],
                attrs.get("attrs_restore", {}),
                attrs.get("attrs_convert", {}),
                attrs.get("attrs_skip", [])
            )
            for k in attrs:
                # Manually set during restored or is a class attribute
                if k in attrs_restore or k in skip:
                    continue

                if k in attrs_convert:
                    value = attrs_convert[k]
                    if isinstance(value, LAMBDA_TYPE):
                        value = value(to_convert)
                else:
                    try:
                        value = getattr(to_convert, k)
                    except AttributeError as exc:
                        trace(
                            f"Conversion could not obtain attr '{k}' in {to_convert}({type(to_convert)}). Using None",
                            TraceLEVELS.WARNING,
                            exc
                        )
                        value = None

                data_conv[k] = convert_object_to_semi_dict(value)

        return {"object_type": f"{type_object.__module__}.{type_object.__name__}", "data": data_conv}

    object_type = type(to_convert)
    if object_type in {int, float, str, bool, decimal.Decimal, type(None)}:
        if object_type is decimal.Decimal:
            to_convert = float(to_convert)

        return to_convert

    if isinstance(to_convert, (list, tuple)):
        to_convert = [convert_object_to_semi_dict(value) for value in to_convert]
        return to_convert

    if isinstance(to_convert, Enum):
        return {"enum_type": f"{object_type.__module__}.{object_type.__name__}", "value": to_convert.value}

    if isclass(to_convert):  # Class itself, not an actual isntance
        return {"class_path": f"{to_convert.__module__}.{to_convert.__name__}"}

    if only_ref:
        # Don't serialize object completly, only ID is requested.
        # This prevents unnecessarily large data to be encoded
        to_convert = ObjectReference(get_object_id(to_convert))

    return _convert_json_slots(to_convert)


def convert_from_semi_dict(d: Union[Mapping, list, Any]):
    """
    Function that converts the ``d`` parameter which is a semi-dict back to the object
    representation.

    Parameters
    ---------------
    d: Union[dict, list, Any]
        The semi-dict / list to convert.
    """

    def __convert_to_slotted():
        # d is a object serialized to dict
        class_ = import_class(d["object_type"])
        # Get the custom decoder function
        if (decoder_func := CONVERSION_ATTRS.get(class_, {}).get("custom_decoder")) is not None:
            # Custom decoder function is used
            return decoder_func(d["data"])

        # Only object's ID reference was encoded -> restore by ID
        if class_ is ObjectReference:
            return get_by_id(d["data"]["ref"])

        # No custom decoder function, normal conversion is used
        _return = class_.__new__(class_)

        # Change the setattr function to default Python, since we just want to directly set attributes
        # Set saved attributes
        for k, v in d["data"].items():
            if isinstance(v, (Mapping, list)):
                v = convert_from_semi_dict(v)

            try:
                setattr(_return, k, v)
            except Exception as exc:
                trace(
                    f"Could not set {k} of {class_.__name__} - Older DAF version data?",
                    TraceLEVELS.WARNING,
                    exc
                )        

        # Modify attributes that have specified different restore values
        attrs = CONVERSION_ATTRS.get(class_)
        if attrs is not None:
            attrs_restore = attrs.get("attrs_restore", {})
            for k, v in attrs_restore.items():
                # copy.copy prevents external modifications since it's passed by reference
                setattr(_return, k, copy.copy(v))

        # Try to fill in missing attributes
        # Try to set attributes from parameters based on their defaults, if it doesn't work
        # set them to None and hope for the best
        with suppress(AttributeError):
            parameters = signature(class_).parameters
            attrs = attributes.get_all_slots(class_)
            for k in attrs:
                if hasattr(_return, k):
                    continue

                k_lookup = k
                if k_lookup not in parameters:
                    # Some attributes are the same as parameters but "private" marked by '_'
                    k_lookup = k_lookup.strip("_")

                new_val = None
                if k in parameters:
                    default = parameters[k].default
                    if default is not _empty:
                        new_val = default


                setattr(_return, k, new_val)

        return _return

    def __convert_to_dict():  # Compatibility with file backups from v2.9.x
        data = {}
        for k, v in d.items():
            data[k] = convert_from_semi_dict(v)

        return data

    # List conversion, keeps the list but converts the values
    if isinstance(d, list):
        return [convert_from_semi_dict(value) if isinstance(value, Mapping) else value for value in d]

    # Either an object serialized to dict or a normal dictionary
    elif isinstance(d, Mapping):
        if "enum_type" in d:  # It's a JSON converted Enum
            return import_class(d["enum_type"])(d["value"])

        if "class_path" in d:  # A class was directly send (not an instance)
            return import_class(d["class_path"])

        if "object_type" not in d:
            # Compatibility with file backups from v2.9.x
            # It's a normal dictionary
            return __convert_to_dict()

        return __convert_to_slotted()

    return d  # Unsupported value, assume no conversion is necessary
