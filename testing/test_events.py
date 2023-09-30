from datetime import timedelta
from typing import Tuple

import daf
import pytest
import asyncio

from daf.events import *


@pytest.fixture
async def CONTROLLERS():
    master_controller = EventController()
    master_controller.add_subcontroller(EventController())
    master_controller.start()
    yield (master_controller, *master_controller.subcontrollers)
    await master_controller.stop()


@pytest.mark.parametrize(
        "event, expected_args",
        [
            (EventID.g_daf_startup, {}),
            (EventID.g_daf_shutdown, {}),
            (
                EventID.message_ready,
                {"server": None, "message": daf.TextMESSAGE(None, timedelta(seconds=5), "Hello World", daf.AutoCHANNEL("test"))}
            ),
        ]
)
async def test_events(CONTROLLERS: Tuple[EventController, EventController], event: EventID, expected_args: dict):
    master, slave = CONTROLLERS

    handler_called = False
    handler_called2 = False
    handler_local_called = False


    def dummy_listener(*args, **kwargs):
        nonlocal handler_called
        handler_called = True

    def dummy_listener2(*args, **kwargs):
        nonlocal handler_called2
        handler_called2 = True

    def local_dummy_listener(*args, **kwargs):
        nonlocal handler_local_called
        handler_local_called = True

    master.add_listener(event, dummy_listener)
    master.add_listener(event, dummy_listener2)
    slave.add_listener(event, local_dummy_listener)
    master.emit(event, **expected_args)
    await asyncio.sleep(0)
    assert handler_called and handler_called2 and handler_local_called, "Handler was not called"

    handler_called = False
    handler_called2 = False
    master.remove_listener(event, dummy_listener)
    master.remove_listener(event, dummy_listener2)
    master.emit(event, **expected_args)
    await asyncio.sleep(0)
    assert not (handler_called or handler_called2), "Handler was called"

    @master.listen(event)
    def dummy_listener(*args, **kwargs):
        nonlocal handler_called
        handler_called = True

    @master.listen(event)
    def dummy_listener2(*args, **kwargs):
        nonlocal handler_called2
        handler_called2 = True

    handler_called = False
    master.emit(event, **expected_args)
    await asyncio.sleep(0)
    master.remove_listener(event, dummy_listener)
    master.remove_listener(event, dummy_listener2)
    assert handler_called and handler_called2, "Handler was not called"
