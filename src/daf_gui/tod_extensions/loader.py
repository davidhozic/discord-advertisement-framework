"""
Extension loader method.
"""
from datetime import datetime
from typing import Union, List

from ..tkclasswiz.object_frame.frame_struct import NewObjectFrameStruct

from ..tkclasswiz.convert import ObjectInfo, convert_to_object_info
from ..tkclasswiz.extensions import Extension
from ..tkclasswiz.annotations import register_annotations as reg_annotations

from . import deprecation_notice
from . import extra_widgets
from . import help_button
from . import method_execution
from . import live_objects
from . import convert

import _discord as discord
import daf



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
    convert_to_object_info.register_extension(
        Extension("Live object save_original", "1.0.0", convert.load_extension_to_object_info)
    )


def register_annotations():
    reg_annotations(
        discord.Embed,
        {
            "colour": Union[int, discord.Colour, None],
            "color": Union[int, discord.Colour, None],
            "title": Union[str, None],
            "type": discord.embeds.EmbedType,
            "url": Union[str, None],
            "description": Union[str, None],
            "timestamp": Union[datetime, None],
            "fields": Union[List[discord.EmbedField], None],
            "author": Union[discord.EmbedAuthor, None],
            "footer": Union[discord.EmbedFooter, None],
            "image": Union[str, discord.EmbedMedia, None],
            "thumbnail": Union[str, discord.EmbedMedia, None],
        }
    )

    reg_annotations(
        discord.EmbedAuthor,
        {
            "name": str,
            "url": Union[str, None],
            "icon_url": Union[str, None]
        }
    )

    reg_annotations(
        discord.EmbedFooter,
        {
            "text": str,
            "icon_url": Union[str, None]
        }    
    )

    reg_annotations(
        discord.EmbedMedia,
        url=str
    )

    reg_annotations(
        discord.Intents,
        {k: bool for k in discord.Intents.VALID_FLAGS}
    )

    reg_annotations(
        discord.EmbedField,
        {
            "name": str, "value": str, "inline": bool
        }
    )

    reg_annotations(
        daf.add_object,
        obj=daf.ACCOUNT
    )
