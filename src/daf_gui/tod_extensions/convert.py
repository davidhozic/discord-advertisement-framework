"""
Module implements conversion extensions.
"""
from typing import get_type_hints
from inspect import getmembers

from tkclasswiz.convert import ObjectInfo, convert_to_object_info

from daf.misc.instance_track import ObjectReference, get_object_id
from daf.logging.tracing import *



def load_extension_to_object_info(object_, ret: ObjectInfo, *, save_original = False):
    if save_original and isinstance(ret, ObjectInfo):
        ret.real_object = ObjectReference(get_object_id(object_))

        # Convert object properties
        # This will only be aviable for live objects, since it has no configuration value,
        # thus keeping it wouldn't make much sense
        if hasattr(object_, "_daf_id"):
            property_map = {}
            prop: property
            for name, prop in getmembers(type(object_), lambda x: isinstance(x, property)):
                if name.startswith("_"):  # Don't obtain private properties
                    continue

                try:
                    return_annotation = get_type_hints(prop.fget).get("return")
                    property_map[name] = (convert_to_object_info(prop.fget(object_)), return_annotation)
                except Exception as exc:
                    trace(
                        f"Unable to get property {name} in {object_} when converting to ObjectInfo",
                        TraceLEVELS.ERROR,
                        exc
                    )

            ret.property_map = property_map

    return ret
