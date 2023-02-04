"""
    Contains definitions related to voice messaging."""


from contextlib import suppress
from typing import Any, Dict, List, Iterable, Optional, Union
from datetime import timedelta, datetime
from typeguard import typechecked

from .base import *
from ..dtypes import *
from ..logging.tracing import *

from .. import client
from ..logging import sql
from .. import misc
from .. import dtypes

import asyncio
import _discord as discord


__all__ = (
    "VoiceMESSAGE",
)


# Configuration
# ----------------------#
C_VC_CONNECT_TIMEOUT = 3 # Timeout of voice channels


@misc.doc_category("Messages", path="message")
@sql.register_type("MessageTYPE")
class VoiceMESSAGE(BaseMESSAGE):
    """
    This class is used for creating objects that represent messages which will be streamed to voice channels.

    .. deprecated:: v2.1

        - start_in (start_now) - Using bool value to dictate whether the message should be sent at framework start.
        - start_period, end_period - Using int values, use ``timedelta`` object instead.
    
    .. versionchanged:: v2.1

        - start_period, end_period Accept timedelta objects.
        - start_now - renamed into ``start_in`` which describes when the message should be first sent.
        - removed ``deleted`` property

    Parameters
    ------------
    start_period: Union[int, timedelta, None]
        The value of this parameter can be:

        - None - Use this value for a fixed (not randomized) sending period
        - timedelta object - object describing time difference, if this is used, then the parameter represents the bottom limit of the **randomized** sending period.
    end_period: Union[int, timedelta]
        If ``start_period`` is not None, then this represents the upper limit of randomized time period in which messages will be sent.
        If ``start_period`` is None, then this represents the actual time period between each message send.

        .. code-block:: python
            :caption: **Randomized** sending period between **5** seconds and **10** seconds.

            # Time between each send is somewhere between 5 seconds and 10 seconds.
            daf.VoiceMESSAGE(start_period=timedelta(seconds=5), end_period=timedelta(seconds=10), data=daf.AUDIO("msg.mp3"), channels=[12345], start_in=timedelta(seconds=0), volume=50)

        .. code-block:: python
            :caption: **Fixed** sending period at **10** seconds

            # Time between each send is exactly 10 seconds.
            daf.VoiceMESSAGE(start_period=None, end_period=timedelta(seconds=10), data=daf.AUDIO("msg.mp3"), channels=[12345], start_in=timedelta(seconds=0), volume=50)
    data: AUDIO
        The data parameter is the actual data that will be sent using discord's API. The data types of this parameter can be:
            - AUDIO object.
            - Function that accepts any amount of parameters and returns an AUDIO object. To pass a function, YOU MUST USE THE :ref:`data_function` decorator on the function before passing the function to the daf.
    channels: Union[Iterable[Union[int, discord.VoiceChannel]], daf.message.AutoCHANNEL]
        .. versionchanged:: v2.3
            Can also be :class:`~daf.message.AutoCHANNEL`

        Channels that it will be advertised into (Can be snowflake ID or channel objects from PyCord).
    volume: Optional[int]
        The volume (0-100%) at which to play the audio. Defaults to 50%. This was added in v2.0.0
    start_in: Optional[timedelta]
        When should the message be first sent.
    remove_after: Optional[Union[int, timedelta, datetime]]
        Deletes the message after:

        * int - provided amounts of sends
        * timedelta - the specified time difference
        * datetime - specific date & time
    """

    __slots__ = (
        "period",
        "start_period",
        "end_period",
        "volume",
        "channels",
    )

    @typechecked
    def __init__(self,
                 start_period: Union[int, timedelta, None],
                 end_period: Union[int, timedelta],
                 data: Union[AUDIO, Iterable[AUDIO], _FunctionBaseCLASS],
                 channels: Union[Iterable[Union[int, discord.VoiceChannel]], AutoCHANNEL],
                 volume: Optional[int]=50,
                 start_in: Optional[Union[timedelta, bool]]=timedelta(seconds=0),
                 remove_after: Optional[Union[int, timedelta, datetime]]=None):

        if not dtypes.GLOBALS.voice_installed:
            raise ModuleNotFoundError("You need to install extra requirements: pip install discord-advert-framework[voice]")

        super().__init__(start_period, end_period, data, start_in, remove_after)
        self.volume = max(0, min(100, volume)) # Clamp the volume to 0-100 %
        self.channels = channels

    def _check_state(self) -> bool:
        """
        Checks if the message is ready to be deleted.
        
        Returns
        ----------
        True
            The message should be deleted.
        False
            The message is in proper state, do not delete.
        """
        return super()._check_state() or not bool(self.channels)

    def _update_state(self, err_channels: List[dict]):
        "Updates the state of the object based on errored channels."
        super()._update_state()
        # Remove any channels that returned with code status 404 (They no longer exist)
        for data in err_channels:
            reason = data["reason"]
            channel = data["channel"]
            if isinstance(reason, discord.HTTPException):
                if (reason.status == 403 or                    # Forbidden
                    reason.code in {50007, 10003}):     # Not Forbidden, but bad error codes
                    self.channels.remove(channel)

    def generate_log_context(self,
                             audio: AUDIO,
                             succeeded_ch: List[discord.VoiceChannel],
                             failed_ch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generates information about the message send attempt that is to be saved into a log.

        Parameters
        -----------
        audio: audio
            The audio that was streamed.
        succeeded_ch: List[Union[discord.VoiceChannel]]
            List of the successfully streamed channels
        failed_ch: List[Dict[discord.VoiceChannel, Exception]]
            List of dictionaries contained the failed channel and the Exception object

        Returns
        ----------
        Dict[str, Any]
            .. code-block:: python
              
                {
                    sent_data:
                    {
                        streamed_audio: str - The filename that was streamed/youtube url
                    },
                    channels:
                    {
                        successful:
                        {
                            id: int - Snowflake id,
                            name: str - Channel name
                        },
                        failed:
                        {
                            id: int - Snowflake id,
                            name: str - Channel name,
                            reason: str - Exception that caused the error
                        }
                    },
                    type: str - The type of the message, this is always VoiceMESSAGE.
              }
        """
        if not (len(succeeded_ch) + len(failed_ch)):
            return None

        succeeded_ch = [{"name": str(channel), "id" : channel.id} for channel in succeeded_ch]
        failed_ch = [{"name": str(entry["channel"]), "id" : entry["channel"].id,
                     "reason": str(entry["reason"])} for entry in failed_ch]
        return {
            "sent_data": {
                "streamed_audio" : audio.to_dict()
            },
            "channels": {
                "successful" : succeeded_ch,
                "failed": failed_ch
            },
            "type" : type(self).__name__
        }

    async def _get_data(self) -> dict:
        """"
        Returns a dictionary of keyword arguments that is then expanded
        into other methods eg. `_send_channel, _generate_log`
        
        .. versionchanged:: v2.3
            Turned async.
        """
        data = None
        _data_to_send = {}
        data = await super()._get_data()
        if data is not None:
            if not isinstance(data, (list, tuple, set)):
                data = (data,)
            for element in data:
                if isinstance(element, AUDIO):
                    _data_to_send["audio"] = element
        return _data_to_send

    async def initialize(self, parent: Any):
        """
        This method initializes the implementation specific api objects and checks for the correct channel input context.

        Parameters
        --------------
        parent: daf.guild.GUILD
            The GUILD this message is in

        Raises
        ------------
        TypeError
            Channel contains invalid channels
        ValueError
            Channel does not belong to the guild this message is in.
        ValueError
            No valid channels were passed to object"
        """
        ch_i = 0
        self.parent = parent
        cl = parent.parent.client
        _guild = parent.apiobject
        to_remove = []

        if isinstance(self.channels, AutoCHANNEL):
            await self.channels.initialize(self, "voice_channels")
        else:
            for ch_i, channel in enumerate(self.channels):
                if isinstance(channel, discord.abc.GuildChannel):
                    channel_id = channel.id
                else:
                    # Snowflake IDs provided
                    channel_id = channel
                    channel = self.channels[ch_i] = cl.get_channel(channel_id)

                if channel is None:
                    trace(f"Unable to get channel from ID {channel_id}", TraceLEVELS.WARNING)
                    to_remove.append(channel)
                elif type(channel) is not discord.VoiceChannel:
                    raise TypeError(f"VoiceMESSAGE object received channel type of {type(channel).__name__}, but was expecting discord.VoiceChannel")
                elif channel.guild != _guild:
                    raise ValueError(f"The channel {channel.name}(ID: {channel_id}) does not belong into {_guild.name}(ID: {_guild.id}) but is part of {channel.guild.name}(ID: {channel.guild.id})")
            
            for channel in to_remove:
                self.channels.remove(channel)

        if not self.channels:
            raise ValueError(f"No valid channels were passed to {self} object")

    async def _send_channel(self,
                           channel: discord.VoiceChannel,
                           audio: Optional[AUDIO]) -> dict:
        """
        Sends data to specific channel

        Returns a dictionary:
        - "success" - Returns True if successful, else False
        - "reason"  - Only present if "success" is False, contains the Exception returned by the send attempt

        Parameters
        -------------
        channel: discord.VoiceChannel
            The channel in which to send the data.
        audio: AUDIO
            the audio to stream.
        """
        stream = None
        voice_client = None
        try:
            # Check if client has permissions before attempting to join
            client_: discord.Client = self.parent.parent.client
            if (member := channel.guild.get_member(client_.user.id)) is None:
                raise self._generate_exception(404, -1, "Client user could not be found in guild members", discord.NotFound)

            if channel.guild.me.pending:
                raise self._generate_exception(
                    403, 50009,
                    "Channel verification level is too high for you to gain access",
                    discord.Forbidden
                )

            ch_perms = channel.permissions_for(member)
            if not all([ch_perms.connect, ch_perms.stream, ch_perms.speak]):
                raise self._generate_exception(403, 50013, "You lack permissions to perform that action", discord.Forbidden)
            
            # Check if channel still exists in cache (has not been deleted)
            if client_.get_channel(channel.id) is None:
                raise self._generate_exception(404, 10003, "Channel was deleted", discord.NotFound)

            voice_client = await channel.connect(timeout=C_VC_CONNECT_TIMEOUT)
            stream = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(audio.url, options="-loglevel fatal"), volume=self.volume/100)
            voice_client.play(stream)

            while voice_client.is_playing():
                await asyncio.sleep(1)
            return {"success": True}
        except Exception as ex:
            return {"success": False, "reason": ex}
        finally:
            if voice_client is not None:
                with suppress(ConnectionResetError):
                    await voice_client.disconnect()

                await asyncio.sleep(1) # Avoid sudden disconnect and connect to a new channel

    @misc._async_safe("update_semaphore")
    async def _send(self) -> Union[dict, None]:
        """
        Sends the data into each channel.

        Returns
        ----------
        Union[Dict, None]
            Returns a dictionary generated by the ``generate_log_context`` method or the None object if message wasn't ready to be sent (:ref:`data_function` returned None or an invalid type)

            This is then passed to :ref:`GUILD`._generate_log method.
        """
        _data_to_send = await self._get_data()
        if any(_data_to_send.values()):
            errored_channels = []
            succeeded_channels= []

            for channel in self.channels:
                context = await self._send_channel(channel, **_data_to_send)
                if context["success"]:
                    succeeded_channels.append(channel)
                else:
                    errored_channels.append({"channel":channel, "reason": context["reason"]})

            self._update_state(errored_channels)
            
            return self.generate_log_context(**_data_to_send, succeeded_ch=succeeded_channels, failed_ch=errored_channels)

        return None

    @typechecked
    @misc._async_safe("update_semaphore")
    async def update(self, _init_options: Optional[dict] = {}, **kwargs):
        """
        .. versionadded:: v2.0

        Used for changing the initialization parameters the object was initialized with.

        .. warning::
            Upon updating, the internal state of objects get's reset, meaning you basically have a brand new created object.

        Parameters
        -------------
        **kwargs: Any
            Custom number of keyword parameters which you want to update, these can be anything that is available during the object creation.

        Raises
        -----------
        TypeError
            Invalid keyword argument was passed
        Other
            Raised from .initialize() method
        """
        if "start_in" not in kwargs:
            # This parameter does not appear as attribute, manual setting necessary
            kwargs["start_in"] = timedelta(seconds=0)

        if "data" not in kwargs:
            kwargs["data"] = self._data

        if "channels" not in kwargs and not isinstance(self.channels, AutoCHANNEL):
            kwargs["channels"] = [x.id for x in self.channels]
        
        if not len(_init_options):
            _init_options = {"parent": self.parent}

        await misc._update(self, init_options=_init_options, **kwargs) # No additional modifications are required
        if isinstance(self.channels, AutoCHANNEL):
            await self.channels.update()

