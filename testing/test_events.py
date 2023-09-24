from datetime import timedelta

import daf
import pytest
import asyncio

from daf.events import *


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
async def test_events(event: EventID, expected_args: dict):
    global_ctrl = get_global_event_ctrl()
    local_ctrl = EventController()
    local_ctrl.start()

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

    global_ctrl.add_listener(event, dummy_listener)
    global_ctrl.add_listener(event, dummy_listener2)
    local_ctrl.add_listener(event, local_dummy_listener)
    global_ctrl.emit(event, **expected_args)
    await asyncio.sleep(0)
    assert handler_called and handler_called2 and handler_local_called, "Handler was not called"

    handler_called = False
    handler_called2 = False
    global_ctrl.remove_listener(event, dummy_listener)
    global_ctrl.remove_listener(event, dummy_listener2)
    global_ctrl.emit(event, **expected_args)
    await asyncio.sleep(0)
    assert not (handler_called or handler_called2), "Handler was called"

    @global_ctrl.listen(event)
    def dummy_listener(*args, **kwargs):
        nonlocal handler_called
        handler_called = True

    @global_ctrl.listen(event)
    def dummy_listener2(*args, **kwargs):
        nonlocal handler_called2
        handler_called2 = True

    handler_called = False
    global_ctrl.emit(event, **expected_args)
    await asyncio.sleep(0)
    global_ctrl.remove_listener(event, dummy_listener)
    global_ctrl.remove_listener(event, dummy_listener2)
    assert handler_called and handler_called2, "Handler was not called"
