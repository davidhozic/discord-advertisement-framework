"""~ voice message related ~
@info:
    Contains definitions related to voice messaging."""

from   .base        import *
from   ..           import client
from   ..           import sql
from   ..dtypes     import *
from   ..tracing    import *
from   ..const      import *
from   ..exceptions import *
from   typing       import List, Iterable, Union
import asyncio
import _discord as discord


__all__ = (
    "VoiceMESSAGE",
)

class GLOBALS:
    """ ~ class ~
    - @Info: Contains global variables used in the voice messaging."""
    voice_client: discord.VoiceClient = None

@sql.register_type("MessageTYPE")
class VoiceMESSAGE(BaseMESSAGE):
    """ ~ class ~
    - @Name: VoiceMESSAGE
    - @Info: The VoiceMESSAGE object containts parameters which describe behaviour and data that will be sent to the channels.
    - @Params:
        - start_period, end_period ~ These 2 parameters specify the period on which the messages will be played:
            - start_period can be either:
                - None ~ Messages will be sent on intervals specified by End period,
                - Integer >= 0 ~ Messages will be sent on intervals randomly chosen between Start period and End period,
                                 where the randomly chosen intervals will be re::randomized after each sent message.
        - data ~ The data parameter is the actual data that will be sent using discord's API. The data types of this parameter can be:
            - Path to an audio file (str)
            - Youtube link (str)
            - Function that accepts any amount of parameters and returns any of the above types.
                    To pass a function, YOU MUST USE THE framework.data_function decorator on the function before
                    passing the function to the framework.
        - channels ~ List of IDs of all the channels you want data to be sent into.
        - start_now ~ A bool variable that can be either True or False. If True, then the framework will send the message
                                 as soon as it is run and then wait it's period before trying again. If False, then the message will
                                 not be sent immediatly after framework is ready, but will instead wait for the period to elapse.
        - volume ~ The volume in percentage (5-100%) of the audio that will be streamed. The default value is 50%."""

    __slots__ = (
        "randomized_time",
        "period",
        "random_range",
        "data",
        "volume",
        "channels",
        "timer",
        "force_retry",
    )

    __logname__ = "VoiceMESSAGE"    # For sql.register_type
    __valid_data_types__ = {AUDIO}  # This is used in the BaseMESSAGE.initialize() to check if the passed data parameters are of correct type

    def __init__(self, start_period: Union[float, None],
                 end_period: float,
                 data: AUDIO,
                 channels: Iterable[int],
                 start_now: bool = True,
                 volume: int=50):

        super().__init__(start_period, end_period, start_now)
        self.data = data

        self.volume = max(5, min(100, volume)) # Clamp the volume to 5-100 % 
        self.channels = list(set(channels)) # Auto remove duplicates

    def generate_log_context(self,
                             audio: AUDIO,
                             succeeded_ch: List[discord.VoiceChannel],
                             failed_ch: List[dict]):
        """ ~ method ~
        - @Name: generate_log_context
        - @Param:
            - audio ~The audio that was streamed to the channels
            - succeeded_ch ~ list of the successfuly streamed channels,
            - failed_ch ~ list of dictionaries contained the failed channel and the Exception
        - @Info: Generates a dictionary containing data that will be saved in the message log"""

        succeeded_ch = [{"name": str(channel), "id" : channel.id} for channel in succeeded_ch]
        failed_ch = [{"name": str(entry["channel"]), "id" : entry["channel"].id,
                     "reason": str(entry["reason"])} for entry in failed_ch]
        return {
            "sent_data": {
                "streamed_audio" : audio.filename
            },
            "channels": {
                "successful" : succeeded_ch,
                "failed": failed_ch
            },
            "type" : type(self).__name__
        }

    def get_data(self) -> dict:
        """ ~ method ~
        - @Name:  get_data
        - @Info: Returns a dictionary of keyword arguments that is then expanded
                 into other functions (send_channel, generate_log)"""
        data = None
        _data_to_send = {}
        data = self.data.get_data() if isinstance(self.data, FunctionBaseCLASS) else self.data
        if data is not None:
            if not isinstance(data, (list, tuple, set)):
                data = (data,)
            for element in data:
                if isinstance(element, AUDIO):
                    _data_to_send["audio"] = element
        return _data_to_send

    async def initialize_channels(self) -> bool:
        """ ~ async method ~
        - @Name:  initialize_channels
        - @Info:  This method initializes the implementation specific
                  api objects and checks for the correct channel inpit context.
        - @Return: True on success
        - @Exceptions:
            - <class DAFInvalidParameterError code=DAF_INVALID_TYPE> ~ Raised when the object obtained from a channel id is not of type discord.VoiceChannel
            - <class DAFMissingParameterError code=DAF_MISSING_PARAMETER> ~ Raised when no channels could be obtained from the given channel ids"""
        ch_i = 0
        cl = client.get_client()
        while ch_i < len(self.channels):
            channel_id = self.channels[ch_i]
            channel = cl.get_channel(channel_id)
            self.channels[ch_i] = channel

            if channel is None:
                trace(f"Unable to get channel from ID {channel_id}", TraceLEVELS.ERROR)
                self.channels.remove(channel)
            elif type(channel) is not discord.VoiceChannel:
                raise DAFInvalidParameterError(f"VoiceMESSAGE object got ID ({channel_id}) for {type(channel).__name__}, but was expecting discord.VoiceChannel", DAF_INVALID_TYPE)
            else:
                ch_i += 1

        if not len(self.channels):
            raise DAFMissingParameterError(f"No valid channels were passed to {type(self)} object", DAF_MISSING_PARAMETER)

    async def send_channel(self,
                           channel: discord.VoiceChannel,
                           audio: AUDIO) -> dict:
        """ ~ async method ~
        - @Name : send_channel
        - @Info:
            Streams audio to specific channel
        - @Return:
            - dict:
                - "success" ~ True if successful, else False
                - "reason"  ~ Only present if "success" is False,
                              contains the Exception returned by the send attempt."""
        stream = None
        try:
            # Check if client has permissions before attempting to join
            ch_perms = channel.permissions_for(channel.guild.get_member(client.get_client().user.id))
            if not all([ch_perms.connect, ch_perms.stream, ch_perms.speak]):
                raise self.generate_exception(403, 50013, "You lack permissions to perform that action", discord.Forbidden)

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
            if isinstance(ex, FileExistsError):
                pass # Don't change error
            elif client.get_client().get_channel(channel.id) is None:
                ex = self.generate_exception(404, 10003, "Channel was deleted", discord.NotFound)
            else:
                ex = self.generate_exception(500, 0, "Timeout error", discord.HTTPException)
            return {"success": False, "reason": ex}
        finally:
            if GLOBALS.voice_client is not None and GLOBALS.voice_client.is_connected():
                await GLOBALS.voice_client.disconnect()
                GLOBALS.voice_client = None
                await asyncio.sleep(1) # Avoid sudden disconnect and connect to a new channel

    async def send(self) -> Union[dict,  None]:
        """" ~ async method ~
        - @Name send
        - @Info: Streams audio into the chanels
        - @Return:
            Returns a dictionary generated by the generate_log_context method
            or the None object if message wasn't ready to be sent (data_function returned None)"""
        _data_to_send = self.get_data()
        if any(_data_to_send.values()):
            errored_channels = []
            succeded_channels= []

            for channel in self.channels:
                context = await self.send_channel(channel, **_data_to_send)
                if context["success"]:
                    succeded_channels.append(channel)
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

            return self.generate_log_context(**_data_to_send, succeeded_ch=succeded_channels, failed_ch=errored_channels)
        return None