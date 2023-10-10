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


def get_value(obj, attr: str, extra_ignore: set=set()):
    custom_key_map = {
        asyncio.Semaphore: lambda sem: (sem.locked(), sem._value),
        daf.discord.Intents: lambda intents: {k: getattr(intents, k) for k in daf.discord.Intents.VALID_FLAGS},
        asyncio.Lock: lambda lock: (lock._locked)
    }

    ignore_attrs = {}

    global_ignores = {
        "_sa_class_manager",
        "_sa_registry",
        "_created_at",
        "_id",
        "_event_ctrl"
    }

    default_key = lambda x: x
    value = getattr(obj, attr, None)
    key = custom_key_map.get(type(value), default_key)
    ignore = ignore_attrs.get(type(obj), set())
    if attr in ignore or attr in global_ignores or attr in extra_ignore:
        return None

    return key(value)


def compare_objects(obj1, obj2, extra_ignore=set()):
    assert type(obj1) is type(obj2)

    for attr in get_attrs(obj1):
        val_obj1 = get_value(obj1, attr, extra_ignore)
        val_obj2 = get_value(obj2, attr, extra_ignore)

        if get_attrs(val_obj1) and not inspect.isclass(val_obj1):
            compare_objects(val_obj1, val_obj2)
        else:
            assert val_obj1 == val_obj2
