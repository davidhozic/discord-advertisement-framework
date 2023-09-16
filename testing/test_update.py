from datetime import timedelta
from typing import List

import os
import time
import pytest
import daf
import asyncio

from daf.events import *

# CONFIGURATION
TEST_USER_ID = 145196308985020416



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



async def test_text_message_update(TEXT_MESSAGE: daf.TextMESSAGE, DIRECT_MESSAGE: daf.DirectMESSAGE):
    "This tests if all the text messages succeed in their sends"
    TEXT_MESSAGE_TEST_MESSAGE = [
        ("Hello world", daf.discord.Embed(title="Hello world")),
        ("Goodbye world", daf.discord.Embed(title="Goodbye world"))
    ]

    text_message = TEXT_MESSAGE
    direct_message = DIRECT_MESSAGE

    # TextMESSAGE send
    text: str
    embed: daf.discord.Embed
    for data in TEXT_MESSAGE_TEST_MESSAGE:
        text, embed = data
        await text_message.update(data=data)
        message_ctx = await text_message._send()

        # Check results
        message: daf.discord.Message
        for message in text_message.sent_messages.values():
            assert text == message.content, "TextMESSAGE text does not match message content"
            assert embed.to_dict() in [e.to_dict() for e in message.embeds], "TextMESSAGE embed not in message embeds"

        assert len(message_ctx["channels"]["failed"]) == 0, "Failed to send to all channels"

        # DirectMESSAGE send
        await direct_message.update(data=data)
        message_ctx = await direct_message._send()
        # Check results
        message = direct_message.previous_message
        assert text == message.content, "DirectMESSAGE text does not match message content"
        assert embed.to_dict() in [e.to_dict() for e in message.embeds], "DirectMESSAGE embed not in message embeds"
        assert message_ctx["success_info"]["success"], "Failed to send to all channels"



async def test_voice_message_update(VOICE_MESSAGE: daf.VoiceMESSAGE):
    "This tests if all the voice messages succeed in their sends"
    await asyncio.sleep(5)  # Wait for any messages still playing
    cwd = os.getcwd()
    os.chdir(os.path.dirname(__file__))
    with open("testing123.mp3", "rb") as file:
        fdata = file.read()

    VOICE_MESSAGE_TEST_MESSAGE = [
        (4.5, daf.FILE("test.mp3", fdata)),
        (4.5, daf.FILE("test.mp3", fdata.hex())),
        (4.5, daf.AUDIO("testing123.mp3"))
    ]

    os.chdir(cwd)
    voice_message = VOICE_MESSAGE

    # Send
    for duration, audio in VOICE_MESSAGE_TEST_MESSAGE:
        await voice_message.update(data=audio)
        start_time = time.time()
        message_ctx = await voice_message._send()
        end_time = time.time()

        # Check results
        assert end_time - start_time >= duration * len(voice_message.channels), "Message was not played till the end."
        assert len(message_ctx["channels"]["failed"]) == 0, "Failed to send to all channels"
