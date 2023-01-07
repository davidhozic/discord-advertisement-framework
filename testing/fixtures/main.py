from contextlib import suppress
from typing import List
import asyncio
import pytest
import pytest_asyncio
import os
import daf


TEST_TOKEN1, TEST_TOKEN2 = os.environ.get("DISCORD_TOKEN", None).split(';')
TEST_GUILD_ID = 863071397207212052
TEST_CATEGORY_NAME = "RUNNING-TEST"
TEST_TEXT_CHANNEL_NAME_FORM = "PYTEST"
TEST_TEXT_CHANNEL_NUM = 3
TEST_VOICE_CHANNEL_NAME_FORM = "PYTEST_VOICE"
TEST_VOICE_CHANNEL_NUM = 2


@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def start_daf(event_loop: asyncio.AbstractEventLoop):
    event_loop.run_until_complete(daf.initialize(debug=daf.TraceLEVELS.ERROR))
    event_loop.call_later(420, lambda: event_loop.stop()) # Auto exit tests if they don't complete in 7 minutes
    return event_loop


@pytest_asyncio.fixture(scope="session")
async def accounts():
    accs = [
        daf.ACCOUNT(token=TEST_TOKEN1),
        daf.ACCOUNT(token=TEST_TOKEN2)
    ]
    for a in accs:
        await daf.add_object(a)
    
    return accs


@pytest_asyncio.fixture(scope="session")
async def guilds(accounts: List[daf.ACCOUNT]):
    """
    Create tests guilds.
    """
    client = accounts[0].client
    guild_include = None
    guild_exclude = None

    for guild in client.guilds:
        if guild.name == "magic-123-magic":
            guild_include = guild
            break
    else:
        guild_include = await client.create_guild(name="magic-123-magic")

    for guild in client.guilds:
        if guild.name == "magic-321-magic":
            guild_exclude = guild
            break
    else:
        guild_exclude = await client.create_guild(name="magic-321-magic")

    return guild_include, guild_exclude


@pytest_asyncio.fixture(scope="session")
async def channels(guilds):
    guild: daf.discord.Guild
    guild, _ = guilds
    t_channels = []
    v_channels = []
    for channel in guild.channels:
        await channel.delete()

    for i in range(10):
        t_channels.append(await guild.create_text_channel(f"testpy-{i}"))
        v_channels.append(await guild.create_voice_channel(f"testpy-{i}"))

    yield t_channels, v_channels
    for channel in t_channels + v_channels:
        with suppress(daf.discord.HTTPException):
            await channel.delete()
