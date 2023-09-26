"""
Utility module for tracking instances
based on ID.
"""
from weakref import WeakValueDictionary
from functools import wraps


__all__ = (
    "get_by_id",
    "get_object_id",
    "ObjectReference",
    "track_id",
)

OBJECT_ID_MAP = WeakValueDictionary()


def get_by_id(id_: int):
    """
    Returns an object from it's id().
    """
    try:
        return OBJECT_ID_MAP[id_]
    except KeyError as exc:
        raise KeyError("Object not present in DAF.") from exc


def get_object_id(obj: object) -> int:
    "Returns either internal daf's ID if it exist otherwise just the regular id()"
    return getattr(obj, "_daf_id", -1)


class ObjectReference:
    """
    Descriptive class that describes a reference to an object
    instead of the object itself. Useful for reducing unneeded storage.
    """
    def __init__(self, ref: int) -> None:
        self.ref = ref


def track_id(cls):
    """
    Decorator which replaces the __new__ method with a function that keeps a weak reference.
    """
    @wraps(cls, updated=[])
    class TrackedClass(cls):
        if hasattr(cls, "__slots__"):  # Don't break classes without slots
            __slots__ = ("__weakref__", "_daf_id")

        def _update_tracked_id(self):
            "Saves ID to the tracked dictionary"
            value = id(self)
            self._daf_id = value
            OBJECT_ID_MAP[value] = self

        @wraps(cls.initialize)
        async def initialize(self, *args, **kwargs):
            _r = await super().initialize(*args, **kwargs)
            self._update_tracked_id()
            return _r

        def __getattr__(self, __key: str):
            "Method that gets called whenever an attribute is not found."
            if __key == "_daf_id":
                return -1

            raise AttributeError(__key)

    return TrackedClass
