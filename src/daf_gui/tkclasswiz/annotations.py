"""
Module used for managing annotations.
"""
from datetime import datetime, timedelta, timezone
from typing import Union, Optional
from contextlib import suppress
from inspect import isclass


__all__ = (
    "register_annotations",
    "get_annotations",
)


ADDITIONAL_ANNOTATIONS = {
    timedelta: {
        "days": float,
        "seconds": float,
        "microseconds": float,
        "milliseconds": float,
        "minutes": float,
        "hours": float,
        "weeks": float
    },
    datetime: {
        "year": int,
        "month": Union[int, None],
        "day": Union[int, None],
        "hour": int,
        "minute": int,
        "second": int,
        "microsecond": int,
        "tzinfo": timezone
    },
    timezone: {
        "offset": timedelta,
        "name": str
    },
}


def register_annotations(cls: type, mapping: Optional[dict] = {}, **annotations):
    """
    Extends original annotations of ``cls``.

    This can be useful eg. when the class your
    are adding is not part of your code and is also not annotated.

    Parameters
    ------------
    cls: type
        The class (or function) to register additional annotations on.
    mapping: Optional[Dict[str, type]]
        Mapping mapping the parameter name to it's type.
    annotations: Optional[Unpack[str, type]]
        Keyword arguments mapping parameter name to it's type (``name=type``).

    Example
    -----------
    
    .. code-block:: python

        from datetime import timedelta, timezone

        register_annotations(
            timezone,
            offset=timedelta,
            name=str
        )    
    """
    if cls not in ADDITIONAL_ANNOTATIONS:
        ADDITIONAL_ANNOTATIONS[cls] = {}

    ADDITIONAL_ANNOTATIONS[cls].update(**annotations, **mapping)


def get_annotations(class_) -> dict:
    """
    Returns class / function annotations including the ones extended with ``register_annotations``.
    It does not return the return annotation.
    """
    annotations = {}
    with suppress(AttributeError):
        if isclass(class_):
            annotations = class_.__init__.__annotations__
        else:
            annotations = class_.__annotations__

    additional_annotations = ADDITIONAL_ANNOTATIONS.get(class_, {})
    annotations = {**annotations, **additional_annotations}

    if "return" in annotations:
        del annotations["return"]

    return annotations
