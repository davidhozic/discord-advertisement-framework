from datetime import timedelta
from typing import Tuple, List
import time
import pytest
import daf
import asyncio
import os

from daf.events import *

# CONFIGURATION
TEST_USER_ID = 145196308985020416
VOICE_MESSAGE_TEST_LENGTH = 4.5  # Test if entire message is played


@pytest.fixture(scope="module")
async def TEXT_MESSAGE(channels, guilds, accounts: List[daf.ACCOUNT]):
    guild = daf.GUILD(guilds[0], logging=True)
    await accounts[0].add_server(guild)
    guild._event_ctrl.remove_listener(EventID.message_ready, guild._advertise)
    await guild.add_message(tm := daf.TextMESSAGE(None, timedelta(seconds=5), data="Hello World", channels=channels[0]))
    yield tm
    await accounts[0].remove_server(guild)


@pytest.fixture(scope="module")
async def DIRECT_MESSAGE(accounts: List[daf.ACCOUNT]):
    user = daf.USER(TEST_USER_ID)
    await accounts[0].add_server(user)
    user._event_ctrl.remove_listener(EventID.message_ready, user._advertise)
    TEXT_MESSAGE_TEST_MESSAGE = "Hello world", daf.discord.Embed(title="Hello world")
    direct_message = daf.message.DirectMESSAGE(None, timedelta(seconds=5), TEXT_MESSAGE_TEST_MESSAGE, "send",
                                                start_in=timedelta(0), remove_after=None)
    await user.add_message(direct_message)
    yield direct_message
    await accounts[0].remove_server(user)


@pytest.fixture(scope="module")
async def VOICE_MESSAGE(channels, guilds, accounts: List[daf.ACCOUNT]):
    guild = daf.GUILD(guilds[0], logging=True)
    await accounts[0].add_server(guild)
    guild._event_ctrl.remove_listener(EventID.message_ready, guild._advertise)

    cwd = os.getcwd()
    os.chdir(os.path.dirname(__file__))
    VOICE_MESSAGE_TEST_MESSAGE = daf.FILE("testing123.mp3")
    os.chdir(cwd)

    voice_message = daf.message.VoiceMESSAGE(None, timedelta(seconds=20), VOICE_MESSAGE_TEST_MESSAGE, channels[1],
                                            volume=50, start_in=timedelta(), remove_after=None)
    await guild.add_message(voice_message)
    yield voice_message
    await accounts[0].remove_server(guild)


async def test_text_message_send(TEXT_MESSAGE: daf.TextMESSAGE, DIRECT_MESSAGE: daf.DirectMESSAGE):
    "This tests if all the text messages succeed in their sends"

    text_message = TEXT_MESSAGE
    direct_message = DIRECT_MESSAGE

    # TextMESSAGE send
    message_ctx = await text_message._send()
    sent_data_result = message_ctx["sent_data"]

    # Check results
    for message in text_message.sent_messages.values():
        if "text" in sent_data_result:
            assert sent_data_result["text"] == message.content, "TextMESSAGE text does not match message content"
        if "embed" in sent_data_result:
            assert sent_data_result["embed"] in [e.to_dict() for e in message.embeds], "TextMESSAGE embed not in message embeds"


    assert len(message_ctx["channels"]["failed"]) == 0, "Failed to send to all channels"

    # DirectMESSAGE send
    message_ctx = await direct_message._send()
    sent_data_result = message_ctx["sent_data"]
            
    # Check results
    message = direct_message.previous_message
    if "text" in sent_data_result:
        assert sent_data_result["text"] == message.content, "DirectMESSAGE text does not match message content"
    if "embed" in sent_data_result:
        assert sent_data_result["embed"] in [e.to_dict() for e in message.embeds], "DirectMESSAGE embed not in message embeds"

    assert message_ctx["success_info"]["success"], "Failed to send to all channels"


async def test_voice_message_send(VOICE_MESSAGE: daf.VoiceMESSAGE):
    "This tests if all the voice messages succeed in their sends"
    voice_message = VOICE_MESSAGE

    # Send
    start_time = time.time()
    message_context = await voice_message._send()
    end_time = time.time()

    # Check results
    assert end_time - start_time >= VOICE_MESSAGE_TEST_LENGTH * len(voice_message.channels), "Message was not played till the end."
    assert len(message_context["channels"]["failed"]) == 0, "Failed to send to all channels"
