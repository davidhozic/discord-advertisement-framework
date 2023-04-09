from typing import get_type_hints, Iterable, Any
from contextlib import suppress


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
    "ADDITIONAL_ANNOTATIONS",
)


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
        "month": int | None,
        "day": int | None,
        "hour": int,
        "minute": int,
        "second": int,
        "microsecond": int,
        "tzinfo": dt.tzinfo | None,
        "fold": int
    },
    discord.Embed: {
        "title": str,
        "url": str,
        "description": str
    },
}

if daf.sql.SQL_INSTALLED:
    sql_ = daf.sql
    for item in sql_.ORMBase.__subclasses__():
        ADDITIONAL_ANNOTATIONS[item] = get_type_hints(item.__init__._sa_original_init)

    ADDITIONAL_ANNOTATIONS[sql_.MessageLOG] = {"id": int, **ADDITIONAL_ANNOTATIONS[sql_.MessageLOG]}
    ADDITIONAL_ANNOTATIONS[sql_.MessageLOG]["success_rate"] = decimal.Decimal
    ADDITIONAL_ANNOTATIONS[sql_.MessageLOG]["timestamp"] = dt.datetime


CONVERSION_ATTR_TO_PARAM = {}
OBJECT_CONV_CACHE = {}


if daf.sql.SQL_INSTALLED:
    sql_ = daf.sql

    for subcls in sql_.ORMBase.__subclasses__():
        hints = {**get_type_hints(subcls.__init__._sa_original_init), **ADDITIONAL_ANNOTATIONS.get(subcls, {})}
        CONVERSION_ATTR_TO_PARAM[subcls] = {key: key for key in hints.keys()}

    CONVERSION_ATTR_TO_PARAM[sql_.MessageLOG] = {"id": int, **CONVERSION_ATTR_TO_PARAM[sql_.MessageLOG]}
    CONVERSION_ATTR_TO_PARAM[sql_.GuildUSER]["snowflake_id"] = "snowflake"
    CONVERSION_ATTR_TO_PARAM[sql_.CHANNEL]["snowflake_id"] = "snowflake"


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
            value = getattr(object_, k)
            if value is object_:
                data_conv[v] = value
            else:
                data_conv[v] = convert_to_object_info(value)
                pass

    ret = ObjectInfo(object_type, data_conv)
    OBJECT_CONV_CACHE[object_] = ret
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


def convert_from_json(d: dict | list[dict] | Any) -> ObjectInfo:
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
