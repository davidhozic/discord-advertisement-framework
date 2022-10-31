from contextlib import suppress
from datetime import timedelta

import os

import pytest
# 
import daf


# SIMULATION
#

# CONFIGURATION
TEST_TOKEN = os.environ.get("DISCORD_TOKEN")
TEST_GUILD_ID = 863071397207212052
TEST_USER_ID = 145196308985020416
TEST_CAT_CHANNEL_ID = 1036585192275582997
TEST_CHANNEL_FORMAT = "pytest-{:02d}"
TEST_CHANNEL_NUM = 2


@pytest.mark.asyncio
async def test_text_message_update():
    "This tests if all the text messages succeed in their sends"
    text_channels = []
    try:
        TEXT_MESSAGE_TEST_MESSAGE = [
            ("Hello world", daf.discord.Embed(title="Hello world")),
            ("Goodbye world", daf.discord.Embed(title="Goodbye world"))
        ]

        await daf.initialize(token=TEST_TOKEN)
        client = daf.get_client()
        dc_guild = client.get_guild(TEST_GUILD_ID)
        dc_test_cat = client.get_channel(TEST_CAT_CHANNEL_ID)

        # Create testing channels
        for i in range(1, TEST_CHANNEL_NUM + 1):
            text_channels.append(await dc_guild.create_text_channel(TEST_CHANNEL_FORMAT.format(i), category=dc_test_cat))

        # Create GUILD
        guild = daf.GUILD(TEST_GUILD_ID)
        user = daf.USER(TEST_USER_ID)

        # Create MESSAGE objects
        text_message = daf.message.TextMESSAGE(None, timedelta(seconds=5), "START", text_channels,
                                            "send", start_in=timedelta(), remove_after=None)

        direct_message = daf.message.DirectMESSAGE(None, timedelta(seconds=5), "START", "send",
                                                   start_in=timedelta(0), remove_after=None)

        # Initialize objects
        await guild.initialize()
        await user.initialize()
        await guild.add_message(text_message)
        await user.add_message(direct_message)

        # TextMESSAGE send
        for data in TEXT_MESSAGE_TEST_MESSAGE:
            text, embed = data
            await text_message.update(data=data)
            result = await text_message._send()

            # Check results
            for message in text_message.sent_messages.values():
                assert text == message.content, "TextMESSAGE text does not match message content"
                assert embed.to_dict() in [e.to_dict() for e in message.embeds], "TextMESSAGE embed not in message embeds"

            assert len(result["channels"]["failed"]) == 0, "Failed to send to all channels"

            # DirectMESSAGE send
            await direct_message.update(data=data)
            result = await direct_message._send()

            # Check results
            message = direct_message.previous_message
            assert text == message.content, "DirectMESSAGE text does not match message content"
            assert embed.to_dict() in [e.to_dict() for e in message.embeds], "DirectMESSAGE embed not in message embeds"
            assert result["success_info"]["success"], "Failed to send to all channels"

    finally:
        for channel in text_channels:
            with suppress(daf.discord.HTTPException):
                await channel.delete()