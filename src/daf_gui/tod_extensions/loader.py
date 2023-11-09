"""
Extension loader method.
"""
from ..tk_object_define.object_frame.frame_struct import NewObjectFrameStruct
from ..tk_object_define.convert import ObjectInfo
from ..tk_object_define.extensions import Extension

from . import deprecation_notice
from . import extra_widgets
from . import help_button
from . import method_execution
from . import live_objects


def register_extensions():
    NewObjectFrameStruct.register_extension(Extension("Deprecation notice", "1.0.0", deprecation_notice.load_extension))
    NewObjectFrameStruct.register_extension(Extension("Extra widgets", "1.0.0", extra_widgets.load_extension))
    NewObjectFrameStruct.register_extension(Extension("Help button", "1.0.0", help_button.load_extension))
    NewObjectFrameStruct.register_extension(Extension("Method execution", "1.0.0", method_execution.load_extension))
    NewObjectFrameStruct.to_object.register_extension(
        Extension("Live objects to_object", "1.0.0", live_objects.load_extension_oi_to_object),
    )

    ObjectInfo.register_extension(Extension("Live objects", "1.0.0", live_objects.load_extension_oi))
    ObjectInfo.__eq__.register_extension(Extension("Live objects EQ", "1.0.0", live_objects.load_extension_oi_eq))
