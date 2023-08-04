"""
Testing helper utilities.
"""
import asyncio
import daf
import inspect


def get_attrs(obj):
    slots = set()
    slots.update(daf.misc.get_all_slots(type(obj)))
    slots.update(getattr(obj, "__dict__", {}.keys()))
    return slots


def get_value(obj, attr: str):
    custom_key_map = {
        asyncio.Semaphore: lambda sem: (sem.locked(), sem._value),
    }

    ignore_attrs = {}
    global_ignores = {
        "_sa_class_manager",
        "_sa_registry",
        "_created_at",
        "_id"
    }

    default_key = lambda x: x
    value = getattr(obj, attr, None)
    key = custom_key_map.get(type(value), default_key)
    ignore = ignore_attrs.get(type(obj), set())
    if attr in ignore or attr in global_ignores:
        return 0

    return key(value)


def compare_objects(obj1, obj2):
    assert type(obj1) is type(obj2)

    for attr in get_attrs(obj1):
        val_obj1 = get_value(obj1, attr)
        val_obj2 = get_value(obj2, attr)

        if get_attrs(val_obj1) and not inspect.isclass(val_obj1):
            compare_objects(val_obj1, val_obj2)
        else:
            assert val_obj1 == val_obj2
