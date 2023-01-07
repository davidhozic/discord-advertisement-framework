"""
    The module contains definitions regarding the data types
    you can send using the xxxMESSAGE objects.
"""
from typing import Any, Callable, List, Union, TypeVar, Coroutine
from contextlib import suppress
from typeguard import typechecked
from urllib.parse import urlparse
from .logging.tracing import trace, TraceLEVELS

from . import misc

import copy
import datetime
import _discord as discord


T = TypeVar("T")

__all__ = (
    "data_function",
    "_FunctionBaseCLASS",
    "EMBED",
    "FILE",
    "AUDIO"
)

class GLOBALS:
    "Storage class used for storing global variables"
    voice_installed: bool = False

# --------------------------------- Optional modules --------------------------------- #
try:
    import yt_dlp
    import nacl
    GLOBALS.voice_installed = True
except ModuleNotFoundError:
    GLOBALS.voice_installed = False
# ------------------------------------------------------------------------------------ #


#######################################################################
# Decorators
#######################################################################
class _FunctionBaseCLASS:
    """
    Used as a base class to FunctionCLASS which gets created in :ref:`data_function` decorator.
    Because the FunctionCLASS is inaccessible outside the :ref:`data_function` decorator,
    this class is used to detect if the MESSAGE.data parameter is of function type,
    because the function isinstance also returns True when comparing
    the object to it's class or to the base class from which the object class is inherited from.
    """

@misc.doc_category("Message data types")
def data_function(fnc: Callable):
    """
    Decorator used for wrapping a function that will return data to send when the message is ready.

    The ``fnc`` function must return data that is of type that the **x**\ MESSAGE object supports.
    **If the type returned is not valid, the send attempt will simply be ignored and nothing will be logged at at**,
    this is useful if you want to use the ``fnc`` function to control whenever the message is ready to be sent.
    For example: if we have a function defined like this:

    .. code-block::
        :emphasize-lines: 3

        @daf.data_function
        def get_data():
            return None
    
        ...
        daf.TextMESSAGE(..., data=get_data())
        ...

    then no messages will ever be sent, nor will any logs be made since invalid values are simply ignored by the framework.



    Parameters
    ------------
    fnc: Callable
        The function to wrap.

    Returns
    -----------
    FunctionCLASS
        A class for creating wrapper objects is returned. These wrapper objects can be used as
        a ``data`` parameter to the :ref:`Messages` objects.


    .. literalinclude:: ../../../Examples/Message Types/TextMESSAGE/main_data_function.py
        :language: python
        :emphasize-lines: 11, 24
    """

    class FunctionCLASS(_FunctionBaseCLASS):
        """
        Used for creating special classes that are then used to create objects in the daf.MESSAGE
        data parameter, allows for sending dynamic content received thru an user defined function.

        Parameters
        -----------
        - Custom number of positional and keyword arguments.

        .. literalinclude:: ../../Examples/Message Types/TextMESSAGE/main_data_function.py
            :language: python
        """
        __slots__ = (
            "args",
            "kwargs",
            "func_name",
        )

        def __init__(self, *args: Any, **kwargs: Any):
            self.args = args
            self.kwargs = kwargs
            self.func_name = fnc.__name__

        async def retrieve(self):
            """
            Retrieves the data from the user function.
            """
            _ = fnc(*self.args, **self.kwargs)
            if isinstance(_, Coroutine):
                return await _
            return _
        
        def __str__(self) -> str:
            return self.func_name

    return FunctionCLASS


#######################################################################
# Other
#######################################################################
@typechecked
class EMBED(discord.Embed):
    """

    .. deprecated:: v2.2
        Use :class:`discord.Embed` instead.
    
    .. WARNING::
        USING this is NOT recommended as it is planned for removal.
        Use :class:`discord.Embed` instead.

    Derived class of :class:`discord.Embed` created to provide additional arguments in the creation.

    **Original parameters** from **PyCord**: `PyCord docs <https://docs.pycord.dev/en/master/api.html?highlight=discord%20embed#discord.Embed>`_

    Parameters
    -------------
    author_name: str
        Name of embed author
    author_icon: str
        Url to author image.
    image: str
        Url of image to be placed at the end of the embed.
    thumbnail: str
        Url of image that will be placed at the top right of embed.
    """
    __slots__ = discord.Embed.__slots__
    # Static members
    Color = Colour = discord.Color  # Used for color parameter
    EmptyEmbed = discord.embeds.EmptyEmbed

    @staticmethod
    def from_discord_embed(_object : discord.Embed):
        """
        Creates an EMBED object from a discord.Embed object

        Parameters
        ------------
        _object: discord.Embed
            The Discord Embed object you want converted into a daf.discord.Embed object.
        """
        ret = EMBED()
        # Copy attributes but not special methods to the new EMBED. "dir" is used instead of "vars" because the object does not support the function.
        for key in dir(_object):
            if not key.startswith("__") and not key.endswith("__"):
                with suppress(AttributeError,TypeError):
                    if (not callable(getattr(_object, key))
                        and not isinstance(getattr(_object.__class__, key), property)
                        and getattr(_object,key) is not discord.embeds.EmptyEmbed
                    ):
                        setattr(ret, key, copy.deepcopy(getattr(_object,key)))

        return ret

    def __init__(self, *,
                # Additional parameters
                author_name: str=None,
                author_icon: str=EmptyEmbed,
                image: str= None,
                thumbnail : str = None,
                fields : List[discord.EmbedField] = None,
                # Base class parameters
                colour: Union[int, Colour] = EmptyEmbed,
                color: Union[int, Colour] = EmptyEmbed,
                title: str = EmptyEmbed,
                type : str = "rich",
                url: str= EmptyEmbed,
                description = EmptyEmbed,
                timestamp: datetime.datetime = None):

        trace("DEPRECATED! Using EMBED is deprecated since v2.2, please use discord.Embed:\
            \n\nfrom daf import discord\n\ndiscord.Embed(...)", TraceLEVELS.DEPRECATED)
        super().__init__(colour=colour,
                         color=color,
                         title=title,
                         type=type,
                         url=url,
                         description=description,
                         timestamp=timestamp,
                         fields=fields)
        ## Set author
        if author_name is not None:
            self.set_author(name=author_name, icon_url=author_icon)
        ## Set image
        if image is not None:
            self.set_image(url=image)
        ## Set thumbnail
        if thumbnail is not None:
            self.set_thumbnail(url=thumbnail)

@typechecked
@misc.doc_category("Message data types")
class FILE:
    """
    FILE object used as a data parameter to the MESSAGE objects.
    This is needed opposed to a normal file object because this way,
    you can edit the file after the framework has already been started.

    .. warning::
        This is used for sending an actual file and **NOT it's contents as text**.

    Parameters
    -------------
    filename: str
         Path to the file you want sent.
    """
    __slots__ = ("filename",)
    def __init__(self,
                 filename: str):
        self.filename = filename
    
    def __str__(self) -> str:
        return f"FILE(filename={self.filename})"


@typechecked
@misc.doc_category("Message data types")
class AUDIO:
    """
    Used for streaming audio from file or YouTube.

    .. note::
        Using a youtube video, will cause the shilling start to be delayed due to youtube data extraction.

    Parameters
    -----------------
    filename: str
        Path to the file you want streamed or a YouTube video url.

    Raises
    ----------
    ValueError
        Raised when the file or youtube url is not found.
    """

    ytdl_options = {
        "format": "bestaudio/best",
        "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
        "restrictfilenames": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "logtostderr": False,
        "quiet": True,
        "no_warnings": True,
        "default_search": "auto"
    }
    def __init__(self, filename: str) -> None:
        self.orig = filename
        self.is_stream = False

        if not GLOBALS.voice_installed:
            raise ModuleNotFoundError("You need to install extra requirements: pip install discord-advert-framework[voice]")

        url_info = urlparse(filename) # Check if it's youtube
        if "www.youtube.com" == url_info.hostname:
            try:
                self.is_stream = True
                youtube_dl = yt_dlp.YoutubeDL(params=self.ytdl_options)
                data = youtube_dl.extract_info(filename, download=False)
                if "entries" in data:
                    data = data["entries"][0] # Is a playlist, get the first entry
        
                self.url = data["url"]
                self.title = data["title"]

            except yt_dlp.DownloadError:
                raise ValueError(f'The audio from "{self.orig}" could not be streamed')
        else:
            self.url = filename
            try:
                with open(self.url):
                    pass
            except FileNotFoundError:
                raise ValueError(f"The file {self.url} could not be found.")
    
    def __str__(self):
        return f"AUDIO({str(self.to_dict())})"

    def to_dict(self):
        """
        Returns dictionary representation of this data type.

        .. versionchanged:: v2.0

            Changed to method ``to_dict`` from property ``filename``
        """
        if self.is_stream:
            return {
                "type:" : "Youtube",
                "title": self.title,
                "url": self.orig
            }
        return {
            "type:" : "File",
            "filename": self.orig
        }
