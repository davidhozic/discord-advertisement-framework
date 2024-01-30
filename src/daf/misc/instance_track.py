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
    "Returns either internal daf's ID"
    return getattr(obj, "_daf_id")


class ObjectReference:
    """
    Descriptive class that describes a reference to an object
    instead of the object itself. Useful for reducing unneeded storage.
    """
    def __init__(self, ref: int, remote_allowed = True) -> None:
        self.ref = ref
        self.remote_allowed = remote_allowed  # Can be transferred, but not manipulated

    @classmethod
    def from_object(cls, obj: object):
        if not hasattr(obj, "_daf_id") or obj._daf_id == -1:
            return None

        return cls(get_object_id(obj), obj._tracked_allow_remote)


TRACK_DEFAULT_ATTR = {
    "_daf_id": -1,
    "_tracked_allow_remote": True
}

def track_id(cls):
    """
    Decorator which replaces the __new__ method with a function that keeps a weak reference.
    """
    @wraps(cls, updated=[])
    class TrackedClass(cls):
        if hasattr(cls, "__slots__") and cls.__slots__:  # Don't break classes without slots
            __slots__ = ["_daf_id", "_tracked_allow_remote"]
            if not hasattr(cls, "__weakref__"):
                __slots__.append('__weakref__')

            __slots__ = tuple(__slots__)


        def _update_tracked_id(self, allow_remote: bool = True):
            """
            Saves ID to the tracked dictionary

            Parameters
            --------------
            allow_remote: bool
                Should a remote client be able to manipulate the object.
                If this is False, the object will be tracked but refresh,
                update and method execution will not be available.
            """
            self._tracked_allow_remote = allow_remote
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

            value = TRACK_DEFAULT_ATTR.get(__key)
            if value is not None:
                return value

            raise AttributeError(__key)

    return TrackedClass
