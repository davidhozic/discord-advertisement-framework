import pytest
import asyncio
import os
import daf


TEST_TOKEN = os.environ.get("DISCORD_TOKEN")
TEST_GUILD_ID = 863071397207212052
TEST_USER_ID = 145196308985020416

@pytest.fixture(scope="session")
def event_loop():
    return asyncio.get_event_loop()

@pytest.fixture(scope="session", autouse=True)
def start_daf(event_loop: asyncio.ProactorEventLoop):
    event_loop.run_until_complete(daf.initialize(token=TEST_TOKEN))
    # Create GUILD
    guild = daf.GUILD(TEST_GUILD_ID)
    user = daf.USER(TEST_USER_ID)
    event_loop.run_until_complete(daf.add_object(guild))
    event_loop.run_until_complete(daf.add_object(user))
    yield event_loop
    event_loop.close()