"""
    Contains definitions related to voice messaging."""

from   .base        import *
from   ..dtypes     import *
from   ..tracing    import *
from   ..const      import *
from   ..exceptions import *
from   typing       import Any, Dict, List, Iterable, Union
from   ..           import client
from   ..           import sql
from   ..           import core
from   ..           import misc
import asyncio
import _discord as discord


__all__ = (
    "VoiceMESSAGE",
)

class GLOBALS:
    """ ~ class ~
    - @Info: Contains global variables used in the voice messaging.
    """
    voice_client: discord.VoiceClient = None

@sql._register_type("MessageTYPE")
class VoiceMESSAGE(BaseMESSAGE):
    """
    This class is used for creating objects that represent messages which will be streamed to voice channels.

    .. versionchanged:: v2.0
        
        - Added the ``volume`` parameter
        - Renamed ``channel_ids`` parameter to ``channels``
        - Channels parameter now also accepts channel objects instead of int

    Parameters
    ------------
    start_period: Union[int, None]
        The value of this parameter can be:

        ..  table:: 
        
            ===========  =================================================================================================================
             Value        Info
            ===========  =================================================================================================================
             None         Messages are sent in a constant time period equal to the value of ``end_period``.
             int > 0      Messages are sent in a randomized time period. ``start_period`` represents the bottom limit of this period.
            ===========  =================================================================================================================

    end_period: int
        If ``start_period`` > 0, then this represents the upper limit of randomized time period in which messages will be sent.
        If ``start_period`` is None, then this represents the actual time period between each message send.

        .. code-block:: python
            :caption: **Randomized** sending period between **5** seconds and **10** seconds.
            
            # Time between each send is somewhere between 5 seconds and 10 seconds.
            framework.VoiceMESSAGE(start_period=None, end_period=10, data=framework.AUDIO("msg.mp3"), channels=[12345], start_now=True, volume=50)

        .. code-block:: python
            :caption: **Fixed** sending period at **10** seconds

            # Time between each send is exactly 10 seconds.
            framework.VoiceMESSAGE(start_period=None, end_period=10, data=framework.AUDIO("msg.mp3"), channels=[12345], start_now=True, volume=50)

    data: AUDIO
        The data parameter is the actual data that will be sent using discord's API. The data types of this parameter can be:
            - AUDIO object.
            - Function that accepts any amount of parameters and returns an AUDIO object. To pass a function, YOU MUST USE THE :ref:`data_function` decorator on the function before passing the function to the framework.
    channels: Iterable[Union[int, discord.VoiceChannel]]
        Channels that it will be advertised into (Can be snowflake ID or channel objects from PyCord).
    volume: int         
        The volume (0-100%) at which to play the audio. Defaults to 50%. This was added in v2.0.0
    start_now: bool
        If True, then the framework will send the message as soon as it is run.      
    """

    __slots__ = (
        "randomized_time",
        "period",
        "start_period",
        "end_period",
        "data",
        "volume",
        "channels",
        "timer",
        "force_retry",
    )

    __logname__ = "VoiceMESSAGE"    # For sql._register_type
    __valid_data_types__ = {AUDIO}  # This is used in the BaseMESSAGE.initialize() to check if the passed data parameters are of correct type

    def __init__(self, start_period: Union[float, None],
                 end_period: float,
                 data: AUDIO,
                 channels: Iterable[Union[int, discord.VoiceChannel]],
                 volume: int=50,
                 start_now: bool = True):

        super().__init__(start_period, end_period, data, start_now)
        self.volume = max(0, min(100, volume)) # Clamp the volume to 0-100 % 
        self.channels = list(set(channels))    # Auto remove duplicates

    def _generate_log_context(self,
                             audio: AUDIO,
                             succeeded_ch: List[discord.VoiceChannel],
                             failed_ch: List[dict]) -> Dict[str, Any]:
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
            Dictionary containing:

                - sent_data: Dict[str, str]:
                    - streamed_audio: str - The filename that was streamed/youtube url

                - channels: Dict[str, List]:
                    - successful: List[Dict[str, int]] - List of dictionaries containing name of the channel and snowflake id of the channels.
                    - failed: List[Dict[str, Any]] - List of dictionaries containing name of the channel (str), snowflake id (int) and reason why streaming to channel failed (str).
                
                - type: str - The type of the message, this is always VoiceMESSAGE.
        """

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

    def _get_data(self) -> dict:
        """"
        Returns a dictionary of keyword arguments that is then expanded
        into other methods eg. `_send_channel, generate_log`
        """
        data = None
        _data_to_send = {}
        data = self.data.get_data() if isinstance(self.data, _FunctionBaseCLASS) else self.data
        if data is not None:
            if not isinstance(data, (list, tuple, set)):
                data = (data,)
            for element in data:
                if isinstance(element, AUDIO):
                    _data_to_send["audio"] = element
        return _data_to_send

    async def _initialize_channels(self):
        """
        This method initializes the implementation specific api objects and checks for the correct channel input context.
        
        Raises
        ------------
        - `DAFParameterError(code=DAF_INVALID_TYPE)` - Raised when the object retrieved from channels is not a discord.TextChannel or discord.Thread object.
        - `DAFNotFoundError(code=DAF_MISSING_PARAMETER)` - Raised when no channels could be found were parsed.
        """
        ch_i = 0
        cl = client.get_client()
        while ch_i < len(self.channels):
            channel = self.channels[ch_i]
            if isinstance(channel, discord.abc.GuildChannel):
                channel_id = channel.id
            else:
                channel_id = channel
                channel = self.channels[ch_i] = cl.get_channel(channel_id)

            if channel is None:
                trace(f"Unable to get channel from ID {channel_id}", TraceLEVELS.ERROR)
                self.channels.remove(channel)
            elif type(channel) not in {discord.VoiceChannel}:
                raise DAFParameterError(f"TextMESSAGE object received channel type of {type(channel).__name__}, but was expecting VoiceChannel", DAF_INVALID_TYPE)
            else:
                ch_i += 1

        if not len(self.channels):
            raise DAFNotFoundError(f"No valid channels were passed to {type(self)} object", DAF_MISSING_PARAMETER)

    async def _send_channel(self,
                           channel: discord.VoiceChannel,
                           audio: AUDIO) -> dict:
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
        try:
            # Check if client has permissions before attempting to join
            ch_perms = channel.permissions_for(channel.guild.get_member(client.get_client().user.id))
            if not all([ch_perms.connect, ch_perms.stream, ch_perms.speak]):
                raise self._generate_exception(403, 50013, "You lack permissions to perform that action", discord.Forbidden)

            if GLOBALS.voice_client is None or not GLOBALS.voice_client.is_connected():
                GLOBALS.voice_client = await channel.connect(timeout=C_VC_CONNECT_TIMEOUT)
            else:
                await GLOBALS.voice_client.move_to(channel)

            stream = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(audio.url), volume=self.volume/100)

            GLOBALS.voice_client.play(stream)

            while GLOBALS.voice_client.is_playing():
                await asyncio.sleep(1)
            return {"success": True}
        except Exception as ex:
            if isinstance(ex, (FileExistsError, discord.Forbidden)):
                pass # Don't change error
            elif client.get_client().get_channel(channel.id) is None:
                ex = self._generate_exception(404, 10003, "Channel was deleted", discord.NotFound)
            else:
                ex = self._generate_exception(500, 0, "Timeout error", discord.HTTPException)
            return {"success": False, "reason": ex}
        finally:
            if GLOBALS.voice_client is not None and GLOBALS.voice_client.is_connected():
                await GLOBALS.voice_client.disconnect()
                GLOBALS.voice_client = None
                await asyncio.sleep(1) # Avoid sudden disconnect and connect to a new channel

    @misc._async_safe("update_semaphore")
    async def send(self) -> Union[dict,  None]:
        """
        Sends the data into each channel.
        
        Returns
        ----------
        Union[Dict, None]
            Returns a dictionary generated by the ``_generate_log_context`` method or the None object if message wasn't ready to be sent (:ref:`data_function` returned None or an invalid type)
            
            This is then passed to :ref:`GUILD`.generate_log method.
        """
        _data_to_send = self._get_data()
        if any(_data_to_send.values()):
            errored_channels = []
            succeeded_channels= []

            for channel in self.channels:
                context = await self._send_channel(channel, **_data_to_send)
                if context["success"]:
                    succeeded_channels.append(channel)
                else:
                    errored_channels.append({"channel":channel, "reason": context["reason"]})

            # Remove any channels that returned with code status 404 (They no longer exist)
            for data in errored_channels:
                reason = data["reason"]
                channel = data["channel"]
                if isinstance(reason, discord.HTTPException):
                    if (reason.status == 403 or
                        reason.code in {10003, 50013} # Unknown, Permissions
                    ):
                        self.channels.remove(channel)
                        trace(f"Channel {channel.name}(ID: {channel.id}) {'was deleted' if reason.code == 10003 else 'does not have permissions'}, removing it from the send list", TraceLEVELS.WARNING)

            return self._generate_log_context(**_data_to_send, succeeded_ch=succeeded_channels, failed_ch=errored_channels)

        return None

    @misc._async_safe("update_semaphore")
    async def update(self, **kwargs):
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
        DAFParameterError(code=DAF_UPDATE_PARAMETER_ERROR)
            Invalid keyword argument was passed
        Other
            Raised from .initialize() method
        """
        if "start_now" not in kwargs:
            # This parameter does not appear as attribute, manual setting necessary 
            kwargs["start_now"] = True

        await core._update(self, **kwargs) # No additional modifications are required
