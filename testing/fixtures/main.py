import asyncio
import pytest
import pytest_asyncio
import os
import daf


TEST_TOKEN = os.environ.get("DISCORD_TOKEN")
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
    event_loop.run_until_complete(daf.initialize(TEST_TOKEN))
    return event_loop


@pytest_asyncio.fixture(scope="session")
async def category():
    client = daf.get_client()
    guild: daf.discord.Guild = client.get_guild(TEST_GUILD_ID)
    cat = await guild.create_category(TEST_CATEGORY_NAME)
    yield cat
    await cat.delete()


@pytest_asyncio.fixture(scope="session")
async def text_channels(category: daf.discord.CategoryChannel):
    ret = []
    for i in range(TEST_TEXT_CHANNEL_NUM):
        ret.append(await category.create_text_channel(TEST_TEXT_CHANNEL_NAME_FORM))

    yield ret
    for c in ret:
        await c.delete()


@pytest_asyncio.fixture(scope="session")
async def voice_channels(category: daf.discord.CategoryChannel):
    ret = []
    for i in range(TEST_VOICE_CHANNEL_NUM):
        ret.append(await category.create_voice_channel(TEST_VOICE_CHANNEL_NAME_FORM))
    
    yield ret
    for c in ret:
        await c.delete()
