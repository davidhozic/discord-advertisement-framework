"""
Modules contains definitions related to GUI object transformations.
"""

from typing import Any, Union, List, get_type_hints, Generic, TypeVar
from contextlib import suppress
from enum import Enum
from inspect import signature

import decimal
import datetime as dt

import _discord as discord
import daf


__all__ = (
    "ObjectInfo",
    "convert_to_objects",
    "convert_to_object_info",
    "convert_to_json",
    "convert_from_json",
    "convert_objects_to_script",
    "ADDITIONAL_ANNOTATIONS",
    "issubclass_noexcept",
)

TClass = TypeVar("TClass")


def issubclass_noexcept(*args):
    try:
        return issubclass(*args)
    except Exception:
        return False


ADDITIONAL_ANNOTATIONS = {
    dt.timedelta: {
        "days": float,
        "seconds": float,
        "microseconds": float,
        "milliseconds": float,
        "minutes": float,
        "hours": float,
        "weeks": float
    },
    dt.datetime: {
        "year": int,
        "month": Union[int, None],
        "day": Union[int, None],
        "hour": int,
        "minute": int,
        "second": int,
        "microsecond": int,
        "fold": int
    },
    discord.Embed: {
        "colour": Union[int, discord.Colour],
        "color": Union[int, discord.Colour],
        "title": str,
        "type": discord.embeds.EmbedType,
        "url": str,
        "description": str,
        "timestamp": dt.datetime,
        "fields": List[discord.EmbedField]
    },
    discord.Intents: {k: bool for k in discord.Intents.VALID_FLAGS},
    discord.EmbedField: {
        "name": str, "value": str, "inline": bool
    },
    daf.add_object: {
        "obj": daf.ACCOUNT
    },
}

if daf.logging.sql.SQL_INSTALLED:
    sql_ = daf.logging.sql.tables
    for item in sql_.ORMBase.__subclasses__():
        ADDITIONAL_ANNOTATIONS[item] = item.__init__._sa_original_init.__annotations__

    ADDITIONAL_ANNOTATIONS[sql_.MessageLOG] = {"id": int, "timestamp": dt.datetime, **ADDITIONAL_ANNOTATIONS[sql_.MessageLOG]}
    ADDITIONAL_ANNOTATIONS[sql_.MessageLOG]["success_rate"] = decimal.Decimal

    ADDITIONAL_ANNOTATIONS[sql_.InviteLOG] = {"id": int, "timestamp": dt.datetime, **ADDITIONAL_ANNOTATIONS[sql_.InviteLOG]}


CONVERSION_ATTR_TO_PARAM = {
    daf.AUDIO: {
        "filename": "orig"
    },
    dt.timezone: {
        "offset": "_offset",
        "name": "_name",
    }
}

OBJECT_CONV_CACHE = {}

CONVERSION_ATTR_TO_PARAM[daf.client.ACCOUNT] = {k: k for k in daf.client.ACCOUNT.__init__.__annotations__}
CONVERSION_ATTR_TO_PARAM[daf.client.ACCOUNT]["token"] = "_token"
CONVERSION_ATTR_TO_PARAM[daf.client.ACCOUNT]["username"] = lambda account: account.selenium._username if account.selenium is not None else None
CONVERSION_ATTR_TO_PARAM[daf.client.ACCOUNT]["password"] = lambda account: account.selenium._password if account.selenium is not None else None


if daf.sql.SQL_INSTALLED:
    sql_ = daf.sql

    for subcls in [sql_.GuildUSER, sql_.CHANNEL]:
        hints = {**ADDITIONAL_ANNOTATIONS.get(subcls, {}), **get_type_hints(subcls.__init__._sa_original_init)}
        CONVERSION_ATTR_TO_PARAM[subcls] = {key: key for key in hints.keys()}

    CONVERSION_ATTR_TO_PARAM[sql_.GuildUSER]["snowflake"] = "snowflake_id"
    CONVERSION_ATTR_TO_PARAM[sql_.CHANNEL]["snowflake"] = "snowflake_id"


for item in {daf.TextMESSAGE, daf.VoiceMESSAGE, daf.DirectMESSAGE}:
    CONVERSION_ATTR_TO_PARAM[item] = {k: k for k in item.__init__.__annotations__}
    CONVERSION_ATTR_TO_PARAM[item]["data"] = "_data"
    CONVERSION_ATTR_TO_PARAM[item]["start_in"] = "next_send_time"


CONVERSION_ATTR_TO_PARAM[daf.TextMESSAGE]["channels"] = (
    lambda message_: [x if isinstance(x, int) else x.id for x in message_.channels] if not isinstance(message_.channels, daf.AutoCHANNEL) else message_.channels
)
CONVERSION_ATTR_TO_PARAM[daf.VoiceMESSAGE]["channels"] = CONVERSION_ATTR_TO_PARAM[daf.TextMESSAGE]["channels"]

CONVERSION_ATTR_TO_PARAM[daf.GUILD] = {k: k for k in daf.GUILD.__init__.__annotations__}
CONVERSION_ATTR_TO_PARAM[daf.GUILD]["invite_track"] = (
    lambda guild_: list(guild_.join_count.keys())
)


class ObjectInfo(Generic[TClass]):
    """
    A GUI object that represents real objects,.
    The GUI only knows how to work with ObjectInfo.

    Parameters
    -----------------
    class_: type
        Real object's type.
    data: dict
        Dictionary mapping to real object's parameters
    real_object: object
        Actual object that ObjectInfo represents inside GUI. Used whenever update
        of the real object is needed upon saving inside the GUI.
    """
    CHARACTER_LIMIT = 200

    def __init__(self, class_, data: dict, real_object: object = None) -> None:
        self.class_ = class_
        self.data = data
        self.real_object = real_object

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, ObjectInfo):
            return (
                self.class_ is __value.class_ and
                self.real_object is __value.real_object and
                self.data == __value.data
            )

        return False

    def __repr__(self) -> str:
        _ret: str = self.class_.__name__ + "("
        for k, v in self.data.items():
            v = f'"{v}"' if isinstance(v, str) else str(v)
            _ret += f"{k}={v}, "

        _ret = _ret.rstrip(", ") + ")"
        if len(_ret) > self.CHARACTER_LIMIT:
            _ret = _ret[:self.CHARACTER_LIMIT] + "...)"

        return _ret


def convert_objects_to_script(object: Union[ObjectInfo, list, tuple, set, str]):
    """
    Converts ObjectInfo objects into equivalent Python code.
    """
    object_data = []
    import_data = []
    other_data = []

    if isinstance(object, ObjectInfo):
        object_str = f"{object.class_.__name__}(\n    "
        attr_str = ""
        for attr, value in object.data.items():
            if isinstance(value, (ObjectInfo, list, tuple, set)):
                value, import_data_, other_str = convert_objects_to_script(value)
                import_data.extend(import_data_)
                if other_str != "":
                    other_data.append(other_str)

            elif isinstance(value, str):
                value, _, other_str = convert_objects_to_script(value)
                if other_str != "":
                    other_data.append(other_str)

            attr_str += f"{attr}={value},\n"
            if issubclass(type(value), Enum):
                import_data.append(f"from {type(value).__module__} import {type(value).__name__}")

        import_data.append(f"from {object.class_.__module__} import {object.class_.__name__}")

        object_str += "    ".join(attr_str.splitlines(True)) + ")"
        object_data.append(object_str)

    elif isinstance(object, (list, tuple, set)):
        _list_data = "[\n"
        for element in object:
            object_str, import_data_, other_str = convert_objects_to_script(element)
            _list_data += object_str + ",\n"
            import_data.extend(import_data_)
            other_data.append(other_str)

        _list_data = "    ".join(_list_data.splitlines(keepends=True))
        _list_data += "]"
        object_data.append(_list_data)
    else:
        if isinstance(object, str):
            object = object.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')
            object_data.append(f'"{object}"')
        else:
            object_data.append(str(object))

    return ",".join(object_data).strip(), import_data, "\n".join(other_data).strip()


def convert_to_object_info(object_: object, save_original = False, cache = False):
    """
    Converts an object into ObjectInfo.

    Parameters
    ---------------
    object_: object
        The object to convert.
    save_original: bool
        If True, will save the original object inside the ``real_object`` attribute of :class:`ObjectInfo`
    cache: bool
        Should cache be used to speed up lookups.
    """
    def _convert_object_info(object_, save_original, object_type, attrs):
        data_conv = {}
        for k, v in attrs.items():
            with suppress(Exception):
                if callable(v):
                    value = v(object_)
                else:
                    value = getattr(object_, v)

                # Check if object is a singleton that is not builtin.
                # Singletons should not be stored as they would get recreated causing issues on save -> load.
                type_value = type(value)
                with suppress(ValueError):  # Some don't have a signature
                    if type_value.__name__ not in __builtins__ and not len(signature(type_value).parameters):
                        continue

                if value is object_:
                    data_conv[k] = value
                else:
                    data_conv[k] = convert_to_object_info(value, save_original, cache=cache)

        ret = ObjectInfo(object_type, data_conv)
        if save_original:
            ret.real_object = object_
        return ret

    def get_conversion_map(object_type):
        attrs = CONVERSION_ATTR_TO_PARAM.get(object_type)
        if attrs is None:
            attrs = {}
            additional_annots = {key: key for key in ADDITIONAL_ANNOTATIONS.get(object_type, {})}
            with suppress(AttributeError):
                attrs = {key: key for key in object_type.__init__.__annotations__.keys()}

            attrs.update(**additional_annots)

        attrs.pop("return", None)
        return attrs

    with suppress(KeyError, TypeError):
        if cache:
            return OBJECT_CONV_CACHE[object_]

    object_type = type(object_)

    if object_type in {int, float, str, bool, decimal.Decimal, type(None)} or isinstance(object_, Enum):
        if object_type is decimal.Decimal:
            object_ = float(object_)

        return object_

    if isinstance(object_, (set, list, tuple)):
        object_ = [convert_to_object_info(value, save_original, cache=cache) for value in object_]
        return object_

    attrs = get_conversion_map(object_type)
    ret = _convert_object_info(object_, save_original, object_type, attrs)
    with suppress(TypeError):
        if cache:
            OBJECT_CONV_CACHE[object_] = ret
            if len(OBJECT_CONV_CACHE) > 50000:
                for k in list(OBJECT_CONV_CACHE.keys())[:10000]:
                    del OBJECT_CONV_CACHE[k]

    return ret


def convert_to_objects(
    d: Union[ObjectInfo, dict, list],
    keep_original_object: bool = False,
    skip_real_conversion: bool = False,
) -> Union[object, dict, List]:
    """
    Converts :class:`ObjectInfo` instances into actual objects,
    specified by the ObjectInfo.class_ attribute.

    Parameters
    -----------------
    d: ObjectInfo | list[ObjectInfo] | dict
        The object(s) to convert. Can be an ObjectInfo object, a list of ObjectInfo objects or a dictionary that is a
        mapping of ObjectInfo parameters.
    keep_original_object: bool
        If True, the returned object will be the same object (``real_object`` attribute) and will just
        copy the the attributes. Important for preserving parent-child connections across real objects.
    skip_real_conversion: bool
        If set to True the old real object will be returned without conversion and ``keep_original_object`` parameter
        has no effect.
        Defaults to False.
    """
    def convert_list():
        _ = []
        for item in d:
            _.append(convert_to_objects(item, keep_original_object, skip_real_conversion))

        return _

    def convert_object_info():
        # Skip conversion
        real = d.real_object
        if skip_real_conversion and real is not None:
            return real

        data_conv = {}
        for k, v in d.data.items():
            if isinstance(v, (list, tuple, set, ObjectInfo, dict)):
                data_conv[k] = convert_to_objects(v, keep_original_object)
            else:
                data_conv[k] = v

        new_obj = d.class_(**data_conv)
        if keep_original_object and real is not None:
            with suppress(TypeError, AttributeError):
                # Only update old objects that are surely not built-in and have information about attributes
                args = daf.misc.get_all_slots(type(real)) if hasattr(real, "__slots__") else vars(real)
                for a in args:
                    setattr(real, a, getattr(new_obj, a))

                new_obj = real

        return new_obj

    def convert_object_info_dict():
        data_conv = {}
        for k, v in d.items():
            data_conv[k] = convert_to_objects(v, keep_original_object, skip_real_conversion)

        return data_conv

    if isinstance(d, (list, tuple, set)):
        return convert_list()
    if isinstance(d, ObjectInfo):
        return convert_object_info()
    if isinstance(d, dict):
        return convert_object_info_dict()

    return d


def convert_to_json(d: Union[ObjectInfo, List[ObjectInfo], Any]):
    """
    Converts ObjectInfo into JSON representation.
    """
    def _convert_to_json_oi(d: ObjectInfo):
        data_conv = {}
        for k, v in d.data.items():
            data_conv[k] = convert_to_json(v)

        return {"type": f"{d.class_.__module__}.{d.class_.__name__}", "data": data_conv}

    def _convert_to_json_list(d: List[ObjectInfo]):
        d = d.copy()
        for i, element in enumerate(d):
            d[i] = convert_to_json(element)

        return d

    if isinstance(d, ObjectInfo):
        return _convert_to_json_oi(d)

    elif isinstance(d, list):
        return _convert_to_json_list(d)

    elif issubclass((type_d := type(d)), Enum):
        return {"type": f"{type_d.__module__}.{type_d.__name__}", "value": d.value}

    return d


def convert_from_json(d: Union[dict, List[dict], Any]) -> ObjectInfo:
    """
    Converts previously converted JSON back to ObjectInfo.
    """
    if isinstance(d, list):
        result = []
        for item in d:
            result.append(convert_from_json(item))

        return result

    elif isinstance(d, dict):
        type_: str = d["type"]
        type_split = type_.split('.')
        module = type_split[:len(type_split) - 1]
        type_ = type_split[-1]
        if module[0] == __name__.split(".")[-1]:
            type_ = globals()[type_]
        else:
            module_ = __import__(module[0])
            module.pop(0)
            for i, m in enumerate(module):
                module_ = getattr(module_, module[i])

            type_ = getattr(module_, type_)

        # Simple object (or enum)
        if "value" in d:
            return type_(d["value"])

        # ObjectInfo
        data: dict = d["data"]
        for k, v in data.items():
            # List or dictionary and dictionary is a object representation of an object
            if isinstance(v, list) or isinstance(v, dict) and d.get("type") is not None:
                v = convert_from_json(v)
                data[k] = v

        return ObjectInfo(type_, data)
    else:
        return d
