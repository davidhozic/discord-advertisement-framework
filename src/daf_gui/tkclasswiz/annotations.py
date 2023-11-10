"""
Module used for managing annotations.
"""
from typing import Union, List, Optional
from contextlib import suppress
from inspect import isclass

import datetime as dt

import _discord as discord
import daf


__all__ = (
    "register_annotations",
    "get_annotations",
)


ADDITIONAL_ANNOTATIONS = {
    dt.timedelta: {
        "days": float,
        "seconds": float,
        "microseconds": float,
        "milliseconds": float,
        "minutes": float,
        "hours": float,
        "weeks": float
    },
    dt.datetime: {
        "year": int,
        "month": Union[int, None],
        "day": Union[int, None],
        "hour": int,
        "minute": int,
        "second": int,
        "microsecond": int,
        "tzinfo": dt.timezone
    },
    dt.timezone: {
        "offset": dt.timedelta,
        "name": str
    },
    discord.Embed: {
        "colour": Union[int, discord.Colour, None],
        "color": Union[int, discord.Colour, None],
        "title": Union[str, None],
        "type": discord.embeds.EmbedType,
        "url": Union[str, None],
        "description": Union[str, None],
        "timestamp": Union[dt.datetime, None],
        "fields": Union[List[discord.EmbedField], None],
        "author": Union[discord.EmbedAuthor, None],
        "footer": Union[discord.EmbedFooter, None],
        "image": Union[str, discord.EmbedMedia, None],
        "thumbnail": Union[str, discord.EmbedMedia, None],
    },
    discord.EmbedAuthor: {
        "name": str,
        "url": Union[str, None],
        "icon_url": Union[str, None]
    },
    discord.EmbedFooter: {
        "text": str,
        "icon_url": Union[str, None]
    },
    discord.EmbedMedia: {
        "url": str
    },
    discord.Intents: {k: bool for k in discord.Intents.VALID_FLAGS},
    discord.EmbedField: {
        "name": str, "value": str, "inline": bool
    },
    discord.TextChannel: {
        "name": str,
        "id": int
    },
    daf.add_object: {
        "obj": daf.ACCOUNT
    },
}

ADDITIONAL_ANNOTATIONS[discord.VoiceChannel] = ADDITIONAL_ANNOTATIONS[discord.TextChannel]
ADDITIONAL_ANNOTATIONS[discord.Guild] = ADDITIONAL_ANNOTATIONS[discord.TextChannel]
ADDITIONAL_ANNOTATIONS[discord.User] = ADDITIONAL_ANNOTATIONS[discord.Guild]


def register_annotations(cls: type, mapping: Optional[dict] = {}, **annotations):
    """
    Extends original annotations of ``cls``.

    This can be useful eg. when the class your
    are adding is not part of your code and is also not annotated.

    Parameters
    ------------
    cls: type
        The class (or function) to register additional annotations on.
    """
    if cls not in ADDITIONAL_ANNOTATIONS:
        ADDITIONAL_ANNOTATIONS[cls] = {}

    ADDITIONAL_ANNOTATIONS[cls].update(**annotations, **mapping)


def get_annotations(class_) -> dict:
    """
    Returns class / function annotations including the ones extended with ``register_annotations``.
    It does not return the return annotation.
    """
    annotations = {}
    with suppress(AttributeError):
        if isclass(class_):
            annotations = class_.__init__.__annotations__
        else:
            annotations = class_.__annotations__

    additional_annotations = ADDITIONAL_ANNOTATIONS.get(class_, {})
    annotations = {**annotations, **additional_annotations}

    if "return" in annotations:
        del annotations["return"]

    return annotations
