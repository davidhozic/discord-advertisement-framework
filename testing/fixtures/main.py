import asyncio
import pytest
import os
import daf



TEST_TOKEN = os.environ.get("DISCORD_TOKEN")

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
