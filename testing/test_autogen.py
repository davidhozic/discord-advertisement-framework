"""
Module contains automatic tests that
test if automatic generation part of the framework
works as expected.
"""
from datetime import timedelta
from typing import List

from daf.events import *

import os
import daf
import asyncio
import pytest


async def test_autoguild(guilds, accounts: List[daf.ACCOUNT]):
    """
    Test if AutoGUILD works as expected.
    """
    account = accounts[0]
    guild_include, guild_exclude = guilds
    auto_guild = daf.AutoGUILD(
        "magic-.*-magic", "-321-",
        messages=[
            daf.TextMESSAGE(None, timedelta(seconds=1), "Hello World", daf.message.AutoCHANNEL("testpy-[0-9]", "testpy-[5-9]"))
        ]
    )
    await account.add_server(auto_guild)
    found = auto_guild._get_guilds()
    print('Found Guilds ', found)
    print('All Guilds ', account.client.guilds)
    assert guild_include in found, "AutoGUILD failed to find guild that matches the name."
    assert guild_exclude not in found, "AutoGUILD included the guild that matches exclude pattern."
    await account.remove_server(auto_guild)


async def test_autochannel(guilds, channels, accounts):
    """
    Tests if AutoCHANNEL functions properly.
    """
    daf_guild = None
    account: daf.ACCOUNT = accounts[0]
    try:
        guild: daf.discord.Guild
        guild, _ = guilds
        text_channels, voice_channels = channels
        auto_channel = daf.message.AutoCHANNEL("testpy-[0-9]", "testpy-[5-9]")
        auto_channel2 = daf.message.AutoCHANNEL("testpy-[0-9]", "testpy-[5-9]")

        cwd = os.getcwd()
        os.chdir(os.path.dirname(__file__))
        daf_guild = daf.GUILD(
            guild,
            messages=[
                tm := daf.TextMESSAGE(None, timedelta(seconds=20), "Hello World", auto_channel),
                vc := daf.VoiceMESSAGE(None, timedelta(seconds=20), daf.AUDIO("testing123.mp3"), auto_channel2)
            ]
        )

        os.chdir(cwd)
        await daf.add_object(daf_guild, account)

        sort_key = lambda x: x.name
        auto_channel._get_channels()
        auto_channel2._get_channels()
        assert sorted(text_channels[:5], key=sort_key) == sorted(auto_channel.channels, key=sort_key), "Correct behavior would be for AutoCHANNEL to only find first 5 text channels"
        assert sorted(voice_channels[:5], key=sort_key) == sorted(auto_channel2.channels, key=sort_key), "Correct behavior would be for AutoCHANNEL to only find first 5 voice channels"

        await auto_channel.update(exclude_pattern=None)
        await auto_channel2.update(exclude_pattern=None)
        auto_channel._get_channels()
        auto_channel2._get_channels()
        assert sorted(text_channels, key=sort_key) == sorted(auto_channel.channels, key=sort_key), "Correct behavior would be for AutoCHANNEL to find all text channels"
        assert sorted(voice_channels, key=sort_key) == sorted(auto_channel2.channels, key=sort_key), "Correct behavior would be for AutoCHANNEL to find all voice channels"

        # Test update
        await daf_guild.update()
        await tm.update()
        await vc.update()
        await auto_channel.update()
        await auto_channel2.update()
    finally:
        await account.remove_server(daf_guild)
