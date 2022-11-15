"""
Module contains automatic tests that 
test if automatic generation part of the framework
works as expected.
"""
from datetime import timedelta

import pytest
import pytest_asyncio
import daf
import asyncio

@pytest_asyncio.fixture(scope="module")
async def guilds():
    """
    Create tests guilds.
    """
    client = daf.get_client()
    guild_include = await client.create_guild(name="magic-123-magic")
    guild_exclude = await client.create_guild(name="magic-321-magic")
    yield guild_include, guild_exclude
    await guild_include.delete()
    await guild_exclude.delete()


@pytest.mark.asyncio
async def test_autoguild(guilds):
    """
    Test if AutoGUILD works as expected.
    """
    guild_include, guild_exclude = guilds
    auto_guild = daf.AutoGUILD("magic-.*-magic", "-321-")
    await daf.add_object(auto_guild)
    await asyncio.sleep(1)
    found = [x.apiobject for x in auto_guild.guilds]
    print(found)
    assert guild_include in found, "AutoGUILD failed to find guild that matches the name."
    assert guild_exclude not in found, "AutoGUILD included the guild that matches exclude pattern."
