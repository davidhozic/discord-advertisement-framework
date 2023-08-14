"""
Modules contains definitions related to GUI object transformations.
"""

from typing import Any, Union, List, get_type_hints, Generic, TypeVar, Iterable, Mapping
from contextlib import suppress
from enum import Enum
from inspect import signature, getmembers

from daf.convert import import_class
from daf.misc import instance_track as it

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
    "convert_dict_to_object_info",
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
    discord.TextChannel: {
        "name": str,
        "id": int
    },
    daf.add_object: {
        "obj": daf.ACCOUNT
    },
}

ADDITIONAL_ANNOTATIONS[discord.VoiceChannel] = ADDITIONAL_ANNOTATIONS[discord.TextChannel]
ADDITIONAL_ANNOTATIONS[discord.Guild] = ADDITIONAL_ANNOTATIONS[discord.TextChannel]

if daf.logging.sql.SQL_INSTALLED:
    sql_ = daf.logging.sql.tables
    for item in sql_.ORMBase.__subclasses__():
        ADDITIONAL_ANNOTATIONS[item] = item.__init__._sa_original_init.__annotations__

    ADDITIONAL_ANNOTATIONS[sql_.MessageLOG] = {"id": int, "timestamp": dt.datetime, **ADDITIONAL_ANNOTATIONS[sql_.MessageLOG]}
    ADDITIONAL_ANNOTATIONS[sql_.MessageLOG]["success_rate"] = decimal.Decimal

    ADDITIONAL_ANNOTATIONS[sql_.InviteLOG] = {"id": int, "timestamp": dt.datetime, **ADDITIONAL_ANNOTATIONS[sql_.InviteLOG]}


CONVERSION_ATTR_TO_PARAM = {
    dt.timezone: {
        "offset": "_offset",
        "name": "_name",
    },
}

CONVERSION_ATTR_TO_PARAM[daf.client.ACCOUNT] = {k: k for k in daf.client.ACCOUNT.__init__.__annotations__}
CONVERSION_ATTR_TO_PARAM[daf.client.ACCOUNT]["token"] = "_token"
CONVERSION_ATTR_TO_PARAM[daf.client.ACCOUNT]["username"] = lambda account: account.selenium._username if account.selenium is not None else None
CONVERSION_ATTR_TO_PARAM[daf.client.ACCOUNT]["password"] = lambda account: account.selenium._password if account.selenium is not None else None

CONVERSION_ATTR_TO_PARAM[daf.dtypes.FILE] = {k: k for k in daf.dtypes.FILE.__init__.__annotations__}
CONVERSION_ATTR_TO_PARAM[daf.dtypes.FILE]["data"] = "hex"
CONVERSION_ATTR_TO_PARAM[daf.dtypes.FILE]["filename"] = "fullpath"


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


# Map whhich's values is a tuple that tells which fields are passwords.
# These fields will be replaced with a '*' when viewed in object form.
PASSWORD_PARAMS = {
    daf.ACCOUNT: {"token", "password", },
    daf.SeleniumCLIENT: {"password", },
}

CONVERSION_ATTR_TO_PARAM[daf.web.SeleniumCLIENT] = {k: f"_{k}" for k in daf.web.SeleniumCLIENT.__init__.__annotations__}
CONVERSION_ATTR_TO_PARAM[daf.web.SeleniumCLIENT].pop("return")


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
    property_map: Mapping[str, ObjectInfo]
        Mapping that maps a property (name) of the object into it's ObjectInfo.
    """
    CHARACTER_LIMIT = 150

    def __init__(
        self,
        class_,
        data: Mapping,
        real_object: it.ObjectReference = None,
        property_map: Mapping[str, "ObjectInfo"] = {}
    ) -> None:
        self.class_ = class_
        self.data = data
        self.real_object = real_object
        self.property_map = property_map
        self.__hash = 0
        self.__repr = None

    def __eq__(self, _value: object) -> bool:
        if isinstance(_value, ObjectInfo):
            cond = (
                self.class_ is _value.class_ and
                (   # Compare internal daf IDs for trackable objects (@track_id) in case a remote connection is present
                    getattr(self.real_object, "ref", None) ==
                    getattr(_value.real_object, "ref", None)
                ) and
                self.data == _value.data
            )
            return cond

        return False

    def __hash__(self) -> int:
        if not self.__hash:
            try:
                self.__hash = hash(self.data)
            except TypeError:
                self.__hash = -1

        return self.__hash

    def __repr__(self) -> str:
        if self.__repr is not None:
            return self.__repr

        _ret: str = self.class_.__name__ + "("
        private_params = PASSWORD_PARAMS.get(self.class_, set())
        if hasattr(self.class_, "__passwords__"):
            private_params = private_params.union(self.class_.__passwords__)

        for k, v in self.data.items():
            if len(_ret) > self.CHARACTER_LIMIT:
                break

            if isinstance(v, str):
                if k in private_params:
                    v = len(v) * '*'  # Hide password types

                v = f'"{v}"'
            else:
                v = str(v)

            _ret += f"{k}={v}, "

        _ret = _ret.rstrip(", ") + ")"
        if len(_ret) > self.CHARACTER_LIMIT:
            _ret = _ret[:self.CHARACTER_LIMIT] + "...)"

        self.__repr = _ret
        return _ret


@daf.misc.cache.cache_result(max=1024)
def convert_objects_to_script(object: Union[ObjectInfo, list, tuple, set, str]):
    """
    Converts ObjectInfo objects into equivalent Python code.
    """
    object_data = []
    import_data = []
    other_data = []

    if isinstance(object, ObjectInfo):
        object_str = f"{object.class_.__name__}(\n    "
        attr_str = []
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

            attr_str.append(f"{attr}={value},\n")
            if issubclass(type(value), Enum):
                import_data.append(f"from {type(value).__module__} import {type(value).__name__}")

        import_data.append(f"from {object.class_.__module__} import {object.class_.__name__}")

        object_str += "    ".join(''.join(attr_str).splitlines(True)) + ")"
        object_data.append(object_str)

    elif isinstance(object, (list, tuple, set)):
        _list_data = ["[\n"]
        for element in object:
            object_str, import_data_, other_str = convert_objects_to_script(element)
            _list_data.append(object_str + ",\n")
            import_data.extend(import_data_)
            other_data.append(other_str)

        _list_data = "    ".join(''.join(_list_data).splitlines(keepends=True)) + "]"
        object_data.append(_list_data)
    else:
        if isinstance(object, str):
            object = object.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')
            object_data.append(f'"{object}"')
        else:
            object_data.append(str(object))

    return ",".join(object_data).strip(), import_data, "\n".join(other_data).strip()


@daf.misc.cache.cache_result(16_384)
def convert_to_object_info(object_: object, save_original = False):
    """
    Converts an object into ObjectInfo.

    Parameters
    ---------------
    object_: object
        The object to convert.
    save_original: bool
        If True, will save the original object inside the ``real_object`` attribute of :class:`ObjectInfo`
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
                    data_conv[k] = convert_to_object_info(value, save_original)

        ret = ObjectInfo(object_type, data_conv)
        if save_original:
            ret.real_object = it.ObjectReference(it.get_object_id(object_))

            # Convert object properties
            # This will only be aviable for live objects, since it has no configuration value,
            # thus keeping it wouldn't make much sense
            if hasattr(object_, "_daf_id"):
                property_map = {}
                prop: property
                for name, prop in getmembers(type(object_), lambda x: isinstance(x, property)):
                    with suppress(AttributeError):
                        return_annotation = get_type_hints(prop.fget).get("return")
                        property_map[name] = (convert_to_object_info(prop.fget(object_), True), return_annotation)

                ret.property_map = property_map

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

    object_type = type(object_)
    if object_type in {int, float, str, bool, decimal.Decimal, type(None)} or isinstance(object_, Enum):
        if object_type is decimal.Decimal:
            object_ = float(object_)

        return object_

    if isinstance(object_, (set, list, tuple)):
        object_ = [convert_to_object_info(value, save_original) for value in object_]
        return object_

    attrs = get_conversion_map(object_type)
    return _convert_object_info(object_, save_original, object_type, attrs)


@daf.misc.cache.cache_result()
def _convert_to_objects_cached(*args, **kwargs):
    return convert_to_objects(*args, **kwargs)


def convert_to_objects(
    d: Union[ObjectInfo, dict, list],
    skip_real_conversion: bool = False,
    cached: bool = False
) -> Union[object, dict, List]:
    """
    Converts :class:`ObjectInfo` instances into actual objects,
    specified by the ObjectInfo.class_ attribute.

    Parameters
    -----------------
    d: ObjectInfo | list[ObjectInfo] | dict
        The object(s) to convert. Can be an ObjectInfo object, a list of ObjectInfo objects or a dictionary that is a
        mapping of ObjectInfo parameters.
    skip_real_conversion: bool
        If set to True the old real object will be returned without conversion has no effect.
        Defaults to False.
    cached: bool
        If True items will be returned from cache. ONLY USE FOR IMMUTABLE USE.
    """
    convert_func = _convert_to_objects_cached if cached else convert_to_objects

    def convert_object_info():
        # Skip conversion
        real = d.real_object
        if skip_real_conversion and real is not None:
            return real

        data_conv = {
            k:
            convert_func(v, skip_real_conversion, cached)
            if isinstance(v, (list, tuple, set, ObjectInfo, dict)) else v
            for k, v in d.data.items()
        }

        new_obj = d.class_(**data_conv)
        return new_obj

    if isinstance(d, (list, tuple, set)):
        return [convert_func(item, skip_real_conversion, cached) for item in d]
    if isinstance(d, ObjectInfo):
        return convert_object_info()
    if isinstance(d, dict):
        return {k: convert_func(v, skip_real_conversion, cached) for k, v in d.items()}

    return d


@daf.misc.cache.cache_result()
def convert_to_json(d: Union[ObjectInfo, List[ObjectInfo], Any]):
    """
    Converts ObjectInfo into JSON representation.
    """
    if isinstance(d, ObjectInfo):
        data_conv = {k: convert_to_json(v) for k, v in d.data.items()}
        return {"type": f"{d.class_.__module__}.{d.class_.__name__}", "data": data_conv}

    if isinstance(d, list):
        return [convert_to_json(x) for x in d]

    if issubclass((type_d := type(d)), Enum):
        return {"type": f"{type_d.__module__}.{type_d.__name__}", "value": d.value}

    return d


@daf.misc.cache.cache_result()
def convert_from_json(d: Union[dict, List[dict], Any]) -> ObjectInfo:
    """
    Converts previously converted JSON back to ObjectInfo.
    """
    if isinstance(d, list):
        result = [convert_from_json(item) for item in d]
        return result

    if isinstance(d, dict):
        type_ = import_class(d["type"])

        if "value" in d:  # Enum type or a single value type
            return type_(d["value"])

        return ObjectInfo(type_, {k: convert_from_json(v) for k, v in d["data"].items()})

    return d


def convert_dict_to_object_info(data: Union[dict, Iterable, Any]):
    """
    Method that converts a dict JSON into
    It's object representation inside the GUI, that is ObjectInfo.

    Parameters
    -----------
    data: str
        The JSON data to convert.
    """
    class DictView:
        def __init__(self) -> None:
            raise NotImplementedError

    annotations = {}
    object_info_data = {}

    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict):
                v = convert_dict_to_object_info(v)
                type_v = type(v)
            elif isinstance(v, (list, tuple, set)):
                v = convert_dict_to_object_info(v)
                type_v = List[Any]
            else:
                type_v = type(v)

            annotations[k] = type_v
            object_info_data[k] = v

        DictView.__init__.__annotations__ = annotations
        return ObjectInfo(DictView, object_info_data)
    elif isinstance(data, (list, tuple, set)):
        return [convert_dict_to_object_info(x) for x in data]
    else:
        return data
