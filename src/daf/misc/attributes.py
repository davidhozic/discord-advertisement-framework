"""
Attribute manipulation utitilities.
"""
from typing import Any
from itertools import chain
from contextlib import suppress
from inspect import _empty


__all__ = (
    "write_non_exist",
    "get_all_slots",
)


def write_non_exist(obj: Any, name: str, value: Any):
    """
    Method that assigns an attribute only if it does not already exist.
    This is to prevent any ``.update()`` method calls from resetting critical
    variables that should not be changed,
    even if the objects goes thru initialization again.

    Parameters
    -------------
    obj: Any
        Object to safely write.

    name: str
        The name of the attribute to change.

    value: Any
        The value to change the attribute with.
    """
    # Write only if forced, or if not forced, then the attribute must not exist
    if getattr(obj, name, None) is None:
        setattr(obj, name, value)


def get_all_slots(cls) -> list:
    """
    Returns slots of current class and it's bases. Skips the __weakref__ slot.
    Also returns internal_daf_id descriptor for tracked objects
    """
    ret = list(chain.from_iterable(getattr(class_, '__slots__', []) for class_ in cls.__mro__))

    with suppress(ValueError):
        ret.remove("__weakref__")

    return ret
