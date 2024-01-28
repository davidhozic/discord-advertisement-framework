"""
    Contains definitions related to voice messaging."""


from typing import Any, Dict, List, Iterable, Optional, Union, Tuple, Callable
from datetime import timedelta, datetime
from typeguard import typechecked
from pathlib import Path

from ..messagedata.dynamicdata import _DeprecatedDynamic

from ..messagedata import BaseVoiceData, VoiceMessageData, FILE
from ..misc import doc, instance_track
from ..logging import sql
from .. import dtypes

from ..logging.tracing import *
from .messageperiod import *
from .autochannel import *
from ..dtypes import *
from ..events import *
from .base import *

import importlib.util as import_util
import _discord as discord
import asyncio
import os


__all__ = (
    "VoiceMESSAGE",
)


# Configuration
# ----------------------#
C_VC_CONNECT_TIMEOUT = 7  # Timeout of voice channels


class GLOBAL:
    voice_installed: bool = import_util.find_spec("nacl") is not None


@instance_track.track_id
@doc.doc_category("Messages", path="message")
@sql.register_type("MessageTYPE")
class VoiceMESSAGE(BaseChannelMessage):
    """
    This class is used for creating objects that represent messages which will be streamed to voice channels.

    .. warning::

        This additionally requires FFMPEG to be installed on your system.


    Parameters
    ------------
    data: BaseVoiceData
        The actual data streamed to voice channels.
        Can be VoiceMessageData or a class inherited from DynamicMessageData.
    channels: Union[list[Union[int, discord.VoiceChannel]], daf.message.AutoCHANNEL]
        Channels that it will be advertised into (Can be snowflake ID or channel objects from PyCord).
    volume: Optional[int]
        The volume (0-100%) at which to play the audio. Defaults to 50%. This was added in v2.0.0
    remove_after: Optional[Union[int, timedelta, datetime]]
        Deletes the message after:

        * int - provided amounts of successful sends to separate channels.
        * timedelta - the specified time difference
        * datetime - specific date & time
    period: BaseMessagePeriod
        The sending period.
    """
    __slots__ = (
        "volume",
    )

    FFMPEG_OPTIONS = {
        'options': '-vn'
    }

    # Deprecated. TODO: Remove in the future
    _old_data_type = Union[FILE, list, tuple, set, _FunctionBaseCLASS]

    @typechecked
    def __init__(
        self,
        start_period: Union[int, timedelta, None] = None,
        end_period: Union[int, timedelta] = None,
        data: Union[BaseVoiceData, _old_data_type] = None,
        channels: Union[list[Union[int, discord.VoiceChannel]], AutoCHANNEL] = None,
        volume: Optional[int] = 50,
        start_in: Optional[Union[timedelta, datetime]] = None,
        remove_after: Optional[Union[int, timedelta, datetime]] = None,
        period: BaseMessagePeriod = None
    ):
        if not GLOBAL.voice_installed:
            raise ModuleNotFoundError(
                "You need to install extra requirements: pip install discord-advert-framework[voice]"
            )

        if not isinstance(data, BaseVoiceData):
            trace(
                f"Using data types other than {[x.__name__ for x in BaseVoiceData.__subclasses__()]}, "
                "is deprecated on VoiceMESSAGE's data parameter! Planned for removal in 4.2.0",
                TraceLEVELS.DEPRECATED
            )
            # Transform to new data type            
            if isinstance(data, _FunctionBaseCLASS):
                data = _DeprecatedDynamic(data.fnc, *data.args, **data.kwargs)
            else:
                if isinstance(data, FILE):
                    data = [data]

                if not data:
                    raise ValueError("'data' cannot be an empty list, use daf.VoiceMessageData!")

                data = VoiceMessageData(data[0])

        super().__init__(start_period, end_period, data, channels, start_in, remove_after, period)
        self.volume = max(0, min(100, volume))  # Clamp the volume to 0-100 %

    def generate_log_context(self,
                             file: FILE,
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

        succeeded_ch = [{"name": str(channel), "id": channel.id} for channel in succeeded_ch]
        failed_ch = [{"name": str(entry["channel"]), "id": entry["channel"].id,
                     "reason": str(entry["reason"])} for entry in failed_ch]
        return {
            "sent_data": {
                "streamed_audio": file.fullpath
            },
            "channels": {
                "successful": succeeded_ch,
                "failed": failed_ch
            },
            "type": type(self).__name__
        }

    async def _handle_error(self, channel: discord.VoiceChannel, ex: Exception) -> Tuple[bool, ChannelErrorAction]:
        """
        This method handles the error that occurred during the execution of the function.

        Parameters
        -----------
        channel: Union[discord.TextChannel, discord.Thread]
            The channel where the exception occurred.
        ex: Exception
            The exception that occurred during a send attempt.

        Returns
        -----------
        Tuple[bool, ChannelErrorAction]
            Tuple containing (error_handled, ChannelErrorAction),
            where the ChannelErrorAction is a enum telling upper part of the message layer how to proceed.
        """
        handled = False
        action = None

        guild = channel.guild
        member = guild.get_member(self.parent.parent.client.user.id)

        # Acount token invalidated
        if isinstance(ex, discord.HTTPException) and ex.status == 401:  # Acount token invalidated
            action = ChannelErrorAction.REMOVE_ACCOUNT

        # Timeout handling
        elif member is not None and member.timed_out:
            self.period.defer(member.communication_disabled_until.astimezone() + timedelta(minutes=1))
            trace(
                f"User '{member.name}' has been timed-out in guild '{guild.name}'.\n"
                f"Retrying after {self.period.get()} (1 minute after expiry)",
                TraceLEVELS.WARNING
            )

            if isinstance(ex, discord.HTTPException):
                # Prevent channel removal by the cleanup process
                ex.status = 429
                ex.code = 0

            action = ChannelErrorAction.SKIP_CHANNELS

        return handled, action

    def _get_channel_types(self):
        return {discord.VoiceChannel}

    def initialize(self, parent: Any, event_ctrl: EventController, channel_getter: Callable):
        """
        This method initializes the implementation specific API objects
        and checks for the correct channel input context.

        Parameters
        --------------
        parent: daf.guild.GUILD
            The GUILD this message is in
        """
        return super().initialize(parent, event_ctrl, channel_getter)

    def _verify_data(self, data: dict) -> bool:
        return super()._verify_data(VoiceMessageData, data)

    async def _send_channel(self,
                            channel: discord.VoiceChannel,
                            file: Optional[FILE]) -> dict:
        """
        Sends data to specific channel

        Returns a dictionary:
        - "success" - Returns True if successful, else False
        - "reason"  - Only present if "success" is False, contains the Exception returned by the send attempt

        Parameters
        -------------
        channel: discord.VoiceChannel
            The channel in which to send the data.
        audio: FILE
            the audio to stream.
        """
        stream = None
        voice_proto = None
        try:
            # Check if client has permissions before attempting to join
            client_: discord.Client = self.parent.parent.client
            member = channel.guild.get_member(client_.user.id)
            if member is None:
                raise self._generate_exception(
                    404, -1, "Client user could not be found in guild members", discord.NotFound
                )

            if channel.guild.me.pending:
                raise self._generate_exception(
                    403, 50009,
                    "Channel verification level is too high for you to gain access",
                    discord.Forbidden
                )

            ch_perms = channel.permissions_for(member)
            if not all([ch_perms.connect, ch_perms.stream, ch_perms.speak]):
                raise self._generate_exception(
                    403, 50013, "You lack permissions to perform that action", discord.Forbidden
                )

            # Check if channel still exists in cache (has not been deleted)
            if client_.get_channel(channel.id) is None:
                raise self._generate_exception(404, 10003, "Channel was deleted", discord.NotFound)

            # Write data to file instead of directly sending it to FFMPEG.
            # This is needed due to a bug in the API wrapper, which only seems to appear on Linux.
            # TODO: When fixed, replace with audio.stream.
            raw_data = file.data
            filename = Path.home().joinpath(f"daf/tmp_{id(raw_data)}")
            filename.parent.mkdir(exist_ok=True, parents=True)

            with open(filename, "wb") as tmp_file:
                tmp_file.write(raw_data)

            stream = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(filename, **VoiceMESSAGE.FFMPEG_OPTIONS),
                volume=self.volume / 100
            )
            voice_proto = await channel.connect(reconnect=True, timeout=C_VC_CONNECT_TIMEOUT)
            voice_proto.play(stream)
            await asyncio.get_event_loop().run_in_executor(None, voice_proto._player._end.wait)

            await asyncio.sleep(0.5)
            os.remove(filename)

            return {"success": True}
        except Exception as ex:
            trace(f"Could not play audio due to {ex}", TraceLEVELS.ERROR)
            handled, action = await self._handle_error(channel, ex)
            return {"success": False, "reason": ex, "action": action}
        finally:
            if voice_proto is not None:
                await voice_proto.disconnect()
