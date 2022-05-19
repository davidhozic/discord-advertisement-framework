"""
    ~ dtypes ~
    The module contains defintions regarding the data types
    you can send using the xxxMESSAGE objects.
"""
from typing import List, Union
from contextlib import suppress
import copy
import datetime
import _discord as discord


__all__ = (
    "data_function",
    "FunctionBaseCLASS",
    "EmbedFIELD",
    "EMBED",
    "FILE",
    "AUDIO"
)


#######################################################################
# Decorators
#######################################################################
class FunctionBaseCLASS:
    """
    type: dummy class
    name: FunctionBaseCLASS
    info: Used as a base class to FunctionCLASS which gets created in framework.data_function decorator.
          Because the FunctionCLASS is inaccessible outside the data_function decorator,
          this class is used to detect if the MESSAGE.data parameter is of function type,
          because the function isinstance also returns True when comparing
          the object to it's class or to the base class from which the object class is inherited from.
    """

def data_function(fnc):
    """
    type:   Decorator
    name:   data_function
    info:   Decorator used to create a framework FunctionCLASS class for function
    return: FunctionCLASS
    """
    class FunctionCLASS(FunctionBaseCLASS):
        """"
        Name:  FunctionCLASS
        Info:  Used for creating special classes that are then used to create objects in the framework.MESSAGE
               data parameter, allows for sending dynamic contentent received thru an user defined function.

        Param: custom number of positional arguments and custom number of keyword arguments.
        """
        __slots__ = (
            "args",
            "kwargs",
            "func_name",
        )

        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
            self.func_name = fnc.__name__

        def get_data(self):
            """
            Retreives the data from the user function
            """
            return fnc(*self.args, **self.kwargs)
    return FunctionCLASS


#######################################################################
# Other
#######################################################################
class EmbedFIELD:
    """
    Embedded field class for use in EMBED object constructor
    Parameters:
    -  Name         : str    -- Name of the field
    -  Content      : str    -- Content of the embedded field
    -  Inline       : bool   -- Make this field appear in the same line as the previous field
    """
    def __init__(self,
                 name : str,
                 content : str,
                 inline : bool=False):
        self.name = name
        self.content = content
        self.inline = inline

class EMBED(discord.Embed):
    """
    Derrived class of discord.Embed with easier definition
    @Parameters:
        - Added parameters:
            - author_name       : str           -- Name of embed author,
            - author_icon       : str           -- Url to author image,
            - image             : str           -- Url of image to be placed at the end of the embed
            - thumbnail         : str           -- Url of image that will be placed at the top right of embed
            - fields            : list          -- List of EmbedFIELD objects
        - Inherited from discord.Embed:
            - For the other, original params see https://docs.pycord.dev/en/master/api.html?highlight=discord%20embed#discord.Embed

    """
    __slots__ = (
        'title',
        'url',
        'type',
        '_timestamp',
        '_colour',
        '_footer',
        '_image',
        '_thumbnail',
        '_video',
        '_provider',
        '_author',
        '_fields',
        'description',
    )
    # Static members
    Color = Colour = discord.Color  # Used for color parameter
    EmptyEmbed = discord.embeds.EmptyEmbed

    @staticmethod
    def from_discord_embed(_object : discord.Embed):
        """ ~ static method ~
        Name:   from_discord_embed
        Type:   static method
        Param:
            - object : discord.Embed | discord.Embed (same type) -- The discord Embed object you want converted into the framework.EMBED class"""
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
                fields : List[EmbedFIELD] = None,
                # Base class parameters
                colour: Union[int, Colour] = EmptyEmbed,
                color: Union[int, Colour] = EmptyEmbed,
                title: str = EmptyEmbed,
                type : str = "rich",
                url: str= EmptyEmbed,
                description = EmptyEmbed,
                timestamp: datetime.datetime = None):

        super().__init__(colour=colour,
                         color=color,
                         title=title,
                         type=type,
                         url=url,
                         description=description,
                         timestamp=timestamp)

        ## Set author
        if author_name is not None:
            self.set_author(name=author_name, icon_url=author_icon)
        ## Set image
        if image is not None:
            self.set_image(url=image)
        ## Set thumbnail
        if thumbnail is not None:
            self.set_thumbnail(url=thumbnail)
        ### Set fields
        if fields is not None:
            for field in fields:
                self.add_field(name=field.name,value=field.content,inline=field.inline)


class FILE:
    """
    Name:   FILE
    Param:
        -   filename:
            string path to the file you want to send

    Info:   FILE object used as a data parameter to the MESSAGE objects.
            This is needed aposed to a normal file object because this way,
            you can edit the file after the framework has already been started.
    """
    __slots__ = ("filename",)
    def __init__(self,
                 filename):
        self.filename = filename


class AUDIO(FILE):
    """
    Name: AUDIO
    Param:
        -   filename:
            string path to the audio you want to stream
    Info: Represents an audio parameter that is used in the VoiceMESSAGE data parameterer
    """
    __slots__ = ("filename",)
