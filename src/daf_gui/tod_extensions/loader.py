"""
Extension loader method.
"""
from inspect import getmembers, isclass
from typing import Union, List
from datetime import datetime, time, timezone

from tkclasswiz.convert import (
    ObjectInfo,
    convert_to_object_info,
    register_object_objectinfo_rule,
)
from tkclasswiz.annotations import register_annotations as reg_annotations, get_annotations
from tkclasswiz.object_frame.frame_struct import NewObjectFrameStruct
from tkclasswiz.extensions import Extension
from tkclasswiz.deprecation import register_deprecated

from . import deprecation_notice
from . import method_execution
from . import extra_widgets
from . import live_objects
from . import help_button
from . import convert

import _discord as discord
import daf


def register_extensions():
    NewObjectFrameStruct.register_post_extension(Extension("Deprecation notice", "1.0.0", deprecation_notice.load_extension))
    NewObjectFrameStruct.register_post_extension(Extension("Extra widgets", "1.0.0", extra_widgets.load_extension))
    NewObjectFrameStruct.register_post_extension(Extension("Help button", "1.0.0", help_button.load_extension))
    NewObjectFrameStruct.register_post_extension(Extension("Method execution", "1.0.0", method_execution.load_extension))
    NewObjectFrameStruct.to_object.register_post_extension(
        Extension("Live objects to_object", "1.0.0", live_objects.load_extension_oi_to_object),
    )
    NewObjectFrameStruct.load.register_pre_extension(
        Extension("Live Objects preserve after load", "1.0.0", live_objects.load_extension_oi_load)
    )

    ObjectInfo.register_post_extension(Extension("Live objects", "1.0.0", live_objects.load_extension_oi))
    ObjectInfo.__eq__.register_post_extension(Extension("Live objects EQ", "1.0.0", live_objects.load_extension_oi_eq))
    convert_to_object_info.register_post_extension(
        Extension("Live object save_original", "1.0.0", convert.load_extension_to_object_info)
    )


def register_deprecations():
    register_deprecated(daf.AutoGUILD, "include_pattern", str)
    register_deprecated(daf.AutoGUILD, "exclude_pattern")

    register_deprecated(daf.AutoCHANNEL, "include_pattern", str)
    register_deprecated(daf.AutoCHANNEL, "exclude_pattern")

    register_deprecated(daf.BaseMESSAGE, "start_period")
    register_deprecated(daf.BaseMESSAGE, "end_period")
    register_deprecated(daf.BaseMESSAGE, "start_in")
    register_deprecated(daf.messagedata.dynamicdata._DeprecatedDynamic)
    register_deprecated(daf._FunctionBaseCLASS)
    register_deprecated(
        daf.BaseMESSAGE,
        "data",
        str, daf.discord.Embed, daf.FILE, list, tuple, set
    )

def register_annotations():
    reg_annotations(
        time,
        hour=int, minute=int, second=int, microsecond=int, tzinfo=timezone
    )

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


def register_conversions():
    # ACCOUNT
    register_conv_clients()

    # FILE
    register_conv_datatypes()

    # xMESSAGE
    register_conv_message()

    # GUILD
    register_conv_guild()

    # PyCord
    reg_conv_pycord()

    sql = daf.sql
    if sql.SQL_INSTALLED:
        register_conv_sql(sql)


def reg_conv_pycord():
    for cls in (discord.TextChannel, discord.VoiceChannel, discord.Thread, discord.User, discord.Guild):
        register_object_objectinfo_rule(
            cls,
            name="name",
            id="id"
        )

def register_conv_clients():
    m = {k: k for k in daf.client.ACCOUNT.__init__.__annotations__}
    m["token"] = "_token"
    m["username"] = lambda account: account.selenium._username if account.selenium is not None else None
    m["password"] = lambda account: account.selenium._password if account.selenium is not None else None
    del m["return"]
    register_object_objectinfo_rule(
        daf.client.ACCOUNT,
        m
    )


def register_conv_datatypes():
    m = {k: k for k in daf.FILE.__init__.__annotations__}
    m["data"] = "hex"
    m["filename"] = "fullpath"
    register_object_objectinfo_rule(
        daf.FILE,
        m
    )


def register_conv_guild():
    m = {k: k for k in daf.GUILD.__init__.__annotations__}
    m["invite_track"] = (
        lambda guild_: list(guild_.join_count.keys())
    )
    register_object_objectinfo_rule(
        daf.guild.GUILD,
        m
    )
    
    # AutoGUILD
    m = {k: k for k in daf.AutoGUILD.__init__.__annotations__}
    m["invite_track"] = (
        lambda guild_: list(guild_._invite_join_count.keys())
    )
    register_object_objectinfo_rule(
        daf.guild.AutoGUILD,
        m
    )

    register_object_objectinfo_rule(
        daf.web.SeleniumCLIENT,
        {k: f"_{k}" for k in get_annotations(daf.web.SeleniumCLIENT)}
    )


    register_object_objectinfo_rule(
        daf.discord.Guild,
        {"name": "name", "id": "id"}
    )


def register_conv_message():
    def get_period(message: daf.BaseMESSAGE):
        if isinstance(message.parent, daf.AutoGUILD):
            # Convert the start_in to the highest possible next_send_time
            # of any message copies inside AutoGUILD
            ag = message.parent
            max_next_send = datetime.now().astimezone().replace(year=1970)
            max_period_obj = None
            m: daf.BaseMESSAGE
            for guild in ag.guilds:
                for m in guild.messages:
                    if message == m and (period := m.period.get()) > max_next_send:
                        max_next_send = period
                        max_period_obj = m.period

            return max_period_obj

        # Not in AutoGUILD => Initialized, next_send_time should be start_in
        return message.period

    for item in {daf.TextMESSAGE, daf.VoiceMESSAGE, daf.DirectMESSAGE}:
        m = {k: k for k in item.__init__.__annotations__}
        m["data"] = "_data"
        m["period"] = get_period
        register_object_objectinfo_rule(item, m)

    channels = lambda message_: (
        [x if isinstance(x, int) else x.id for x in message_.channels]
        if not isinstance(message_.channels, daf.AutoCHANNEL)
        else message_.channels
    )
    register_object_objectinfo_rule(
        daf.TextMESSAGE, 
        channels=channels
    )

    register_object_objectinfo_rule(
        daf.VoiceMESSAGE,
        channels=channels        
    )


def register_conv_sql(sql):
    register_object_objectinfo_rule(
            sql.MessageLOG,
            {
                "id": "id",
                "timestamp": "timestamp",
                "success_rate": "success_rate",
            }
        )

    register_object_objectinfo_rule(
            sql.InviteLOG,
            {
                "id": "id",
                "timestamp": "timestamp",
            }
        )

    for name, cls in getmembers(sql.tables, lambda x: isclass(x) and hasattr(x.__init__, "_sa_original_init")):
        annots = cls.__init__._sa_original_init.__annotations__.copy()
        annots.pop('return', None)
        register_object_objectinfo_rule(
                cls,
                {k: k for k in annots}
            )

