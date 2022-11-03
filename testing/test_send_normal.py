from datetime import timedelta

import time
import pytest
import daf

# CONFIGURATION
TEST_GUILD_ID = 863071397207212052
TEST_USER_ID = 145196308985020416
VOICE_MESSAGE_TEST_LENGTH = 3 # Test if entire message is played


@pytest.mark.asyncio
async def test_text_message_send(text_channels):
    "This tests if all the text messages succeed in their sends"
    TEXT_MESSAGE_TEST_MESSAGE = "Hello world", daf.discord.Embed(title="Hello world")

    guild = daf.GUILD(TEST_GUILD_ID)
    user = daf.USER(TEST_USER_ID)
    text_message = daf.message.TextMESSAGE(None, timedelta(seconds=5), TEXT_MESSAGE_TEST_MESSAGE, text_channels,
                                        "send", start_in=timedelta(), remove_after=None)
    direct_message = daf.message.DirectMESSAGE(None, timedelta(seconds=5), TEXT_MESSAGE_TEST_MESSAGE, "send",
                                                start_in=timedelta(0), remove_after=None)
    # Initialize objects
    await guild.initialize()
    await user.initialize()
    await guild.add_message(text_message)
    await user.add_message(direct_message)

    # TextMESSAGE send
    result = await text_message._send()
    sent_data_result = result["sent_data"]
            
    # Check results
    for message in text_message.sent_messages.values():
        if "text" in sent_data_result:
            assert sent_data_result["text"] == message.content, "TextMESSAGE text does not match message content"
        if "embed" in sent_data_result:
            assert sent_data_result["embed"] in [e.to_dict() for e in message.embeds], "TextMESSAGE embed not in message embeds"


    assert len(result["channels"]["failed"]) == 0, "Failed to send to all channels"

    # DirectMESSAGE send
    result = await direct_message._send()
    sent_data_result = result["sent_data"]
            
    # Check results
    message = direct_message.previous_message
    if "text" in sent_data_result:
        assert sent_data_result["text"] == message.content, "DirectMESSAGE text does not match message content"
    if "embed" in sent_data_result:
        assert sent_data_result["embed"] in [e.to_dict() for e in message.embeds], "DirectMESSAGE embed not in message embeds"

    assert result["success_info"]["success"], "Failed to send to all channels"


@pytest.mark.asyncio
async def test_voice_message_send(voice_channels):
    "This tests if all the voice messages succeed in their sends"
    VOICE_MESSAGE_TEST_MESSAGE = daf.AUDIO("https://www.youtube.com/watch?v=1O0yazhqaxs") # 3 second countdown

    guild = daf.GUILD(TEST_GUILD_ID)
    voice_message = daf.message.VoiceMESSAGE(None, timedelta(seconds=20), VOICE_MESSAGE_TEST_MESSAGE, voice_channels,
                                            volume=50, start_in=timedelta(), remove_after=None)

    # Initialize objects
    await guild.initialize()
    await guild.add_message(voice_message)

    # Send
    start_time = time.time()
    result = await voice_message._send()
    end_time = time.time()

    # Check results
    assert end_time - start_time >= VOICE_MESSAGE_TEST_LENGTH * len(voice_channels), "Message was not played till the end."
    assert len(result["channels"]["failed"]) == 0, "Failed to send to all channels"

