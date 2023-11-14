"""
Modules contains definitions related to GUI object transformations.
"""

from typing import Any, Union, List, Generic, TypeVar, Mapping, Optional
from contextlib import suppress
from inspect import signature
from enum import Enum

from .utilities import import_class
from .extensions import extendable
from .cache import cache_result
from .annotations import *

import datetime as dt
import warnings
import decimal


__all__ = (
    "ObjectInfo",
    "convert_to_objects",
    "convert_to_object_info",
    "convert_to_json",
    "convert_from_json",
    "convert_objects_to_script",
)

TClass = TypeVar("TClass")


CONVERSION_ATTR_TO_PARAM = {
    dt.timezone: {
        "offset": lambda timezone: timezone.utcoffset(None),
        "name": lambda timezone: timezone.tzname(None)
    },
}


def register_object_objectinfo_rule(cls: type, mapping: Optional[dict] = {}, **kwargs):
    """
    Used for adding new conversion rules when converting from Python objects
    into abstract ObjectInfo objects (GUI objects).

    These rules will be used when calling the ``convert_to_object_info`` function.

    If rules for ``cls`` do not exist, the conversion function will assume parameters
    are located under the same attribute name.

    A neat way to avoid registering custom conversion rules, is to store the attributes either under
    the same name as the parameter, or store them under a different name and create a ``@property``
    getter which has the same name as the parameter.

    Parameters
    ------------
    mapping: Optional[Dict[str, Union[Callable[[T], Any]], str]]
        Mapping mapping the parameter name to attribute from which to obtain the value.
        Values of mapping can also be a getter function, that accepts the object as parameter.
    kwargs: Optional[Unpack[str, Union[Callable[[T], Any]], str]]
        Keyword arguments mapping parameter name to attribute names from which to obtain the value.
        Values of mapping can also be a getter function, that accepts the object as parameter.

    Example
    ----------
    .. code-block:: python
        class FILE:
            def __init__(self, filename: str):
                self.fullpath = filename

        register_object_objectinfo_rule(
            FILE,
            filename="fullpath"
        )

        # Timezone
        import datetime
        register_object_objectinfo_rule(
            datetime.timezone,
            offset=lambda timezone: timezone.utcoffset(None)
        )
    """

    if cls not in CONVERSION_ATTR_TO_PARAM:
        CONVERSION_ATTR_TO_PARAM[cls] = {}

    CONVERSION_ATTR_TO_PARAM[cls].update(**kwargs, **mapping)


def get_object_objectinfo_rule_map(cls: type) -> dict:
    """
    Returns the conversion mapping for ``cls``

    Returns
    ----------
    Dict[str, Union[Callable[[T], Any]], str]
        Mapping of parameter name to the attribute name or getter function.
    """
    return CONVERSION_ATTR_TO_PARAM.get(cls, {})


@extendable
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
    """
    CHARACTER_LIMIT = 150

    def __init__(
        self,
        class_,
        data: Mapping,
    ) -> None:
        self.class_ = class_
        self.data = data
        self.__hash = 0
        self.__repr = None

    @extendable
    def __eq__(self, _value: object) -> bool:
        if isinstance(_value, ObjectInfo):
            return self.class_ is _value.class_ and self.data == _value.data

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
        private_params = set()
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


@cache_result(max=1024)
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


@extendable
@cache_result(16_384)
def convert_to_object_info(object_: object, **kwargs):
    """
    Converts an object into ObjectInfo.

    Parameters
    ---------------
    object_: object
        The object to convert.
    """
    def _convert_object_info(object_, object_type, attrs):
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
                    data_conv[k] = convert_to_object_info(value, **kwargs)

        ret = ObjectInfo(object_type, data_conv)
        return ret

    def get_conversion_map(object_type):
        attrs = CONVERSION_ATTR_TO_PARAM.get(object_type)
        if attrs is None:
            attrs = {k:k for k in get_annotations(object_type)}

        attrs.pop("return", None)
        return attrs

    object_type = type(object_)
    if object_type in {int, float, str, bool, decimal.Decimal, type(None)} or isinstance(object_, Enum):
        if object_type is decimal.Decimal:
            object_ = float(object_)

        return object_

    if isinstance(object_, (set, list, tuple)):
        object_ = [convert_to_object_info(value, **kwargs) for value in object_]
        return object_
    
    if isinstance(object_, dict):
        return ObjectInfo(
            dict,
            {k: convert_to_object_info(v, **kwargs) for k, v in object_.items()},
        )


    attrs = get_conversion_map(object_type)
    return _convert_object_info(object_, object_type, attrs)


@cache_result()
def _convert_to_objects_cached(*args, **kwargs):
    return convert_to_objects(*args, **kwargs)


def convert_to_objects(
    d: Union[ObjectInfo, dict, list],
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
    cached: bool
        If True items will be returned from cache. ONLY USE FOR IMMUTABLE USE.
    """
    convert_func = _convert_to_objects_cached if cached else convert_to_objects

    def convert_object_info():
        data_conv = {
            k:
            convert_func(v, cached)
            if isinstance(v, (list, tuple, set, ObjectInfo, dict)) else v
            for k, v in d.data.items()
        }

        new_obj = d.class_(**data_conv)
        return new_obj

    if isinstance(d, (list, tuple, set)):
        return [convert_func(item, cached) for item in d]
    if isinstance(d, ObjectInfo):
        return convert_object_info()
    if isinstance(d, dict):
        return {k: convert_func(v, cached) for k, v in d.items()}

    return d


@cache_result()
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


@cache_result()
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

        annotations = get_annotations(type_)
        data = {}
        for k, v in d["data"].items():
            if k in annotations:
                data[k] = convert_from_json(v)
            else:
                warnings.warn(f"Parameter {k} does not exist in {type_}, ignoring.")

        return ObjectInfo(type_, data)

    return d
