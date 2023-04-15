from typing import get_type_hints, Iterable, Any, Union, List
from contextlib import suppress
from enum import Enum

import decimal
import datetime as dt
import importlib.util as import_util

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
    "UserDataFunction",
    "issubclass_noexcept",
)


def issubclass_noexcept(*args):
    try:
        return issubclass(*args)
    except Exception:
        return False


def UserDataFunction(fnc: str):
    mod_spec = import_util.spec_from_loader("__tmp", None)
    __tmp = import_util.module_from_spec(mod_spec)
    exec(fnc, __tmp.__dict__)

    _v = None
    for v in __tmp.__dict__.values():
        if issubclass_noexcept(v, daf.dtypes._FunctionBaseCLASS):
            _v = v()
            break

    if _v is None:
        raise ValueError("Could not find any functions. Make sure you've used the @data_function decorator on it!")

    return _v


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
        "tzinfo": Union[dt.tzinfo, None],
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
    discord.EmbedField: {
        "name": str, "value": str, "inline": bool
    },
    daf.TextMESSAGE: {
        "data": Union[Iterable[Union[str, discord.Embed, daf.FILE]], str, discord.Embed, daf.FILE, UserDataFunction]
    },
    daf.VoiceMESSAGE: {
        "data": Union[daf.dtypes.AUDIO, Iterable[daf.dtypes.AUDIO], UserDataFunction]
    },
    daf.DirectMESSAGE: {
        "data": Union[Iterable[Union[str, discord.Embed, daf.FILE]], str, discord.Embed, daf.FILE, UserDataFunction]
    },
}

if daf.sql.SQL_INSTALLED:
    sql_ = daf.sql
    for item in sql_.ORMBase.__subclasses__():
        ADDITIONAL_ANNOTATIONS[item] = get_type_hints(item.__init__._sa_original_init)

    ADDITIONAL_ANNOTATIONS[sql_.MessageLOG] = {"id": int, "timestamp": dt.datetime, **ADDITIONAL_ANNOTATIONS[sql_.MessageLOG]}
    ADDITIONAL_ANNOTATIONS[sql_.MessageLOG]["success_rate"] = decimal.Decimal


CONVERSION_ATTR_TO_PARAM = {}
OBJECT_CONV_CACHE = {}


if daf.sql.SQL_INSTALLED:
    sql_ = daf.sql

    for subcls in [sql_.GuildUSER, sql_.CHANNEL]:
        hints = {**ADDITIONAL_ANNOTATIONS.get(subcls, {}), **get_type_hints(subcls.__init__._sa_original_init)}
        CONVERSION_ATTR_TO_PARAM[subcls] = {key: key for key in hints.keys()}

    CONVERSION_ATTR_TO_PARAM[sql_.GuildUSER]["snowflake"] = "snowflake_id"
    CONVERSION_ATTR_TO_PARAM[sql_.CHANNEL]["snowflake"] = "snowflake_id"


class ObjectInfo:
    """
    Describes Python objects' parameters.
    """
    CHARACTER_LIMIT = 200

    def __init__(self, class_, data: dict) -> None:
        self.class_ = class_
        self.data = data

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
    object_data = []
    import_data = []
    other_data = []

    if isinstance(object, ObjectInfo):
        if object.class_ is UserDataFunction:
            other_data.append(object.data["fnc"])
            object_str = UserDataFunction(object.data["fnc"]).func_name + "("
            attr_str = ""
        else:
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
            object = object.replace("\n", "\\n").replace('"', '\\"')
            object_data.append(f'"{object}"')
        else:
            object_data.append(str(object))

    return ",".join(object_data).strip(), import_data, "\n".join(other_data).strip()


def convert_to_object_info(object_: object):
    with suppress(TypeError):
        if object_ in OBJECT_CONV_CACHE:
            return OBJECT_CONV_CACHE.get(object_)

    object_type = type(object_)

    if object_type in {int, float, str, bool, decimal.Decimal, type(None)}:
        if object_type is decimal.Decimal:
            object_ = float(object_)

        return object_

    if isinstance(object_, Iterable):
        if type(object_) not in {set, list, tuple}:
            object_ = list(object_)

        for i, value in enumerate(object_):
            object_[i] = convert_to_object_info(value)
            pass

        return object_

    data_conv = {}
    attrs = CONVERSION_ATTR_TO_PARAM.get(object_type)
    if attrs is None:
        additional_annots = {key: key for key in ADDITIONAL_ANNOTATIONS.get(object_type, {})}
        attrs = {key: key for key in get_type_hints(object_type.__init__).keys()}
        attrs.update(**additional_annots)

    for k, v in attrs.items():
        with suppress(Exception):
            value = getattr(object_, v)
            if value is object_:
                data_conv[k] = value
            else:
                data_conv[k] = convert_to_object_info(value)
                pass

    ret = ObjectInfo(object_type, data_conv)
    OBJECT_CONV_CACHE[object_] = ret
    if len(OBJECT_CONV_CACHE) > 10000:
        OBJECT_CONV_CACHE.clear()

    return ret


def convert_to_objects(d: ObjectInfo):
    data_conv = {}
    for k, v in d.data.items():
        if isinstance(v, ObjectInfo):
            v = convert_to_objects(v)

        elif isinstance(v, list):
            v = v.copy()
            for i, subv in enumerate(v):
                if isinstance(subv, ObjectInfo):
                    v[i] = convert_to_objects(subv)

        data_conv[k] = v

    return d.class_(**data_conv)


def convert_to_json(d: ObjectInfo):
    data_conv = {}
    for k, v in d.data.items():
        if isinstance(v, ObjectInfo):
            v = convert_to_json(v)

        elif isinstance(v, list):
            v = v.copy()
            for i, subv in enumerate(v):
                if isinstance(subv, ObjectInfo):
                    v[i] = convert_to_json(subv)

        data_conv[k] = v

    return {"type": f"{d.class_.__module__}.{d.class_.__name__}", "data": data_conv}


def convert_from_json(d: Union[dict, List[dict], Any]) -> ObjectInfo:
    if isinstance(d, list):
        result = []
        for item in d:
            result.append(convert_from_json(item))

        return result

    elif isinstance(d, dict):
        type_: str = d["type"]
        data: dict = d["data"]
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

        for k, v in data.items():
            if isinstance(v, list) or isinstance(v, dict) and v.get("type") is not None:
                v = convert_from_json(v)
                data[k] = v

        return ObjectInfo(type_, data)

    else:
        return d
