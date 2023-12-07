"""
Implements live object tracking to ObjectInfo.
"""
from collections.abc import Mapping
from tkclasswiz.convert import ObjectInfo
from daf.misc.instance_track import ObjectReference


def load_extension_oi(frame: ObjectInfo, *args, **kwargs):
    # Additional widgets
    frame.real_object: ObjectReference = None
    frame.property_map: Mapping[str, "ObjectInfo"] = {}

def load_extension_oi_eq(self, other: ObjectInfo, result: bool):
    return result and self.real_object == other.real_object

def load_extension_oi_to_object(self, result_object_info: ObjectInfo, **kwargs):
    if (old_gui_data := self.old_gui_data) is not None:
        # Don't erase the bind to the real object in case this is an edit of an existing ObjectInfo
        result_object_info.real_object = old_gui_data.real_object
        # Also don't erase any saved properties if received from a live object.
        result_object_info.property_map = old_gui_data.property_map

    return result_object_info

def load_extension_oi_load(self, old_data: ObjectInfo, *args, **kwargs):
    if self.old_gui_data is not None:  # Preserve the old reference, even if reloading data
        old_data.real_object = self.old_gui_data.real_object
        old_data.property_map = self.old_gui_data.property_map
